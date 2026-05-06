from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_policy_brief_builder.evals.fixtures import (
    DEFAULT_SYNTHETIC_POLICY_QUESTIONS_PATH,
    FixtureValidationError,
    load_evaluation_fixtures,
)


def test_loads_synthetic_policy_question_fixtures_in_order() -> None:
    fixtures = load_evaluation_fixtures(DEFAULT_SYNTHETIC_POLICY_QUESTIONS_PATH)

    assert tuple(fixture.case_id for fixture in fixtures) == (
        "housing_needs_zoning_reform",
        "community_feedback_displacement",
        "implementation_metrics",
    )
    assert fixtures[0].question.startswith("What zoning reforms")
    assert "key_findings" in fixtures[0].expected_brief_sections
    assert fixtures[0].expected_evidence_ids


def test_fixture_loading_rejects_missing_required_field(tmp_path: Path) -> None:
    path = _write_json(tmp_path, [{"case_id": "missing_question"}])

    with pytest.raises(FixtureValidationError, match="missing required field"):
        load_evaluation_fixtures(path)


def test_fixture_loading_rejects_non_list_root(tmp_path: Path) -> None:
    path = _write_json(tmp_path, {"case_id": "not-a-list"})

    with pytest.raises(FixtureValidationError, match="top-level list"):
        load_evaluation_fixtures(path)


def test_fixture_loading_rejects_duplicate_case_ids(tmp_path: Path) -> None:
    fixture = {
        "case_id": "duplicate",
        "question": "What should Riverton do?",
        "expected_topic_keywords": ["housing"],
        "expected_brief_sections": ["executive_summary"],
    }
    path = _write_json(tmp_path, [fixture, fixture])

    with pytest.raises(FixtureValidationError, match="Duplicate fixture case_id"):
        load_evaluation_fixtures(path)


def test_fixture_loading_rejects_bad_keyword_type(tmp_path: Path) -> None:
    path = _write_json(
        tmp_path,
        [
            {
                "case_id": "bad-keywords",
                "question": "What should Riverton do?",
                "expected_topic_keywords": "housing",
                "expected_brief_sections": ["executive_summary"],
            }
        ],
    )

    with pytest.raises(FixtureValidationError, match="must be a list of strings"):
        load_evaluation_fixtures(path)


def _write_json(tmp_path: Path, data) -> Path:
    path = tmp_path / "fixtures.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path
