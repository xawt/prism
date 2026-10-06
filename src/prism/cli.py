import argparse
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint

from prism import config, context, pr_loader, questions


@dataclass(frozen=True)
class Args:
    path: Path
    list: bool
    print_pr_files: bool
    print_questions: bool
    print_context: bool
    pr_files: pr_loader.PrFiles
    questions: questions.QuestionSet | None


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
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("prism.yaml"),
        help="question config (default: prism.yaml)",
    )
    parser.add_argument("--list", action="store_true", help="print the PR directory file tree")
    parser.add_argument(
        "--print-pr-files",
        action="store_true",
        help="print the loaded PR file structure (debug)",
    )
    parser.add_argument(
        "--print-questions",
        action="store_true",
        help="print the questions loaded from --config (debug)",
    )
    parser.add_argument(
        "--print-context",
        action="store_true",
        help="print each question with the context built for it from the PR (debug)",
    )
    ns = parser.parse_args(argv)
    if not ns.path.is_dir():
        parser.error(f"--path: not a directory: {ns.path}")
    try:
        pr_files = pr_loader.load_pr(ns.path)
    except pr_loader.PrLoadError as e:
        parser.error(f"--path: {e}")
    question_set = None
    if ns.print_questions or ns.print_context:
        try:
            question_set = questions.load_questions(ns.config)
        except questions.QuestionConfigError as e:
            parser.error(f"--config:\n{e}")
    return Args(
        path=ns.path,
        list=ns.list,
        print_pr_files=ns.print_pr_files,
        print_questions=ns.print_questions,
        print_context=ns.print_context,
        pr_files=pr_files,
        questions=question_set,
    )


def main(argv: list[str] | None = None) -> None:
    config.load_env()
    args = parse_args(argv)
    if args.list:
        print("\n".join(pr_loader.tree_lines(args.path)))
    if args.print_pr_files:
        pprint(args.pr_files, sort_dicts=False)
    if args.print_questions and args.questions:
        pprint(args.questions, sort_dicts=False)
    if args.print_context and args.questions:
        for call in context.plan_calls(args.questions, args.pr_files):
            print("\n".join(context.call_lines(call)))
    if not (args.list or args.print_pr_files or args.print_questions or args.print_context):
        print(f"PR directory: {args.path}")


if __name__ == "__main__":
    main()
