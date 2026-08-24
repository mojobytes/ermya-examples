# PDF sources

Provenance for the 11 official AI-governance documents used by the VLS demo
(see `documents.py` for the per-document owner ACL). All PDFs are committed to
the repo so the example runs offline with no live network access.

| filename | jurisdiction | source URL | retrieved | status |
|----------|--------------|------------|-----------|--------|
| eu_ai_act.pdf | EU | https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202401689 | 2026-07-22 | downloaded |
| uk_pro_innovation_white_paper.pdf | UK | https://assets.publishing.service.gov.uk/media/64cb71a547915a00142a91c4/a-pro-innovation-approach-to-ai-regulation-amended-web-ready.pdf | 2026-07-22 | downloaded |
| unesco_ethics_of_ai.pdf | UNESCO | https://unesdoc.unesco.org/ark:/48223/pf0000381137 | 2026-07-22 | downloaded (manual, via browser — site blocks automated clients) |
| oecd_recommendation_ai.pdf | OECD | https://legalinstruments.oecd.org/api/print?ids=648&lang=en | 2026-07-22 | downloaded |
| council_of_europe_framework_convention.pdf | CoE | https://rm.coe.int/1680afae3c (CETS 225) | 2026-07-22 | downloaded (manual, via browser — site blocks automated clients) |
| nist_ai_rmf_1_0.pdf | US | https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf | 2026-07-22 | downloaded |
| australia_ai_ethics_principles.pdf | AU | https://www.industry.gov.au/ — "Guidance for AI adoption: Implementation practices" (DISR). Substituted for the AI Ethics Principles, which are published as HTML only; this is the closest official AU governance PDF | 2026-07-22 | downloaded (manual, via browser) |
| canada_directive_automated_decision_making.pdf | CA | https://publications.gc.ca/collections/collection_2021/sct-tbs/BT48-31-2021-eng.pdf | 2026-07-22 | downloaded (manual, via browser — site blocks automated clients) |
| singapore_model_ai_governance_genai.pdf | SG | https://aiverifyfoundation.sg/downloads/Proposed_MGF_Gen_AI_2024.pdf | 2026-07-22 | downloaded |
| japan_ai_guidelines_for_business.pdf | JP | https://www.meti.go.jp/shingikai/mono_info_service/ai_shakai_jisso/pdf/20240419_9.pdf | 2026-07-22 | downloaded |
| south_korea_ai_basic_act.pdf | KR | https://cset.georgetown.edu/wp-content/uploads/t0625_south_korea_ai_law_EN.pdf (CSET/Georgetown English translation; no official English-language PDF found) | 2026-07-22 | downloaded |

All 11 documents are present as of 2026-07-22. Four of them (UNESCO, CoE,
Australia, Canada) block automated downloads (Cloudflare challenge or
JS-driven interstitial) and were fetched manually via a real browser. The
Australian entry is the DISR "Guidance for AI adoption: Implementation
practices" PDF, substituted for the AI Ethics Principles page, which is
published as HTML only.
