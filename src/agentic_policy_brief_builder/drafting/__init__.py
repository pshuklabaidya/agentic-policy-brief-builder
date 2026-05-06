"""Citation-aware policy brief drafting."""

from agentic_policy_brief_builder.drafting.brief import (
    DeterministicFakeDraftingClient,
    OpenAIDraftingClient,
    draft_policy_brief,
)
from agentic_policy_brief_builder.drafting.schemas import (
    BriefSection,
    DraftingClient,
    DraftPolicyBriefRequest,
    EvidenceCitation,
    EvidenceContextItem,
    PolicyBriefDraft,
)

__all__ = [
    "BriefSection",
    "DeterministicFakeDraftingClient",
    "DraftPolicyBriefRequest",
    "DraftingClient",
    "EvidenceCitation",
    "EvidenceContextItem",
    "OpenAIDraftingClient",
    "PolicyBriefDraft",
    "draft_policy_brief",
]
