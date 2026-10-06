"""Reads and validates `prism.yaml`. Rules: docs/input-config.md, section "Validation"."""

from pathlib import Path
from typing import Literal

import yaml

from prism.questions.model import (
    AnswerType,
    AnyQuestion,
    ChoiceQuestion,
    Per,
    QuestionSet,
    ScoreQuestion,
    YesNoQuestion,
)
from prism.selectors import SELECTORS

_COMMON_KEYS = {"id", "per", "type", "question", "context"}
_TYPE_KEYS = {
    AnswerType.YESNO: {"good"},
    AnswerType.CHOICE: {"options"},
    AnswerType.SCORE: {"range", "rubric"},
}


class QuestionConfigError(Exception):
    """All problems found in a config file, one per line."""

    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


def load_questions(path: Path) -> QuestionSet:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as e:
        raise QuestionConfigError([f"{path}: cannot read: {e.strerror}"]) from e
    except yaml.YAMLError as e:
        raise QuestionConfigError([f"{path}: invalid YAML: {e}"]) from e
    return parse_questions(data, source=str(path))


def parse_questions(data: object, source: str = "config") -> QuestionSet:
    errors: list[str] = []
    if not isinstance(data, dict):
        raise QuestionConfigError([f"{source}: expected a mapping with version and questions"])

    for key in sorted(data.keys() - {"version", "questions"}, key=str):
        errors.append(f"{source}: unknown key {key!r}")
    version = data.get("version")
    if version != 1:
        errors.append(f"{source}: version: must be 1")

    rows = data.get("questions")
    questions: list[AnyQuestion] = []
    if not isinstance(rows, list) or not rows:
        errors.append(f"{source}: questions: must be a non-empty list")
        rows = []

    seen_ids: set[str] = set()
    for i, row in enumerate(rows):
        parser = _QuestionParser(row, f"{source}: questions[{i}]")
        question = parser.parse()
        errors.extend(parser.errors)
        if question is None:
            continue
        if question.id in seen_ids:
            errors.append(f"{parser.where}: id: duplicate {question.id!r}")
        seen_ids.add(question.id)
        questions.append(question)

    if errors:
        raise QuestionConfigError(errors)
    return QuestionSet(version=1, questions=tuple(questions))


class _QuestionParser:
    """Parses one item of `questions`, collecting every error instead of stopping at the first."""

    def __init__(self, row: object, where: str):
        self.row = row
        self.where = where
        self.errors: list[str] = []

    def error(self, field: str, message: str) -> None:
        self.errors.append(f"{self.where}: {field}: {message}")

    def parse(self) -> AnyQuestion | None:
        row = self.row
        if not isinstance(row, dict):
            self.errors.append(f"{self.where}: must be a mapping")
            return None

        id_ = row.get("id")
        if isinstance(id_, str) and id_:
            self.where = f"{self.where} ({id_})"
        else:
            self.error("id", "required, must be a non-empty string")

        type_ = self._type(row)
        allowed = _COMMON_KEYS | (_TYPE_KEYS[type_] if type_ else set().union(*_TYPE_KEYS.values()))
        for key in sorted(row.keys() - allowed, key=str):
            self.error(str(key), "unknown key" + (f" for type {type_}" if type_ else ""))

        per = self._per(row)
        text = self._text(row)
        context = self._context(row)

        match type_:
            case AnswerType.YESNO:
                good = self._good(row)
            case AnswerType.CHOICE:
                options = self._options(row)
            case AnswerType.SCORE:
                score = self._score(row)
            case None:
                pass

        if self.errors:
            return None
        # No errors means every field above parsed successfully.
        assert isinstance(id_, str) and per and text and context
        common = {"id": id_, "per": per, "text": text, "context": context}
        match type_:
            case AnswerType.YESNO:
                assert good
                return YesNoQuestion(**common, good=good)
            case AnswerType.CHOICE:
                assert options
                return ChoiceQuestion(**common, options=options)
            case AnswerType.SCORE:
                assert score
                lo, hi, rubric = score
                return ScoreQuestion(**common, min=lo, max=hi, rubric=rubric)
            case None:
                return None

    def _type(self, row: dict) -> AnswerType | None:
        value = row.get("type")
        names = ", ".join(t.value for t in AnswerType)
        if value is None:
            self.error("type", f"required, one of: {names}")
            return None
        try:
            return AnswerType(value)
        except ValueError:
            self.error("type", f"unknown value {value!r}, expected one of: {names}")
            return None

    def _per(self, row: dict) -> Per | None:
        value = row.get("per")
        if value is None:
            self.error("per", "required")
            return None
        try:
            return Per(value)
        except ValueError:
            self.error("per", f'only "pr" is supported so far (got {value!r})')
            return None

    def _text(self, row: dict) -> str | None:
        value = row.get("question")
        if isinstance(value, str) and value.strip():
            return value.strip()
        self.error("question", "required, must be a non-empty string")
        return None

    def _context(self, row: dict) -> tuple[str, ...] | None:
        value = row.get("context")
        if not isinstance(value, list) or not value:
            self.error("context", "required, must be a non-empty list of selectors")
            return None
        ok = True
        for item in value:
            if not isinstance(item, str):
                self.error("context", f"selector must be a string, got {item!r}")
                ok = False
            elif item not in SELECTORS:
                self.error("context", f"unknown selector {item!r}")
                ok = False
        return tuple(value) if ok else None

    def _good(self, row: dict) -> Literal["yes", "no"] | None:
        value = row.get("good")
        if isinstance(value, bool):
            word = "yes" if value else "no"
            self.error("good", f'write "{word}" in quotes; a bare {word} is read as a boolean')
            return None
        if value == "yes" or value == "no":
            return value
        self.error("good", 'required for yesno, must be "yes" or "no"')
        return None

    def _options(self, row: dict) -> tuple[str, ...] | None:
        value = row.get("options")
        if not isinstance(value, list) or not value:
            self.error("options", "required for choice, must be a non-empty list")
            return None
        if not all(isinstance(o, str) and o for o in value):
            self.error("options", "every option must be a non-empty string")
            return None
        duplicates = sorted({o for o in value if value.count(o) > 1})
        if duplicates:
            self.error("options", f"duplicates: {', '.join(duplicates)}")
            return None
        return tuple(value)

    def _score(self, row: dict) -> tuple[int, int, dict[int, str]] | None:
        value = row.get("range")
        if not (
            isinstance(value, list)
            and len(value) == 2
            and all(isinstance(v, int) and not isinstance(v, bool) for v in value)
        ):
            self.error("range", "required for score, must be [min, max] with two integers")
            return None
        lo, hi = value
        if lo >= hi:
            self.error("range", f"min must be smaller than max (got [{lo}, {hi}])")
            return None

        rubric = row.get("rubric", {})
        if not isinstance(rubric, dict):
            self.error("rubric", "must be a mapping of score: description")
            return None
        ok = True
        for key, text in rubric.items():
            if not isinstance(key, int) or isinstance(key, bool) or not lo <= key <= hi:
                self.error("rubric", f"key {key!r} must be an integer in range [{lo}, {hi}]")
                ok = False
            if not isinstance(text, str) or not text:
                self.error("rubric", f"description for {key!r} must be a non-empty string")
                ok = False
        return (lo, hi, dict(rubric)) if ok else None
