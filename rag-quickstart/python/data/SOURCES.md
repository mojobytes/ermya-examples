# PDF sources

Provenance for the 11 official AI-governance documents used by the VLS demo
(see `documents.py` for the per-document owner ACL). All PDFs are committed to
the repo so the example runs offline with no live network access.

| filename | jurisdiction | source URL | retrieved | status |
|----------|--------------|------------|-----------|--------|
| eu_ai_act.pdf | EU | https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202401689 | 2026-07-22 | downloaded |
| uk_pro_innovation_white_paper.pdf | UK | https://assets.publishing.service.gov.uk/media/64cb71a547915a00142a91c4/a-pro-innovation-approach-to-ai-regulation-amended-web-ready.pdf | 2026-07-22 | downloaded |
| unesco_ethics_of_ai.pdf | UNESCO | https://unesdoc.unesco.org/ark:/48223/pf0000381137 | — | **PENDING MANUAL DOWNLOAD** — unesdoc.unesco.org serves an interstitial/redirect page to automated clients (curl gets HTML, not the PDF binary); fetch via browser and save as `unesco_ethics_of_ai.pdf` |
| oecd_recommendation_ai.pdf | OECD | https://legalinstruments.oecd.org/api/print?ids=648&lang=en | 2026-07-22 | downloaded |
| council_of_europe_framework_convention.pdf | CoE | https://rm.coe.int/1680afae3c | — | **PENDING MANUAL DOWNLOAD** — rm.coe.int blocks automated requests with a Cloudflare challenge ("Sorry, you have been blocked"); fetch via browser and save as `council_of_europe_framework_convention.pdf` |
| nist_ai_rmf_1_0.pdf | US | https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf | 2026-07-22 | downloaded |
| australia_ai_ethics_principles.pdf | AU | https://www.industry.gov.au/publications/australias-artificial-intelligence-ethics-principles/australias-ai-ethics-principles | — | **PENDING MANUAL DOWNLOAD** — published as an HTML page on industry.gov.au, no direct PDF found; save/export the page as `australia_ai_ethics_principles.pdf` |
| canada_directive_automated_decision_making.pdf | CA | https://publications.gc.ca/collections/collection_2021/sct-tbs/BT48-31-2021-eng.pdf | — | **PENDING MANUAL DOWNLOAD** — publications.gc.ca redirects automated requests through an "archived" interstitial that loops back to itself (curl gets HTML, not the PDF binary); fetch via browser and save as `canada_directive_automated_decision_making.pdf` |
| singapore_model_ai_governance_genai.pdf | SG | https://aiverifyfoundation.sg/downloads/Proposed_MGF_Gen_AI_2024.pdf | 2026-07-22 | downloaded |
| japan_ai_guidelines_for_business.pdf | JP | https://www.meti.go.jp/shingikai/mono_info_service/ai_shakai_jisso/pdf/20240419_9.pdf | 2026-07-22 | downloaded |
| south_korea_ai_basic_act.pdf | KR | https://cset.georgetown.edu/wp-content/uploads/t0625_south_korea_ai_law_EN.pdf (CSET/Georgetown English translation; no official English-language PDF found) | 2026-07-22 | downloaded |

## Pending manual downloads (4 of 11)

The following jurisdictions block automated (curl) downloads with a
Cloudflare challenge, a JS-driven interstitial, or publish the document only
as an HTML page. A human must fetch these via a real browser and place the
file at the exact path below before the VLS demo has its full 11-document
corpus:

1. `data/unesco_ethics_of_ai.pdf` — https://unesdoc.unesco.org/ark:/48223/pf0000381137
2. `data/council_of_europe_framework_convention.pdf` — https://rm.coe.int/1680afae3c
3. `data/australia_ai_ethics_principles.pdf` — https://www.industry.gov.au/publications/australias-artificial-intelligence-ethics-principles/australias-ai-ethics-principles
4. `data/canada_directive_automated_decision_making.pdf` — https://publications.gc.ca/collections/collection_2021/sct-tbs/BT48-31-2021-eng.pdf

Until all 11 are present, `run_pipeline()`'s VLS demo path will raise
`PdfExtractionError` for the missing filenames when it reaches them in
`documents.DOCUMENTS`.
