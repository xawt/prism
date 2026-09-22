# CLAUDE.md

## Project

Prism — a CLI that splits a PR diff into a checklist: what needs a human's eyes vs. what can be handed to a model. See `README.md`.

- Package sources: `src/prism/` (src-layout)
- Entry point: `prism.prism:main` (`src/prism/prism.py`)
- `skills/` holds standalone Claude skills (e.g. `fetch-pr`) — not part of the Python package.

## Python tooling: uv only

Always use `uv`. Never call `pip`, `pip install`, bare `python`, or activate `.venv` by hand.

| Task | Command |
|---|---|
| Run the CLI | `uv run prism` |
| Run as module | `uv run python -m prism` |
| Run any script/command in the env | `uv run <cmd>` |
| Add dependency | `uv add <pkg>` |
| Add dev dependency | `uv add --dev <pkg>` |
| Remove dependency | `uv remove <pkg>` |
| Install / sync env from lockfile | `uv sync` |
| One-off tool (not a dependency) | `uvx <tool>` |

- Dependencies live in `pyproject.toml`; never edit `uv.lock` by hand — let `uv` regenerate it.
- Commit both `pyproject.toml` and `uv.lock` when dependencies change.

## Secrets

API keys for the engines (Jev, Claude, GPT) go in `.env`, which is gitignored. Never commit `.env` or hardcode keys.
