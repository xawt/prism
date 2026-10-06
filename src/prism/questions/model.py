"""Questions from `prism.yaml`. Format: docs/input-config.md."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class AnswerType(StrEnum):
    YESNO = "yesno"
    CHOICE = "choice"
    SCORE = "score"


class Per(StrEnum):
    PR = "pr"


@dataclass(frozen=True)
class Question:
    """Fields shared by every answer type. `text` is the `question` field in YAML."""

    id: str
    per: Per
    text: str
    context: tuple[str, ...]


@dataclass(frozen=True)
class YesNoQuestion(Question):
    good: Literal["yes", "no"]


@dataclass(frozen=True)
class ChoiceQuestion(Question):
    options: tuple[str, ...]


@dataclass(frozen=True)
class ScoreQuestion(Question):
    min: int
    max: int
    rubric: dict[int, str]


type AnyQuestion = YesNoQuestion | ChoiceQuestion | ScoreQuestion


@dataclass(frozen=True)
class QuestionSet:
    version: int
    questions: tuple[AnyQuestion, ...]
