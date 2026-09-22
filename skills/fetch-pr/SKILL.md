---
name: fetch-pr
description: Download a GitHub Pull Request (metadata, description, per-commit diffs, and every discussion comment/review) into a local directory tree for offline reading and analysis. Use when the user asks to fetch, download, archive, or save a PR/pull request for offline review, or references a github.com/.../pull/N URL and wants it analyzed locally. Also triggers on the /fetch-pr slash command.
---

# fetch-pr

Downloads a single GitHub Pull Request into a self-contained local directory so
it can be analyzed offline, without further `gh`/network calls, and so
individual commits or review comments can be referenced on their own.

## When to use this skill

- The user asks to "fetch", "download", "pull down", "archive", or "save" a PR
  for offline analysis.
- The user pastes a `github.com/<owner>/<repo>/pull/<number>` URL and wants its
  contents/diff/discussion analyzed.
- The user runs `/fetch-pr <owner/repo#number|url>`.

## Requirements

| Requirement | Presence check | Actually-works check |
|---|---|---|
| `gh` CLI installed | `command -v gh` | — |
| `gh` authenticated with a valid token | — | `gh api user` (succeeds and prints your GitHub login) |
| `jq` installed | `command -v jq` | `jq -n '1'` (runs without error) |
| Network access to `api.github.com` | — | implied by the `gh api user` check above |

**Do not trust `gh auth status` alone.** On at least gh 2.46.0 it can print
`X Failed to log in` / "token is invalid" and still exit 0, because it only
checks that credentials are *configured*, not that they still work. The
reliable check is `gh api user`, which actually calls the API and fails with a
real error on an expired/invalid token.

`scripts/fetch-pr.sh` runs all four of these checks itself before doing
anything else, and exits with a clear, specific error message if one fails
(missing binary, broken jq, or failed `gh api user`) — so you never get a
half-populated output directory from a mid-run auth failure. Still, when this
skill is invoked, run the presence + actually-works checks yourself first
(`command -v gh && command -v jq && gh api user`) and report to the user
up front if something's missing, rather than only finding out from the
script's stderr.

## How to invoke

Run the bundled script with one argument, either form:

```bash
scripts/fetch-pr.sh owner/repo#123
scripts/fetch-pr.sh https://github.com/owner/repo/pull/123
```

The script creates `pr-<owner>-<repo>-<number>/` **in the current working
directory** and prints its path plus a short summary (commit count, discussion
item count) to stderr on success, or a clear error message and non-zero exit
code on failure (missing `gh`/`jq`, not authenticated, unparsable argument, or
output directory already exists).

The output directory is treated as **temporary scratch data**: the script
never moves or cleans it up. After inspecting/analyzing it, tell the user
where it is and let them decide whether to move it somewhere permanent or
delete it.

## Output format

```
pr-<owner>-<repo>-<number>/
  meta.json           # PR metadata (number, title, url, state, author, dates, labels, additions/deletions/changedFiles)
  description.md      # raw PR body, verbatim
  commits.json         # array of {oid, messageHeadline, messageBody, authoredDate, authors}, chronological
  diffs/
    001-<shortsha>.diff   # raw unified diff for that one commit (gh api .../commits/{sha}, diff media type)
    002-<shortsha>.diff
    ...
  discussion/
    001-issue_comment-<author>.md
    002-review-<state>-<author>.md
    003-review_comment-<author>-<path_slug>-L<line>.md
    ...
```

- `diffs/` has exactly one file per commit, numbered in commit order — no
  combined/squashed diff is produced by design (the point is to see how the
  change was built up, commit by commit).
- `discussion/` has exactly one file per discussion event (general PR comment,
  review summary, or single inline review comment), numbered in chronological
  order across all three sources combined. Each file is small and independently
  referenceable (e.g. "look at discussion/007..." or "what does comment 12 say").
- Every `discussion/*.md` file has YAML front matter:
  - `issue_comment`: `type, author, created_at`
  - `review`: `type, author, created_at, state`
  - `review_comment`: `type, author, created_at, path, line, in_reply_to` (the
    zero-padded seq number of the comment it replies to, or `null`), and the
    surrounding `diff_hunk` rendered as a fenced ```diff block above the
    comment body for context.

## After fetching

Once the directory exists, read it directly to answer the user's questions —
`meta.json`/`commits.json` with a JSON reader, `description.md`/`diffs/*.diff`/
`discussion/*.md` as plain text. No further `gh` calls are needed for analysis.
