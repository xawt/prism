import argparse
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint

from prism import config, pr_loader


@dataclass(frozen=True)
class Args:
    path: Path
    list: bool
    print_pr_files: bool
    pr_files: pr_loader.PrFiles


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
    parser.add_argument(
        "--print-pr-files",
        action="store_true",
        help="print the loaded PR file structure (debug)",
    )
    ns = parser.parse_args(argv)
    if not ns.path.is_dir():
        parser.error(f"--path: not a directory: {ns.path}")
    try:
        pr_files = pr_loader.load_pr(ns.path)
    except pr_loader.PrLoadError as e:
        parser.error(f"--path: {e}")
    return Args(path=ns.path, list=ns.list, print_pr_files=ns.print_pr_files, pr_files=pr_files)


def main(argv: list[str] | None = None) -> None:
    config.load_env()
    args = parse_args(argv)
    if args.list:
        print("\n".join(pr_loader.tree_lines(args.path)))
    if args.print_pr_files:
        pprint(args.pr_files, sort_dicts=False)
    if not (args.list or args.print_pr_files):
        print(f"PR directory: {args.path}")


if __name__ == "__main__":
    main()
