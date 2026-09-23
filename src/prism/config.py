"""API key loading: `.env` locally, real environment variables on GitHub Actions."""

import os

from dotenv import find_dotenv, load_dotenv

JEV_API_KEY = "JEV_API_KEY"
OPENROUTER_API_KEY = "OPENROUTER_API_KEY"


class MissingApiKeyError(RuntimeError):
    pass


def in_github_actions() -> bool:
    return os.environ.get("GITHUB_ACTIONS") == "true"


def load_env() -> None:
    """Load `.env` into the environment without overriding existing variables. No-op in CI."""
    if in_github_actions():
        return
    load_dotenv(find_dotenv(usecwd=True), override=False)


def require_api_key(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value
    if in_github_actions():
        hint = "Add it as a repository secret and map it in the workflow's env: block."
    else:
        hint = "Add it to .env (see .env.example) or export it in your shell."
    raise MissingApiKeyError(f"{name} is not set. {hint}")
