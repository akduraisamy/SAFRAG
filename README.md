# SAFRAG — SAF + RAG Pipeline

**Author:** Dr. Amudha Kumari Duraisamy  
**Domain:** Chain Elongation (CE) Fermentation | Synthetic Biology | Bioreactor Engineering

A local Retrieval-Augmented Generation (RAG) system for querying a corpus of chain elongation fermentation literature. Ask cross-paper scientific questions in plain language and get cited, evidence-grounded answers.

---

## What It Does

- Embeds your CE fermentation PDFs once into a local vector database (ChromaDB)
- Retrieves the most semantically relevant passages for any question
- Synthesizes a precise, source-cited answer using a large language model
- Runs entirely on your machine — no data leaves your system except the final LLM query

---

## Project Structure

```
SAFRAG/
├── app.py                  # Streamlit UI entry point
├── scripts/
│   ├── ingest.py           # PDF → chunks → ChromaDB (run once)
│   └── query.py            # RAG retrieval + LLM answer (CLI)
├── literatures/            # Your CE fermentation PDFs
├── chroma_db/              # Persisted vector index (auto-generated)
├── requirements.txt
├── .env                    # API key (never commit this)
├── .env.example            # Template for .env
├── Dockerfile
├── docker-compose.yml
└── ROADMAP.md
```

---

## Quickstart

### 1. Clone and install

```bash
git clone <your-repo-url>
cd SAFRAG
pip install -r requirements.txt
```

### 2. Configure API key

```bash
cp .env.example .env
# Open .env and set your ANTHROPIC_API_KEY
```

### 3. Add your PDFs

Drop your CE fermentation PDFs into the `literatures/` folder.

### 4. Index the literature (run once)

```bash
python scripts/ingest.py
```

This extracts text, chunks it into ~800-character segments, and embeds everything into ChromaDB locally. Only needed again if you add new papers.

### 5. Launch the UI

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### CLI mode (optional)

```bash
python scripts/query.py "Which papers reported MCCA > 8 g/L and what HRT did they use?"
```

---

## Docker

### Build and run

```bash
docker-compose up --build
```

The app will be available at [http://localhost:8501](http://localhost:8501).

### First-time indexing inside Docker

```bash
docker-compose run --rm app python scripts/ingest.py
```

### Environment variables for Docker

Set `ANTHROPIC_API_KEY` in your shell before running:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
docker-compose up
```

Or copy `.env.example` to `.env` and fill in your key — docker-compose will pick it up automatically.

---

## Example Questions

| Question | What it tests |
|---|---|
| Which papers reported MCCA > 8 g/L and what HRT did they use? | Cross-paper yield + operating conditions |
| Which feedstocks appeared in semi-continuous setups? | Reactor type + substrate linkage |
| What genera were dominant in Tonanzi 2020? | Microbial community per paper |
| Compare ethanol-to-acetate ratios across studies | Stoichiometry comparison |
| What pH conditions were used in continuous reactors? | Operating parameter survey |

---

## Configuration

| Parameter | Location | Default | Description |
|---|---|---|---|
| `CHUNK_SIZE` | `scripts/ingest.py` | 800 chars | Text chunk size |
| `CHUNK_OVERLAP` | `scripts/ingest.py` | 150 chars | Overlap between chunks |
| `N_RESULTS` | `scripts/query.py` | 8 | Chunks retrieved per query |
| `MAX_CONTEXT_CHARS` | `scripts/query.py` | 12000 | Max context sent to LLM |
| Chunks retrieved | Streamlit sidebar | 4–16 | Adjustable per query |

---

## Stack

| Component | Library | Purpose |
|---|---|---|
| Vector DB | ChromaDB | Local persistent embedding store |
| Embeddings | all-MiniLM-L6-v2 (ONNX) | Free, local sentence embeddings |
| PDF parsing | pdfplumber | Robust text + layout extraction |
| LLM | Anthropic API | Answer synthesis |
| UI | Streamlit | Interactive web interface |

---

## Security Notes

- Never commit `.env` — it contains your API key
- `chroma_db/` contains your embedded literature; keep it local
- The LLM query sends retrieved text excerpts to the Anthropic API — no raw PDFs

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Dr. Amudha Kumari Duraisamy

Free to use, modify, and distribute with attribution.
