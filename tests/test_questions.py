from pathlib import Path

import pytest
import yaml

from prism import cli
from prism.questions import (
    ChoiceQuestion,
    Per,
    QuestionConfigError,
    ScoreQuestion,
    YesNoQuestion,
    load_questions,
    parse_questions,
)

REPO = Path(__file__).parent.parent
EXAMPLE_PR = REPO / "skills/fetch-pr/example/pr-pallets-click-1582"


def config(*questions: str, version: str = "1") -> object:
    """Parse a YAML config made of question snippets (each a YAML mapping without the dash)."""
    items = "\n".join("  - " + "\n    ".join(q.strip().splitlines()) for q in questions)
    return yaml.safe_load(f"version: {version}\nquestions:\n{items}\n")


YESNO = """
id: q
per: pr
type: yesno
good: "yes"
question: "Is it good?"
context:
  - pr.description
"""


def errors_for(*questions: str, version: str = "1") -> list[str]:
    with pytest.raises(QuestionConfigError) as exc:
        parse_questions(config(*questions, version=version))
    return exc.value.errors


def replace(snippet: str, old: str, new: str) -> str:
    assert old in snippet
    return snippet.replace(old, new)


def test_load_repo_prism_yaml():
    qs = load_questions(REPO / "prism.yaml")

    assert qs.version == 1
    assert [type(q) for q in qs.questions] == [ChoiceQuestion, ScoreQuestion, YesNoQuestion]
    scope, load, matches = qs.questions
    assert isinstance(scope, ChoiceQuestion)
    assert scope.id == "pr_scope"
    assert scope.per == Per.PR
    assert scope.text == "What is the dominant nature of this change?"
    assert scope.options == ("feature", "fix", "refactor", "config", "docs", "mixed")
    assert scope.context == ("pr.meta", "pr.description", "commits[*].message")
    assert isinstance(load, ScoreQuestion)
    assert (load.min, load.max) == (1, 5)
    assert sorted(load.rubric) == [1, 3, 5]
    assert isinstance(matches, YesNoQuestion)
    assert matches.good == "yes"


def test_rubric_is_optional():
    snippet = """
id: s
per: pr
type: score
range: [0, 10]
question: "How much?"
context:
  - pr.meta
"""
    (q,) = parse_questions(config(snippet)).questions

    assert isinstance(q, ScoreQuestion)
    assert q.rubric == {}


def test_version_must_be_1():
    assert errors_for(YESNO, version="2") == ["config: version: must be 1"]


def test_unknown_top_level_key():
    data = config(YESNO)
    assert isinstance(data, dict)
    data["engine"] = "claude"

    with pytest.raises(QuestionConfigError, match="unknown key 'engine'"):
        parse_questions(data)


def test_questions_must_be_a_non_empty_list():
    with pytest.raises(QuestionConfigError, match="questions: must be a non-empty list"):
        parse_questions({"version": 1, "questions": []})


def test_duplicate_id():
    assert errors_for(YESNO, YESNO) == ["config: questions[1] (q): id: duplicate 'q'"]


def test_missing_id():
    errors = errors_for(replace(YESNO, "id: q", "id: ''"))

    assert errors == ["config: questions[0]: id: required, must be a non-empty string"]


def test_only_per_pr_is_supported():
    errors = errors_for(replace(YESNO, "per: pr", "per: file"))

    assert errors == ["config: questions[0] (q): per: only \"pr\" is supported so far (got 'file')"]


def test_unknown_type():
    errors = errors_for(replace(YESNO, "type: yesno", "type: multi"))

    assert errors[0].startswith("config: questions[0] (q): type: unknown value 'multi'")


def test_unknown_key_for_type():
    errors = errors_for(YESNO + "options: [a, b]\n")

    assert errors == ["config: questions[0] (q): options: unknown key for type yesno"]


