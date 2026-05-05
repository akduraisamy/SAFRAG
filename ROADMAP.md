# SAFRAG Roadmap

**Author:** Dr. Amudha Kumari Duraisamy  
**Last updated:** May 2026

---

## Phase 1 — Core RAG Pipeline ✅ COMPLETE

**Goal:** Functional local Q&A over CE fermentation PDFs.

- [x] PDF text extraction with pdfplumber
- [x] Sentence-boundary-aware chunking (800 chars, 150 overlap)
- [x] Local vector embeddings via ChromaDB (all-MiniLM-L6-v2)
- [x] Semantic retrieval with cosine similarity
- [x] LLM answer synthesis with source citation
- [x] Streamlit UI with example questions and chunk viewer
- [x] CLI mode for quick terminal queries
- [x] Docker support

---

## Phase 2 — Smarter Retrieval 🔄 NEXT

**Goal:** Improve answer quality and reduce hallucination.

- [ ] **Metadata-aware filtering** — filter by paper name, year, reactor type before retrieval
- [ ] **Hybrid search** — combine semantic (vector) + keyword (BM25) retrieval
- [ ] **Re-ranking** — cross-encoder re-ranking of retrieved chunks (e.g., `ms-marco-MiniLM`)
- [ ] **Multi-query expansion** — auto-generate query variants to improve recall
- [ ] **Table extraction** — parse and index HTML/structured tables from PDFs separately
- [ ] **SI paper linking** — associate supplementary info files with their parent paper

---

## Phase 3 — Structured Data Extraction

**Goal:** Go from Q&A to structured outputs useful for data analysis.

- [ ] **Auto-extract key parameters** — HRT, pH, temperature, yield, feedstock from all papers
- [ ] **Export to CSV/Excel** — structured comparison table across papers
- [ ] **Contradiction detection** — flag when papers report conflicting values
- [ ] **Paper summary cards** — auto-generate a 1-page summary per paper

---

## Phase 4 — Multi-modal Support

**Goal:** Handle figures, diagrams, and tables embedded in PDFs.

- [ ] **Figure extraction** — extract reactor diagrams and performance graphs
- [ ] **OCR for scanned PDFs** — handle image-based PDFs (e.g., older papers)
- [ ] **Table-to-JSON** — convert embedded tables to structured data
- [ ] **Visual Q&A** — describe or query extracted figures

---

## Phase 5 — LitHarvest Integration

**Goal:** Evolve SAFRAG into a full literature management pipeline (LitHarvest).

- [ ] **Automated paper discovery** — PubMed / Semantic Scholar API integration
- [ ] **Relevance scoring** — rank new papers by domain fit before adding to corpus
- [ ] **Citation graph** — build and visualize citation relationships
- [ ] **Auto-update pipeline** — weekly crawl for new CE fermentation publications
- [ ] **Zotero / Mendeley sync** — pull PDFs directly from reference manager

---

## Phase 6 — Deployment & Collaboration

**Goal:** Make SAFRAG shareable within a research group.

- [ ] **Multi-user auth** — per-user API key management
- [ ] **Shared corpus** — team-level shared ChromaDB index
- [ ] **Query history** — save and revisit past queries per user
- [ ] **Cloud deployment** — one-click deploy to Hugging Face Spaces or Streamlit Cloud
- [ ] **REST API** — expose `ask()` as an HTTP endpoint for programmatic use

---

## Known Limitations (Current)

| Limitation | Notes |
|---|---|
| No table-aware chunking | Tables split across chunks may lose structure |
| SI files not auto-linked | Supplementary PDFs indexed independently |
| English-only | Non-English abstracts not handled |
| Single corpus | One ChromaDB collection; no multi-project support |

---

## Contribution Notes

This is a solo research tool. If extending for group use, please:
1. Keep `.env` out of version control
2. Run `python scripts/ingest.py` after adding new papers
3. Tag issues with `phase-2`, `phase-3`, etc. for triage
