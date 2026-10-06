"""Text tree of a PR directory, like the `tree` command."""

from pathlib import Path


def tree_lines(root: Path) -> list[str]:
    """Return `root` and everything under it as tree lines. Hidden entries are skipped."""
    return [f"{root.name}/", *_children(root, prefix="")]


def _children(directory: Path, prefix: str) -> list[str]:
    entries = sorted(p for p in directory.iterdir() if not p.name.startswith("."))
    lines: list[str] = []
    for i, entry in enumerate(entries):
        last = i == len(entries) - 1
        connector = "└── " if last else "├── "
        if entry.is_dir():
            lines.append(f"{prefix}{connector}{entry.name}/")
            lines.extend(_children(entry, prefix + ("    " if last else "│   ")))
        else:
            lines.append(f"{prefix}{connector}{entry.name}")
    return lines
