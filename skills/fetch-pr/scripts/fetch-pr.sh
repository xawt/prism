#!/usr/bin/env bash
#
# Fetch a GitHub Pull Request (metadata, description, per-commit diffs, and
# every discussion comment/review) into a local directory for offline
# analysis. See ../SKILL.md for the full output format spec.
#
# Usage: fetch-pr.sh <owner/repo#number | pull-request-url>

set -euo pipefail

usage() {
  echo "Usage: $(basename "$0") <owner/repo#number | https://github.com/owner/repo/pull/number>" >&2
  exit 1
}

[ $# -eq 1 ] || usage
input="$1"

if [[ "$input" =~ ^https?://github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
  owner="${BASH_REMATCH[1]}"
  repo="${BASH_REMATCH[2]}"
  number="${BASH_REMATCH[3]}"
elif [[ "$input" =~ ^([^/]+)/([^/]+)#([0-9]+)$ ]]; then
  owner="${BASH_REMATCH[1]}"
  repo="${BASH_REMATCH[2]}"
  number="${BASH_REMATCH[3]}"
else
  echo "Error: could not parse '$input' as 'owner/repo#number' or a GitHub PR URL." >&2
  usage
fi

for bin in gh jq; do
  command -v "$bin" >/dev/null 2>&1 || { echo "Error: required tool '$bin' not found in PATH." >&2; exit 1; }
done

# A trivial filter, not just `command -v`, catches a broken/wrong jq on PATH.
jq -n '1' >/dev/null 2>&1 || { echo "Error: 'jq' was found on PATH but failed to run a trivial filter." >&2; exit 1; }

# `gh auth status` can report exit code 0 even with an invalid/expired token
# (observed on gh 2.46.0) — it only checks that credentials are *configured*,
# not that they still work. `gh api user` actually calls the API and fails
# loudly (401) on a bad token, so it is the real "is auth working" check.
if ! gh api user >/dev/null 2>&1; then
  echo "Error: gh authentication check failed ('gh api user' did not succeed)." >&2
  echo "Run 'gh auth login' and confirm with 'gh api user' before retrying." >&2
  exit 1
fi

outdir="pr-${owner}-${repo}-${number}"
if [ -e "$outdir" ]; then
  echo "Error: output directory '$outdir' already exists. Remove it or move it aside first." >&2
  exit 1
fi

repo_slug="$owner/$repo"
mkdir -p "$outdir/diffs" "$outdir/discussion"

echo "Fetching PR #$number from $repo_slug..." >&2

pr_json=$(gh pr view "$number" -R "$repo_slug" --json \
  number,title,url,state,author,createdAt,closedAt,mergedAt,baseRefName,headRefName,labels,additions,deletions,changedFiles,body,commits,reviews)

echo "$pr_json" | jq '{number,title,url,state,author,createdAt,closedAt,mergedAt,baseRefName,headRefName,labels,additions,deletions,changedFiles}' \
  > "$outdir/meta.json"

echo "$pr_json" | jq -r '.body // ""' > "$outdir/description.md"

echo "$pr_json" | jq '.commits' > "$outdir/commits.json"

reviews_json=$(echo "$pr_json" | jq '.reviews')

echo "Fetching discussion (issue comments, reviews, review comments)..." >&2

issue_comments_json=$(gh api --paginate "repos/${repo_slug}/issues/${number}/comments" | jq -s 'add // []')
review_comments_json=$(gh api --paginate "repos/${repo_slug}/pulls/${number}/comments" | jq -s 'add // []')

merged=$(jq -n \
  --argjson reviews "$reviews_json" \
  --argjson issue_comments "$issue_comments_json" \
  --argjson review_comments "$review_comments_json" '
  def norm_issue:
    map({
      _type: "issue_comment",
      id: .id,
      author: .user.login,
      created_at: .created_at,
      body: (.body // ""),
      path: null, line: null, diff_hunk: null, state: null, in_reply_to_id: null
    });
  def norm_review:
    map(select(.submittedAt != null) | {
      _type: "review",
      id: .id,
      author: .author.login,
      created_at: .submittedAt,
      body: (.body // ""),
      path: null, line: null, diff_hunk: null,
      state: .state,
      in_reply_to_id: null
    });
  def norm_review_comment:
    map({
      _type: "review_comment",
      id: .id,
      author: .user.login,
      created_at: .created_at,
      body: (.body // ""),
      path: .path,
      line: (.line // .original_line),
      diff_hunk: .diff_hunk,
      state: null,
      in_reply_to_id: .in_reply_to_id
    });

  (($issue_comments | norm_issue) + ($reviews | norm_review) + ($review_comments | norm_review_comment))
  | sort_by(.created_at)
  | to_entries
  | map(.value + {seq: (.key + 1)})
  | . as $withseq
  | ($withseq | map({(.id | tostring): .seq}) | add // {}) as $idmap
  | $withseq | map(. + {reply_seq: (if .in_reply_to_id then ($idmap[(.in_reply_to_id | tostring)] // null) else null end)})
')

discussion_count=$(echo "$merged" | jq 'length')

echo "$merged" | jq -c '.[]' | while IFS= read -r row; do
  type=$(jq -r '._type' <<<"$row")
  author=$(jq -r '.author' <<<"$row")
  created_at=$(jq -r '.created_at' <<<"$row")
  body=$(jq -r '.body' <<<"$row")
  seq=$(jq -r '.seq' <<<"$row")
  seqp=$(printf '%03d' "$seq")

  case "$type" in
    issue_comment)
      fname="${seqp}-issue_comment-${author}.md"
      ;;
    review)
      state=$(jq -r '.state' <<<"$row")
      state_lc=$(echo "$state" | tr '[:upper:]' '[:lower:]')
      fname="${seqp}-review-${state_lc}-${author}.md"
      ;;
    review_comment)
      path=$(jq -r '.path' <<<"$row")
      line_raw=$(jq -r '.line' <<<"$row")
      slug=$(echo "$path" | tr '/' '_')
      if [ "$line_raw" = "null" ]; then
        line_label="file"
      else
        line_label="L${line_raw}"
      fi
      fname="${seqp}-review_comment-${author}-${slug}-${line_label}.md"
      ;;
  esac

  outfile="$outdir/discussion/$fname"

  {
    echo "---"
    printf 'type: %s\n' "$type"
    printf 'author: "%s"\n' "$author"
    printf 'created_at: "%s"\n' "$created_at"
    if [ "$type" = "review" ]; then
      printf 'state: %s\n' "$state"
    fi
    if [ "$type" = "review_comment" ]; then
      printf 'path: "%s"\n' "$path"
      printf 'line: %s\n' "$line_raw"
      reply_seq=$(jq -r '.reply_seq // empty' <<<"$row")
      if [ -n "$reply_seq" ]; then
        printf 'in_reply_to: "%s"\n' "$(printf '%03d' "$reply_seq")"
      else
        printf 'in_reply_to: null\n'
      fi
    fi
    echo "---"
    echo ""
    if [ "$type" = "review_comment" ]; then
      diff_hunk=$(jq -r '.diff_hunk // ""' <<<"$row")
      if [ -n "$diff_hunk" ]; then
        printf '```diff\n'
        printf '%s\n' "$diff_hunk"
        printf '```\n'
        echo ""
      fi
    fi
    printf '%s\n' "$body"
  } > "$outfile"
done

echo "Fetching per-commit diffs..." >&2

commit_count=$(jq 'length' "$outdir/commits.json")

i=0
jq -c '.[]' "$outdir/commits.json" | while IFS= read -r crow; do
  i=$((i + 1))
  oid=$(jq -r '.oid' <<<"$crow")
  shortsha=${oid:0:7}
  seqp=$(printf '%03d' "$i")
  gh api -H "Accept: application/vnd.github.v3.diff" "repos/${repo_slug}/commits/${oid}" \
    > "$outdir/diffs/${seqp}-${shortsha}.diff"
done

cat >&2 <<EOF
Done: $outdir/
  commits:    $commit_count
  discussion: $discussion_count item(s)
EOF
