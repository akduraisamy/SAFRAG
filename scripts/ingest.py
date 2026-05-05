# SAFRAG — SAF + RAG Pipeline
# Author: Dr. Amudha Kumari Duraisamy
# Script: ingest.py — Extract text from PDFs, chunk, and embed into ChromaDB.
# Usage:  python scripts/ingest.py

import os
import re
import pdfplumber
import chromadb
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent
LITERATURE_DIR = ROOT / "literatures"
CHROMA_DIR = str(ROOT / "chroma_db")
COLLECTION_NAME = "safrag_papers"
CHUNK_SIZE = 800      # characters (~150-200 tokens for dense scientific text)
CHUNK_OVERLAP = 150


def extract_text(pdf_path: Path) -> str:
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def chunk_text(text: str, source: str) -> list[dict]:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    chunks = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = start + CHUNK_SIZE

        # Break at sentence boundary where possible
        if end < len(text):
            boundary = text.rfind(". ", start, end)
            if boundary != -1 and boundary > start + CHUNK_SIZE // 2:
                end = boundary + 1

        chunk = text[start:end].strip()
        if len(chunk) > 100:
            chunks.append({
                "text": chunk,
                "source": source,
                "chunk_index": chunk_index,
                "id": f"{source}__chunk{chunk_index}",
            })
            chunk_index += 1

        start = end - CHUNK_OVERLAP

    return chunks


def ingest():
    pdf_files = sorted(LITERATURE_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {LITERATURE_DIR}/")
        return

    print(f"SAFRAG Ingest — Dr. Amudha Kumari Duraisamy")
    print(f"Found {len(pdf_files)} PDFs to ingest.\n")

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    try:
        client.delete_collection(COLLECTION_NAME)
        print("Cleared existing collection.")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    all_ids, all_docs, all_metas = [], [], []

    for pdf_path in pdf_files:
        source = pdf_path.stem
        print(f"  Processing: {source} ...", end=" ", flush=True)

        try:
            text = extract_text(pdf_path)
            chunks = chunk_text(text, source)
            print(f"{len(chunks)} chunks")

            for chunk in chunks:
                all_ids.append(chunk["id"])
                all_docs.append(chunk["text"])
                all_metas.append({
                    "source": chunk["source"],
                    "chunk_index": chunk["chunk_index"],
                })

        except Exception as e:
            print(f"FAILED — {e}")

    batch_size = 100
    for i in range(0, len(all_ids), batch_size):
        collection.add(
            ids=all_ids[i:i + batch_size],
            documents=all_docs[i:i + batch_size],
            metadatas=all_metas[i:i + batch_size],
        )

    print(f"\nDone. {len(all_ids)} total chunks stored in '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    ingest()
