from __future__ import annotations

from dataclasses import dataclass

import pytest

from agentic_policy_brief_builder.drafting import (
    BriefSection,
    DeterministicFakeDraftingClient,
    DraftPolicyBriefRequest,
    EvidenceCitation,
    PolicyBriefDraft,
    draft_policy_brief,
)


@dataclass(frozen=True, slots=True)
class FakeRetrievalResult:
    evidence_id: str
    text: str
    document_name: str = "Riverton Housing Packet.pdf"
    source_type: str = "pdf"
    page_number: int | None = 3
    chunk_index: int = 0


class UnknownCitationDraftingClient:
    def draft_policy_brief(self, request: DraftPolicyBriefRequest) -> PolicyBriefDraft:
        known_id = request.evidence_context[0].evidence_id
        return PolicyBriefDraft(
            title="Unknown Citation Draft",
            executive_summary="A draft that intentionally cites unknown evidence.",
            key_findings=(
                BriefSection(
                    heading="Finding",
                    content="This finding cites valid evidence.",
                    evidence_ids=(known_id,),
                ),
            ),
            policy_options=(
                BriefSection(
                    heading="Option",
                    content="This option cites an invented evidence ID.",
                    evidence_ids=("EVID-invented-page-99-0",),
                ),
            ),
            risks_and_tradeoffs=(
                BriefSection(
                    heading="Risk",
                    content="This risk cites valid evidence.",
                    evidence_ids=(known_id,),
                ),
            ),
            recommendation=BriefSection(
                heading="Recommendation",
                content="This recommendation cites valid evidence.",
                evidence_ids=(known_id,),
            ),
            evidence_used=(
                EvidenceCitation(
                    evidence_id=known_id,
                    document_name=request.evidence_context[0].document_name,
                    source_type=request.evidence_context[0].source_type,
                    page_number=request.evidence_context[0].page_number,
                    chunk_index=request.evidence_context[0].chunk_index,
                    cited_text=request.evidence_context[0].text,
                ),
            ),
        )


def test_draft_policy_brief_generates_successful_brief_from_fake_evidence() -> None:
    draft = draft_policy_brief(
        "How should Riverton reduce eviction risk?",
        _retrieval_results(),
        drafting_client=DeterministicFakeDraftingClient(),
    )

    assert draft.title == "Policy Brief: How should Riverton reduce eviction risk?"
    assert draft.executive_summary
    assert draft.key_findings
    assert draft.policy_options
    assert draft.risks_and_tradeoffs
    assert draft.recommendation.content


def test_evidence_ids_survive_into_brief_sections() -> None:
    draft = draft_policy_brief(
        "How should Riverton reduce eviction risk?",
        _retrieval_results(),
        drafting_client=DeterministicFakeDraftingClient(),
    )

    assert draft.key_findings[0].evidence_ids == ("EVID-riverton-page-3-0",)
    assert draft.policy_options[0].evidence_ids == ("EVID-riverton-page-4-1",)
    assert draft.risks_and_tradeoffs[0].evidence_ids == ("EVID-riverton-page-3-0",)
    assert draft.recommendation.evidence_ids == (
        "EVID-riverton-page-3-0",
        "EVID-riverton-page-4-1",
    )


def test_unknown_generated_evidence_ids_raise_clear_error() -> None:
    with pytest.raises(
        ValueError,
        match="Generated brief cites unknown evidence IDs: EVID-invented-page-99-0",
    ):
        draft_policy_brief(
            "How should Riverton reduce eviction risk?",
            _retrieval_results(),
            drafting_client=UnknownCitationDraftingClient(),
        )


def test_blank_question_raises_clear_error() -> None:
    with pytest.raises(ValueError, match="policy_question must not be blank"):
        draft_policy_brief(
            "   ",
            _retrieval_results(),
            drafting_client=DeterministicFakeDraftingClient(),
        )


def test_empty_retrieval_results_raise_clear_error() -> None:
    with pytest.raises(ValueError, match="retrieved_results must contain at least one result"):
        draft_policy_brief(
            "How should Riverton reduce eviction risk?",
            (),
            drafting_client=DeterministicFakeDraftingClient(),
        )


def test_evidence_used_preserves_citation_metadata() -> None:
    draft = draft_policy_brief(
        "How should Riverton reduce eviction risk?",
        _retrieval_results(),
        drafting_client=DeterministicFakeDraftingClient(),
    )

    assert draft.evidence_used == (
        EvidenceCitation(
            evidence_id="EVID-riverton-page-3-0",
            document_name="Riverton Housing Packet.pdf",
            source_type="pdf",
            page_number=3,
            chunk_index=0,
            cited_text="Eviction diversion reduced filings by 18 percent in the pilot.",
        ),
        EvidenceCitation(
            evidence_id="EVID-riverton-page-4-1",
            document_name="Riverton Housing Packet.pdf",
            source_type="pdf",
            page_number=4,
            chunk_index=1,
            cited_text="Rental assistance was most effective when paired with legal aid.",
        ),
    )


def _retrieval_results() -> tuple[FakeRetrievalResult, ...]:
    return (
        FakeRetrievalResult(
            evidence_id="EVID-riverton-page-3-0",
            text="Eviction diversion reduced filings by 18 percent in the pilot.",
            page_number=3,
            chunk_index=0,
        ),
        FakeRetrievalResult(
            evidence_id="EVID-riverton-page-4-1",
            text="Rental assistance was most effective when paired with legal aid.",
            page_number=4,
            chunk_index=1,
        ),
    )
