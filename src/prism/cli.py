import argparse
from dataclasses import dataclass
from pathlib import Path

from prism import config, pr_loader


@dataclass(frozen=True)
class Args:
    path: Path
    list: bool


def parse_args(argv: list[str] | None = None) -> Args:
    parser = argparse.ArgumentParser(
        prog="prism",
        description="Split a PR into what needs human review and what can be handed to a model.",
    )
    parser.add_argument(
        "--path",
        type=Path,
        required=True,
        help="PR directory created by the fetch-pr skill",
    )
    parser.add_argument("--list", action="store_true", help="print the PR directory file tree")
    ns = parser.parse_args(argv)
    if not ns.path.is_dir():
        parser.error(f"--path: not a directory: {ns.path}")
    return Args(path=ns.path, list=ns.list)


def main(argv: list[str] | None = None) -> None:
    config.load_env()
    args = parse_args(argv)
    if args.list:
        print("\n".join(pr_loader.tree_lines(args.path)))
    else:
        print(f"PR directory: {args.path}")


if __name__ == "__main__":
    main()