def test_typo_in_key_is_reported():
    errors = errors_for(replace(YESNO, "question:", "questoin:"))

    assert "config: questions[0] (q): questoin: unknown key for type yesno" in errors
    assert "config: questions[0] (q): question: required, must be a non-empty string" in errors


def test_good_bare_yes_gets_a_hint():
    errors = errors_for(replace(YESNO, 'good: "yes"', "good: yes"))

    assert errors == [
        'config: questions[0] (q): good: write "yes" in quotes; a bare yes is read as a boolean'
    ]


def test_good_is_required_for_yesno():
    errors = errors_for(replace(YESNO, 'good: "yes"\n', ""))

    assert errors == ['config: questions[0] (q): good: required for yesno, must be "yes" or "no"']


def test_choice_options_must_be_unique():
    snippet = replace(YESNO, 'type: yesno\ngood: "yes"', "type: choice\noptions: [a, b, a]")

    assert errors_for(snippet) == ["config: questions[0] (q): options: duplicates: a"]


def test_choice_requires_options():
    snippet = replace(YESNO, 'type: yesno\ngood: "yes"', "type: choice")

    assert errors_for(snippet) == [
        "config: questions[0] (q): options: required for choice, must be a non-empty list"
    ]


def test_score_range_min_below_max():
    snippet = replace(YESNO, 'type: yesno\ngood: "yes"', "type: score\nrange: [5, 1]")

    assert errors_for(snippet) == [
        "config: questions[0] (q): range: min must be smaller than max (got [5, 1])"
    ]


def test_score_rubric_key_in_range():
    snippet = replace(
        YESNO, 'type: yesno\ngood: "yes"', 'type: score\nrange: [1, 5]\nrubric:\n  7: "too high"'
    )

    assert errors_for(snippet) == [
        "config: questions[0] (q): rubric: key 7 must be an integer in range [1, 5]"
    ]


def test_unknown_selector():
    errors = errors_for(replace(YESNO, "pr.description", "commits[*].diffs"))

    assert errors == ["config: questions[0] (q): context: unknown selector 'commits[*].diffs'"]


def test_context_is_required():
    errors = errors_for(replace(YESNO, "context:\n  - pr.description", "context: []"))

    assert errors == [
        "config: questions[0] (q): context: required, must be a non-empty list of selectors"
    ]


def test_all_errors_are_reported_together():
    broken = replace(replace(YESNO, "per: pr", "per: file"), "pr.description", "nope")
    errors = errors_for(broken, version="2")

    assert len(errors) == 3


def test_load_questions_reports_invalid_yaml(tmp_path):
    path = tmp_path / "prism.yaml"
    path.write_text("questions: [a, b\n")

    with pytest.raises(QuestionConfigError, match="invalid YAML"):
        load_questions(path)


def test_load_questions_reports_missing_file(tmp_path):
    with pytest.raises(QuestionConfigError, match="cannot read"):
        load_questions(tmp_path / "missing.yaml")


def test_cli_print_questions(capsys):
    cli.main(["--path", str(EXAMPLE_PR), "--config", str(REPO / "prism.yaml"), "--print-questions"])

    out = capsys.readouterr().out
    assert out.startswith("QuestionSet(version=1,")
    for name in ("ChoiceQuestion(id='pr_scope'", "ScoreQuestion(id='review_load'"):
        assert name in out


def test_cli_config_error_exits_with_2(tmp_path, capsys):
    path = tmp_path / "prism.yaml"
    path.write_text("version: 2\nquestions: []\n")

    with pytest.raises(SystemExit) as exc:
        cli.main(["--path", str(EXAMPLE_PR), "--config", str(path), "--print-questions"])

    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "version: must be 1" in err
    assert "questions: must be a non-empty list" in err


def test_cli_does_not_need_config_without_print_questions(tmp_path, capsys):
    cli.main(["--path", str(EXAMPLE_PR), "--config", str(tmp_path / "missing.yaml")])

    assert capsys.readouterr().out.startswith("PR directory:")
