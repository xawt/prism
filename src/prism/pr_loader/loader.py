"""Builds the structure of a PR directory created by the `fetch-pr` skill."""

import json
from pathlib import Path
from typing import TypedDict

from prism.pr_loader.pr_commit import PrCommit
from prism.pr_loader.pr_file import PrFile, PrFileType


class PrLoadError(Exception):
    pass


class PrFiles(TypedDict):
    meta: PrFile
    description: PrFile
    commits: list[PrCommit]
    discussion: list[PrFile]


def load_pr(root: Path) -> PrFiles:
    """Index the files of a PR directory.

    `commits.json` is parsed right away; diffs and other file contents are read when first used.
    """
    return {
        "meta": _required(root, "meta.json", PrFileType.META),
        "description": _required(root, "description.md", PrFileType.DESCRIPTION),
        "commits": _commits(root),
        "discussion": _all(root / "discussion", ".md", PrFileType.COMMENT),
    }


def _required(root: Path, name: str, type: PrFileType) -> PrFile:
    path = root / name
    if not path.is_file():
        raise PrLoadError(f"missing {name} in {root}")
    return PrFile(type=type, name=name, path=path)


def _all(directory: Path, suffix: str, type: PrFileType) -> list[PrFile]:
    if not directory.is_dir():
        return []
    paths = sorted(
        p
        for p in directory.iterdir()
        if p.is_file() and p.suffix == suffix and not p.name.startswith(".")
    )
    return [PrFile(type=type, name=p.name, path=p) for p in paths]


def _commits(root: Path) -> list[PrCommit]:
    """Parse `commits.json` and pair each commit with `diffs/NNN-<sha7>.diff`."""
    source = _required(root, "commits.json", PrFileType.COMMITS)
    try:
        rows = json.loads(source.text)
    except json.JSONDecodeError as e:
        raise PrLoadError(f"commits.json: invalid JSON: {e}") from e
    if not isinstance(rows, list):
        raise PrLoadError("commits.json: expected a list of commits")

    diffs = {d.name: d for d in _all(root / "diffs", ".diff", PrFileType.DIFF)}
    commits = [_commit(i, row, diffs) for i, row in enumerate(rows, start=1)]

    extra = sorted(diffs.keys() - {c.diff.name for c in commits})
    if extra:
        raise PrLoadError(f"diffs/{extra[0]} has no matching commit in commits.json")
    return commits


def _commit(index: int, row: object, diffs: dict[str, PrFile]) -> PrCommit:
    if not isinstance(row, dict):
        raise PrLoadError(f"commits.json: commit {index} is not an object")
    oid = _field(row, "oid", index)
    diff_name = f"{index:03d}-{oid[:7]}.diff"
    if diff_name not in diffs:
        raise PrLoadError(f"missing diffs/{diff_name} for commit {oid}")
    authors = row.get("authors") or []
    return PrCommit(
        index=index,
        oid=oid,
        headline=_field(row, "messageHeadline", index),
        body=row.get("messageBody") or "",
        authors=[a.get("name") or a.get("login") or "" for a in authors],
        authored_at=_field(row, "authoredDate", index),
        committed_at=_field(row, "committedDate", index),
        diff=diffs[diff_name],
    )


def _field(row: dict, key: str, index: int) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value:
        raise PrLoadError(f"commits.json: commit {index} has no {key}")
    return value
