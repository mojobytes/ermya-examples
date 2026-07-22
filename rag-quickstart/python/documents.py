"""The demo corpus: 11 official AI-governance PDFs with per-document ACLs.

Alice = Europe + international bodies; Bob = Americas + Asia-Pacific. No document
is shared, so the same query returns disjoint sets per user.
"""
from __future__ import annotations

from dataclasses import dataclass

ALICE = "alice"
BOB = "bob"


@dataclass(frozen=True)
class Document:
    filename: str
    jurisdiction: str
    owner: str


DOCUMENTS: list[Document] = [
    Document("eu_ai_act.pdf", "EU", ALICE),
    Document("uk_pro_innovation_white_paper.pdf", "UK", ALICE),
    Document("unesco_ethics_of_ai.pdf", "UNESCO", ALICE),
    Document("oecd_recommendation_ai.pdf", "OECD", ALICE),
    Document("council_of_europe_framework_convention.pdf", "CoE", ALICE),
    Document("nist_ai_rmf_1_0.pdf", "US", BOB),
    Document("australia_ai_ethics_principles.pdf", "AU", BOB),
    Document("canada_directive_automated_decision_making.pdf", "CA", BOB),
    Document("singapore_model_ai_governance_genai.pdf", "SG", BOB),
    Document("japan_ai_guidelines_for_business.pdf", "JP", BOB),
    Document("south_korea_ai_basic_act.pdf", "KR", BOB),
]


def owners() -> set[str]:
    return {d.owner for d in DOCUMENTS}
