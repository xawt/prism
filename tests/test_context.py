from pathlib import Path

import pytest

from prism import cli
from prism.context import QuestionCall, build_context, call_lines, plan_calls
from prism.pr_loader import load_pr
from prism.questions import Per, YesNoQuestion, load_questions
from prism.selectors import SELECTORS

REPO = Path(__file__).parent.parent
EXAMPLE_PR = REPO / "skills/fetch-pr/example/pr-pallets-click-1582"


def question(*context: str) -> YesNoQuestion:
    return YesNoQuestion(id="q", per=Per.PR, text="Is it good?", context=context, good="yes")


def loaded(pr) -> set[str]:
    files = [pr["meta"], pr["description"], *pr["discussion"], *(c.diff for c in pr["commits"])]
    return {f.name for f in files if f.loaded}


@pytest.mark.parametrize("name", sorted(SELECTORS))
def test_every_selector_works_on_example(name):
    assert SELECTORS[name](load_pr(EXAMPLE_PR)).startswith("<")


def test_pr_description_selector():
    out = SELECTORS["pr.description"](load_pr(EXAMPLE_PR))

    assert out == (
        '<description name="description.md">\n'
        "I believe this should close issue #1488 \n"
        "</description>"
    )


def test_commit_messages_selector_has_no_diffs():
    pr = load_pr(EXAMPLE_PR)
    out = SELECTORS["commits[*].message"](pr)

    assert out.count("<commit ") == 3
    assert '<commit sha="81ff0ae" index="2">\nrefactor version_option\n\n' in out
    assert "diff --git" not in out
    assert loaded(pr) == set()


def test_commit_diffs_selector():
    out = SELECTORS["commits[*].diff"](load_pr(EXAMPLE_PR))

    assert [line for line in out.splitlines() if line.startswith("<diff ")] == [
        '<diff name="001-cb37854.diff">',
        '<diff name="002-81ff0ae.diff">',
        '<diff name="003-b38cb0e.diff">',
    ]


def test_build_context_keeps_config_order():
    pr = load_pr(EXAMPLE_PR)

    a = build_context(question("pr.description", "pr.meta"), pr)
    b = build_context(question("pr.meta", "pr.description"), pr)

    assert a.index("<description") < a.index("<meta")
    assert b.index("<meta") < b.index("<description")


def test_build_context_reads_only_selected_files():
    pr = load_pr(EXAMPLE_PR)

    build_context(question("pr.description", "commits[*].message"), pr)

    assert loaded(pr) == {"description.md"}


def test_plan_calls_for_repo_config():
    pr = load_pr(EXAMPLE_PR)
    calls = plan_calls(load_questions(REPO / "prism.yaml"), pr)

    assert [(c.question.id, c.unit) for c in calls] == [
        ("pr_scope", "PR"),
        ("review_load", "PR"),
        ("description_matches_diff", "PR"),
    ]
    assert calls[2].context == build_context(calls[2].question, pr)
    assert not any(f.loaded for f in pr["discussion"])


def test_call_lines():
    call = QuestionCall(question=question("pr.meta"), unit="PR", context="<meta>x</meta>")

    assert call_lines(call) == [
        "=== q · YesNoQuestion · PR ===",
        "Q: Is it good?",
        "",
        "<meta>x</meta>",
        "",
    ]


def test_cli_print_context(capsys):
    cli.main(["--path", str(EXAMPLE_PR), "--config", str(REPO / "prism.yaml"), "--print-context"])

    out = capsys.readouterr().out
    headers = [line for line in out.splitlines() if line.startswith("=== ")]
    assert headers == [
        "=== pr_scope · ChoiceQuestion · PR ===",
        "=== review_load · ScoreQuestion · PR ===",
        "=== description_matches_diff · YesNoQuestion · PR ===",
    ]
    assert out.count('<diff name="002-81ff0ae.diff">') == 2
