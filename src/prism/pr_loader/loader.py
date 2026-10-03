"""Builds the structure of a PR directory created by the `fetch-pr` skill."""

from pathlib import Path
from typing import TypedDict

from prism.pr_loader.pr_file import PrFile, PrFileType


class PrLoadError(Exception):
    pass


class PrFiles(TypedDict):
    meta: PrFile
    description: PrFile
    commits: PrFile
    diffs: list[PrFile]
    discussion: list[PrFile]


def load_pr(root: Path) -> PrFiles:
    """Index the files of a PR directory. File contents are not read until used."""
    return {
        "meta": _required(root, "meta.json", PrFileType.META),
        "description": _required(root, "description.md", PrFileType.DESCRIPTION),
        "commits": _required(root, "commits.json", PrFileType.COMMITS),
        "diffs": _all(root / "diffs", ".diff", PrFileType.DIFF),
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
