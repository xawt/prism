"""Joins questions with a loaded PR: one `QuestionCall` per engine call."""

from dataclasses import dataclass

from prism.pr_loader import PrFiles
from prism.questions import AnyQuestion, Per, Question, QuestionSet
from prism.selectors import SELECTORS


@dataclass(frozen=True)
class QuestionCall:
    """One question asked about one unit, with the context the engine will see."""

    question: AnyQuestion
    unit: str
    context: str


def build_context(question: Question, pr: PrFiles) -> str:
    """The question's selectors applied to the PR, in config order."""
    return "\n\n".join(SELECTORS[name](pr) for name in question.context)


def plan_calls(question_set: QuestionSet, pr: PrFiles) -> list[QuestionCall]:
    """Every engine call needed to answer the question set, in config order."""
    calls: list[QuestionCall] = []
    for question in question_set.questions:
        match question.per:
            case Per.PR:
                calls.append(
                    QuestionCall(question=question, unit="PR", context=build_context(question, pr))
                )
    return calls


def call_lines(call: QuestionCall) -> list[str]:
    """A readable dump of one call: header, question and context."""
    q = call.question
    return [
        f"=== {q.id} · {q.__class__.__name__} · {call.unit} ===",
        f"Q: {q.text}",
        "",
        call.context,
        "",
    ]
