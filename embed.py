"""
embed.py — Embed all chunks and store them in ChromaDB.

Run this once after ingest.py is working:
    python embed.py

The vector store is saved locally in ./chroma_db/
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer
from ingest import build_chunks

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "professor_reviews"
EMBED_MODEL = "all-MiniLM-L6-v2"


def build_vector_store(reset: bool = False):
    """
    Embed all chunks and upsert them into ChromaDB.
    Set reset=True to wipe and rebuild the collection from scratch.
    """
    print(f"Loading embedding model: {EMBED_MODEL} ...")
    model = SentenceTransformer(EMBED_MODEL)

    print("Building chunks from docs/ ...")
    chunks = build_chunks()
    print(f"  → {len(chunks)} chunks ready to embed\n")

    # ── Set up ChromaDB ──────────────────────────────────────────────────
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    if reset and COLLECTION_NAME in [c.name for c in client.list_collections()]:
        client.delete_collection(COLLECTION_NAME)
        print(f"  Deleted existing collection '{COLLECTION_NAME}'")

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},   # cosine similarity
    )

    # ── Embed and upsert in batches ──────────────────────────────────────
    BATCH = 64
    total = len(chunks)

    for i in range(0, total, BATCH):
        batch = chunks[i: i + BATCH]
        texts = [c["text"] for c in batch]
        ids = [c["chunk_id"] for c in batch]
        metadatas = [
            {
                "source": c["source"],
                "professor": c["professor"],
                "course": c["course"],
            }
            for c in batch
        ]

        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        end = min(i + BATCH, total)
        print(f"  Embedded chunks {i+1}–{end} / {total}")

    print(f"\n✅ Vector store built at {CHROMA_DIR}/")
    print(f"   Collection '{COLLECTION_NAME}' contains "
          f"{collection.count()} documents.")
    return collection


if __name__ == "__main__":
    build_vector_store(reset=True)
