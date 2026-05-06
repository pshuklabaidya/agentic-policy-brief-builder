from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_policy_brief_builder.evals import (
    DEFAULT_SYNTHETIC_POLICY_QUESTIONS_PATH,
    DeterministicFakeEmbeddingClient,
    run_local_evaluation,
)
from agentic_policy_brief_builder.evals.runner import EvaluationRunResult


@pytest.mark.evals
def test_local_evaluation_run_passes_with_synthetic_fixtures() -> None:
    result = run_local_evaluation(DEFAULT_SYNTHETIC_POLICY_QUESTIONS_PATH)

    assert isinstance(result, EvaluationRunResult)
    assert result.passed is True
    assert result.total_cases == 3
    assert result.failed_cases == ()
    assert all(case_result.retrieved_results for case_result in result.case_results)
    assert all(case_result.markdown for case_result in result.case_results)


@pytest.mark.evals
def test_failing_evaluation_run_returns_nonpassing_status(tmp_path: Path) -> None:
    fixture_path = tmp_path / "failing_fixture.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "case_id": "unmatched-expectations",
                    "question": "What zoning reforms should Riverton consider?",
                    "expected_topic_keywords": ["quantum", "volcano"],
                    "expected_evidence_ids": ["EVID-does-not-exist"],
                    "expected_evidence_patterns": ["phrase that is absent"],
                    "expected_brief_sections": [
                        "executive_summary",
                        "key_findings",
                        "policy_options",
                        "risks_and_tradeoffs",
                        "recommendation",
                        "evidence_used",
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    result = run_local_evaluation(fixture_path)

    assert result.passed is False
    assert len(result.failed_cases) == 1
    failed_gate_names = {
        gate.name for gate in result.case_results[0].quality_gates if not gate.passed
    }
    assert "retrieval_matches_fixture_expectations" in failed_gate_names


@pytest.mark.evals
def test_evaluation_output_ordering_is_deterministic() -> None:
    first = run_local_evaluation(DEFAULT_SYNTHETIC_POLICY_QUESTIONS_PATH)
    second = run_local_evaluation(DEFAULT_SYNTHETIC_POLICY_QUESTIONS_PATH)

    assert tuple(case.fixture.case_id for case in first.case_results) == tuple(
        case.fixture.case_id for case in second.case_results
    )
    assert tuple(
        tuple(result.evidence_id for result in case.retrieved_results)
        for case in first.case_results
    ) == tuple(
        tuple(result.evidence_id for result in case.retrieved_results)
        for case in second.case_results
    )
    assert tuple(
        tuple(gate.name for gate in case.quality_gates) for case in first.case_results
    ) == tuple(tuple(gate.name for gate in case.quality_gates) for case in second.case_results)


@pytest.mark.evals
def test_local_evaluation_does_not_make_openai_api_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_openai_import(name, *args, **kwargs):
        if name == "openai":
            raise AssertionError("OpenAI import should not be attempted during local evals")
        return original_import(name, *args, **kwargs)

    original_import = __import__
    monkeypatch.setattr("builtins.__import__", fail_openai_import)

    result = run_local_evaluation(DEFAULT_SYNTHETIC_POLICY_QUESTIONS_PATH)

    assert result.passed is True


def test_deterministic_fake_embedding_client_is_stable() -> None:
    client = DeterministicFakeEmbeddingClient()

    first = client.embed_texts(("housing zoning", "tenant parking"))
    second = client.embed_texts(("housing zoning", "tenant parking"))

    assert first == second
    assert len(first) == 2
