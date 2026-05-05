# SAFRAG — SAF + RAG Pipeline
# Author: Dr. Amudha Kumari Duraisamy
# Script: query.py — Retrieve relevant chunks from ChromaDB and synthesize answers via LLM.
# Usage:  python scripts/query.py "Your question here"
#         python scripts/query.py --backend anthropic "Your question here"

import os
import sys
import chromadb
import ollama as ollama_client
import anthropic as anthropic_client
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent
CHROMA_DIR = str(ROOT / "chroma_db")
COLLECTION_NAME = "safrag_papers"
N_RESULTS = 8
MAX_CONTEXT_CHARS = 12000

# Default models per backend
OLLAMA_DEFAULT_MODEL = "llama3.2"
ANTHROPIC_DEFAULT_MODEL = "claude-sonnet-4-6"


def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_collection(COLLECTION_NAME)


def get_all_sources() -> list[str]:
    """Return all unique paper source names in the index."""
    collection = get_collection()
    result = collection.get(include=["metadatas"])
    seen = set()
    sources = []
    for meta in result["metadatas"]:
        s = meta["source"]
        if s not in seen:
            seen.add(s)
            sources.append(s)
    return sorted(sources)


def detect_paper_filter(question: str) -> list[str] | None:
    """
    Check if the question mentions a specific paper by author name or year.
    Returns a list of matching source names, or None if no specific paper detected.

    Example: "What genera were dominant in Tonanzi 2020?"
             → ["Tonanzi_2020_SCFA_semi_FW"]
    """
    question_lower = question.lower()
    sources = get_all_sources()
    matched = []

    for source in sources:
        # source looks like "Tonanzi_2020_SCFA_semi_FW"
        parts = source.lower().split("_")
        author = parts[0]           # e.g. "tonanzi"
        year   = parts[1] if len(parts) > 1 else ""  # e.g. "2020"

        # Match if author name appears in question
        if author in question_lower:
            # If a year is also mentioned, require it to match too
            if year and year in question_lower:
                matched.append(source)
            elif year and year not in question_lower:
                matched.append(source)   # year not mentioned → include all by that author
            else:
                matched.append(source)

    return matched if matched else None


def retrieve(question: str, n_results: int = N_RESULTS) -> list[dict]:
    collection = get_collection()

    # Detect if question targets a specific paper → apply metadata filter
    paper_filter = detect_paper_filter(question)

    query_kwargs = dict(
        query_texts=[question],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    if paper_filter:
        if len(paper_filter) == 1:
            query_kwargs["where"] = {"source": {"$eq": paper_filter[0]}}
        else:
            query_kwargs["where"] = {"source": {"$in": paper_filter}}
        # For single-paper queries, retrieve more chunks for full coverage
        query_kwargs["n_results"] = min(n_results * 2, 20)

    results = collection.query(**query_kwargs)

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": doc,
            "source": meta["source"],
            "chunk_index": meta["chunk_index"],
            "distance": round(dist, 4),
        })

    return chunks, paper_filter


def build_context(chunks: list[dict]) -> str:
    parts = []
    total = 0
    for chunk in chunks:
        entry = f"[Source: {chunk['source']}]\n{chunk['text']}"
        if total + len(entry) > MAX_CONTEXT_CHARS:
            break
        parts.append(entry)
        total += len(entry)
    return "\n\n---\n\n".join(parts)


def _answer_ollama(system_prompt: str, user_prompt: str, model: str) -> str:
    response = ollama_client.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.message.content


def _answer_anthropic(system_prompt: str, user_prompt: str, model: str) -> str:
    client = anthropic_client.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


def ask(
    question: str,
    n_results: int = N_RESULTS,
    backend: str = "ollama",
    model: str | None = None,
) -> dict:
    chunks, paper_filter = retrieve(question, n_results)
    context = build_context(chunks)
    sources = list(dict.fromkeys(c["source"] for c in chunks))

    system_prompt = (
        "You are an expert in chain elongation (CE) fermentation, medium-chain carboxylic acid (MCCA) "
        "production, and sustainable aviation fuel (SAF) research. "
        "Your job is to extract and synthesize specific scientific data from the provided literature excerpts.\n\n"
        "Rules:\n"
        "- Always search the excerpts thoroughly for numerical values: concentrations (g/L), "
        "HRT (days/hours), pH, temperature, yields, productivities, and reactor conditions.\n"
        "- Cite every claim with its source name (e.g., 'Kucek_2016'), using the exact source tag shown.\n"
        "- If multiple papers report the same metric, compare them in a structured way.\n"
        "- If a value appears as a table, list, or inline number in the text, extract it.\n"
        "- NEVER say information is missing without first scanning every excerpt carefully.\n"
        "- Only say data is unavailable if it is genuinely absent from all provided excerpts."
    )

    user_prompt = (
        f"Literature excerpts:\n\n{context}\n\n"
        f"---\n\nQuestion: {question}\n\n"
        "Provide a concise, accurate answer citing the relevant sources."
    )

    if backend == "ollama":
        resolved_model = model or OLLAMA_DEFAULT_MODEL
        answer = _answer_ollama(system_prompt, user_prompt, resolved_model)
    elif backend == "anthropic":
        resolved_model = model or ANTHROPIC_DEFAULT_MODEL
        answer = _answer_anthropic(system_prompt, user_prompt, resolved_model)
    else:
        raise ValueError(f"Unknown backend: '{backend}'. Choose 'ollama' or 'anthropic'.")

    return {
        "answer": answer,
        "sources": sources,
        "chunks": chunks,
        "backend": backend,
        "model": resolved_model,
        "paper_filter": paper_filter,   # None = global search, list = filtered to specific papers
    }


if __name__ == "__main__":
    args = sys.argv[1:]
    backend = "ollama"

    if "--backend" in args:
        idx = args.index("--backend")
        backend = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    question = " ".join(args) if args else (
        "Which papers reported MCCA production above 8 g/L and what HRT did they use?"
    )

    print(f"\nSAFRAG Query — Dr. Amudha Kumari Duraisamy")
    print(f"Backend: {backend}  |  Question: {question}\n")

    result = ask(question, backend=backend)

    print("Answer:\n")
    print(result["answer"])
    print(f"\nModel: {result['model']}")
    print(f"Sources consulted: {', '.join(result['sources'])}")
