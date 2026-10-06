```
                                                            ╱▏
██████╗ ██████╗ ██╗███████╗███╗   ███╗                 ────╱ ▏────▶ 🔴  needs a human's eyes
██╔══██╗██╔══██╗██║██╔════╝████╗ ████║                 ───╱  ▏───▶ 🟠
██████╔╝██████╔╝██║███████╗██╔████╔██║                 ──╱   ▏──▶ 🟡
██╔═══╝ ██╔══██╗██║╚════██║██║╚██╔╝██║                  ╱    ▏─▶ 🟢
██║     ██║  ██║██║███████║██║ ╚═╝ ██║                 ╱     ▏▶ 🔵  safe to hand to the model
╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚═╝                ╱      ▏▶ 🟣
```

*Split the diff like light through a prism — see instantly what needs your eyes and what you can hand to the model.*

> **Status:** early-stage project. The CLI can read a PR directory, but there is no analysis yet.

## How it works

1. Prism analyzes the change using one of the following engines:
   - **Jev** — a model from TypeSafe AI
   - a classic LLM (e.g. Claude, GPT)
2. The analysis results are aggregated into a checklist for the reviewer.
3. Each checklist item is tagged with one of two statuses:
   - **Needs human attention** — risky, ambiguous spots, or ones requiring business/domain context.
   - **Can be handed to the model** — mechanical, repetitive changes that are easy to verify automatically.

Goal: the reviewer spends time on the parts that actually need it, instead of reviewing the whole diff uniformly.

## Test engines

Prism is designed so the analysis engine (Jev vs. classic LLM) is interchangeable — the choice of engine shouldn't change the format of the output checklist.

## Usage

Prism works on a PR directory created by the [`fetch-pr`](skills/fetch-pr/SKILL.md) skill. The repo includes one in `skills/fetch-pr/example/`:

```sh
uv run prism --path skills/fetch-pr/example/pr-pallets-click-1582 --list
```

```
pr-pallets-click-1582/
├── commits.json
├── description.md
├── diffs/
│   ├── 001-cb37854.diff
│   ├── 002-81ff0ae.diff
│   └── 003-b38cb0e.diff
├── discussion/
│   ├── 001-issue_comment-0x1za.md
│   …
│   └── 015-issue_comment-davidism.md
└── meta.json
```

| Option | Description |
|---|---|
| `--path PATH` | Required. The PR directory. Without other options Prism prints `PR directory: PATH`. |
| `--config PATH` | The question config. Defaults to `prism.yaml` in the current directory. Only read by options that need questions. |
| `--list` | Print the PR directory's file tree. Hidden files (such as `.DS_Store`) are skipped. |
| `--print-pr-files` | Debug: print the structure Prism builds from the PR directory. It shows each file's type, name, size and whether its text has been read. Contents are read only when first used. |
| `--print-questions` | Debug: print the questions loaded from `--config`. |
| `--print-context` | Debug: for each question, print the context Prism builds from the PR (the selectors in its `context`, in order). This is what the engine will see. Only the files a question uses are read. |
| `-h`, `--help` | Show the options. |

Prism prints an error and exits with code 2 if `--path` is missing, isn't a directory, or has no `meta.json`, `description.md` or `commits.json`. It does the same if the config breaks any rule in [docs/input-config.md](docs/input-config.md#validation), listing every problem with the question and field it belongs to.

## Configuration

Prism needs API keys for the engines it uses. A key is only required when its engine is actually used.

| Variable | Used by |
|---|---|
| `JEV_API_KEY` | Jev (TypeSafe AI) |
| `OPENROUTER_API_KEY` | classic LLMs (Claude, GPT, …) via OpenRouter |

**Locally:** copy `.env.example` to `.env` and fill in the keys. Variables already exported in your shell take precedence over `.env`.

```sh
cp .env.example .env
```

**GitHub Actions:** `.env` is ignored. Add the keys as repository secrets (`gh secret set JEV_API_KEY`, `gh secret set OPENROUTER_API_KEY`) and map them in the workflow:

```yaml
- run: uv run prism ...
  env:
    JEV_API_KEY: ${{ secrets.JEV_API_KEY }}
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

How keys are resolved:

- An exported variable always wins over `.env`; `.env` only fills in what's missing.
- `.env` is looked up in the current directory, then its parents — so a stray `.env` higher up (e.g. `~/.env`) can be picked up if the repo has none.
- A missing `.env` is not an error. A key that is unset *or empty* (`JEV_API_KEY=`) is only reported when an engine needs it.
- CI is detected via `GITHUB_ACTIONS=true` (set by GitHub automatically). Secrets aren't passed to workflows triggered from forks, so those runs will report missing keys.

## Questions

The questions Prism asks about a PR are defined in `prism.yaml`. The format is described in [docs/input-config.md](docs/input-config.md).

## Output

A checklist split into "needs manual review" and "can be verified by a model" sections, ready to paste as a PR comment or use locally before sending a review.

## Roadmap

- [ ] Integration with Jev (TypeSafe AI)
- [ ] Integration with a classic LLM as an alternative engine
- [ ] Checklist format (markdown / PR comment)
- [ ] First CLI-runnable version of the tool
