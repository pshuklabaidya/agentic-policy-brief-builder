"""Fixture loading for deterministic local evaluations."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__all__ = ["EvaluationFixture", "FixtureValidationError", "load_evaluation_fixtures"]

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SYNTHETIC_POLICY_QUESTIONS_PATH = (
    _REPOSITORY_ROOT / "evals" / "fixtures" / "synthetic_policy_questions.json"
)
_REQUIRED_FIELDS = frozenset(
    {
        "case_id",
        "question",
        "expected_topic_keywords",
        "expected_brief_sections",
    }
)


class FixtureValidationError(ValueError):
    """Raised when an evaluation fixture JSON file is malformed."""


@dataclass(frozen=True, slots=True)
class EvaluationFixture:
    """One deterministic policy-question evaluation case."""

    case_id: str
    question: str
    expected_topic_keywords: tuple[str, ...]
    expected_brief_sections: tuple[str, ...]
    expected_evidence_patterns: tuple[str, ...] = ()
    expected_evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_nonblank_string("case_id", self.case_id)
        _require_nonblank_string("question", self.question)
        object.__setattr__(
            self,
            "expected_topic_keywords",
            _nonblank_string_tuple("expected_topic_keywords", self.expected_topic_keywords),
        )
        object.__setattr__(
            self,
            "expected_brief_sections",
            _nonblank_string_tuple("expected_brief_sections", self.expected_brief_sections),
        )
        object.__setattr__(
            self,
            "expected_evidence_patterns",
            _string_tuple("expected_evidence_patterns", self.expected_evidence_patterns),
        )
        object.__setattr__(
            self,
            "expected_evidence_ids",
            _string_tuple("expected_evidence_ids", self.expected_evidence_ids),
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any], *, index: int) -> EvaluationFixture:
        missing = sorted(field for field in _REQUIRED_FIELDS if field not in data)
        if missing:
            fields = ", ".join(missing)
            msg = f"Fixture at index {index} is missing required field(s): {fields}"
            raise FixtureValidationError(msg)

        return cls(
            case_id=_field_string(data, "case_id", index),
            question=_field_string(data, "question", index),
            expected_topic_keywords=_field_string_tuple(
                data, "expected_topic_keywords", index, require_nonempty=True
            ),
            expected_brief_sections=_field_string_tuple(
                data, "expected_brief_sections", index, require_nonempty=True
            ),
            expected_evidence_patterns=_field_string_tuple(
                data, "expected_evidence_patterns", index, require_nonempty=False
            ),
            expected_evidence_ids=_field_string_tuple(
                data, "expected_evidence_ids", index, require_nonempty=False
            ),
        )


def load_evaluation_fixtures(path: str | Path) -> tuple[EvaluationFixture, ...]:
    """Load ordered evaluation fixtures from a JSON file."""

    fixture_path = Path(path)
    if not fixture_path.exists():
        msg = f"Evaluation fixture file does not exist: {fixture_path}"
        raise FileNotFoundError(msg)
    if not fixture_path.is_file():
        msg = f"Evaluation fixture path is not a file: {fixture_path}"
        raise FixtureValidationError(msg)

    try:
        raw_data = json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        msg = f"Evaluation fixture file is not valid JSON: {fixture_path}: {exc.msg}"
        raise FixtureValidationError(msg) from exc

    if not isinstance(raw_data, list):
        msg = "Evaluation fixture JSON must contain a top-level list"
        raise FixtureValidationError(msg)
    if not raw_data:
        msg = "Evaluation fixture JSON must contain at least one fixture"
        raise FixtureValidationError(msg)

    fixtures: list[EvaluationFixture] = []
    seen_case_ids: set[str] = set()
    for index, item in enumerate(raw_data):
        if not isinstance(item, Mapping):
            msg = f"Fixture at index {index} must be an object"
            raise FixtureValidationError(msg)
        fixture = EvaluationFixture.from_mapping(item, index=index)
        if fixture.case_id in seen_case_ids:
            msg = f"Duplicate fixture case_id at index {index}: {fixture.case_id}"
            raise FixtureValidationError(msg)
        seen_case_ids.add(fixture.case_id)
        fixtures.append(fixture)
    return tuple(fixtures)


def _field_string(data: Mapping[str, Any], field_name: str, index: int) -> str:
    value = data[field_name]
    if not isinstance(value, str):
        msg = f"Fixture at index {index} field {field_name!r} must be a string"
        raise FixtureValidationError(msg)
    if not value.strip():
        msg = f"Fixture at index {index} field {field_name!r} must not be blank"
        raise FixtureValidationError(msg)
    return value


def _field_string_tuple(
    data: Mapping[str, Any],
    field_name: str,
    index: int,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if field_name not in data:
        return ()
    value = data[field_name]
    if isinstance(value, str) or not isinstance(value, Sequence):
        msg = f"Fixture at index {index} field {field_name!r} must be a list of strings"
        raise FixtureValidationError(msg)
    if require_nonempty and not value:
        msg = f"Fixture at index {index} field {field_name!r} must not be empty"
        raise FixtureValidationError(msg)
    values: list[str] = []
    for value_index, item in enumerate(value):
        if not isinstance(item, str):
            msg = (
                f"Fixture at index {index} field {field_name!r} item "
                f"{value_index} must be a string"
            )
            raise FixtureValidationError(msg)
        if require_nonempty and not item.strip():
            msg = (
                f"Fixture at index {index} field {field_name!r} item "
                f"{value_index} must not be blank"
            )
            raise FixtureValidationError(msg)
        values.append(item)
    return tuple(values)


def _require_nonblank_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        msg = f"{field_name} must be a string"
        raise TypeError(msg)
    if not value.strip():
        msg = f"{field_name} must not be blank"
        raise ValueError(msg)


def _nonblank_string_tuple(field_name: str, values: Sequence[str]) -> tuple[str, ...]:
    value_tuple = _string_tuple(field_name, values)
    if not value_tuple:
        msg = f"{field_name} must contain at least one value"
        raise ValueError(msg)
    if any(not value.strip() for value in value_tuple):
        msg = f"{field_name} must not contain blank values"
        raise ValueError(msg)
    return value_tuple


def _string_tuple(field_name: str, values: Sequence[str]) -> tuple[str, ...]:
    value_tuple = tuple(values)
    for index, value in enumerate(value_tuple):
        if not isinstance(value, str):
            msg = f"{field_name}[{index}] must be a string"
            raise TypeError(msg)
    return value_tuple
