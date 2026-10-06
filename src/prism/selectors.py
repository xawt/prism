"""Selectors: how each `context` entry in `prism.yaml` is taken from a loaded PR.

`SELECTORS` is the single list of supported selectors. Config validation accepts exactly these
names, and context building calls these functions. Each function returns tagged text, reading
files only when called.
"""

from collections.abc import Callable

from prism.pr_loader import PrFiles

type Selector = Callable[[PrFiles], str]


def _commit_messages(pr: PrFiles) -> str:
    return "\n\n".join(c.context() for c in pr["commits"])


def _commit_diffs(pr: PrFiles) -> str:
    return "\n\n".join(c.diff.context() for c in pr["commits"])


SELECTORS: dict[str, Selector] = {
    "pr.meta": lambda pr: pr["meta"].context(),
    "pr.description": lambda pr: pr["description"].context(),
    "commits[*].message": _commit_messages,
    "commits[*].diff": _commit_diffs,
}
