"""
query.py — Retrieve relevant chunks and generate a grounded answer via Groq.

Usage:
    python query.py "Which professor is best for students who struggled in Java?"
"""

import os
import sys
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "professor_reviews"
EMBED_MODEL = "all-MiniLM-L6-v2"
GROQ_MODEL = "llama-3.3-70b-versatile"
TOP_K = 4

# ── Load resources once (module-level so Gradio doesn't reload each query) ──
_embed_model = None
_collection = None
_groq_client = None


def _load_resources():
    global _embed_model, _collection, _groq_client

    if _embed_model is None:
        _embed_model = SentenceTransformer(EMBED_MODEL)

    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = client.get_collection(COLLECTION_NAME)

    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY not found. "
                "Add it to your .env file: GROQ_API_KEY=your_key_here"
            )
        _groq_client = Groq(api_key=api_key)


def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Embed the query and return the top_k most similar chunks with metadata.
    Each result: {"text": str, "source": str, "professor": str, "distance": float}
    """
    _load_resources()
    query_embedding = _embed_model.encode(query).tolist()

    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "professor": meta.get("professor", "unknown"),
            "course": meta.get("course", "unknown"),
            "distance": round(dist, 4),
        })
    return chunks


def generate(query: str, chunks: list[dict]) -> str:
    """
    Send the query + retrieved chunks to Groq and return a grounded answer.
    The system prompt strictly enforces grounding — no outside knowledge.
    """
    _load_resources()

    # Build the context block with source labels
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Source {i}: {chunk['source']} — {chunk['professor']}]\n"
            f"{chunk['text']}"
        )
    context = "\n\n".join(context_parts)

    system_prompt = """You are a helpful assistant for FIU CS students trying to choose professors.

STRICT RULES — follow these exactly:
1. Answer ONLY using the information in the provided review excerpts below.
2. Do NOT use any outside knowledge or general assumptions about professors or courses.
3. If the provided excerpts do not contain enough information to answer the question, respond with exactly: "I don't have enough information in the available reviews to answer that."
4. Always cite your sources by referring to the [Source N] labels.
5. Be specific and direct — students need actionable answers."""

    user_message = f"""Review excerpts:
{context}

Student question: {query}"""

    response = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,      # low temp = more consistent, less hallucination
        max_tokens=512,
    )

    return response.choices[0].message.content.strip()


def ask(query: str) -> dict:
    """
    Full pipeline: retrieve chunks → generate grounded answer.
    Returns: {"answer": str, "sources": list[str], "chunks": list[dict]}
    """
    chunks = retrieve(query)
    answer = generate(query, chunks)

    # Deduplicate sources for display
    seen = set()
    sources = []
    for c in chunks:
        key = f"{c['professor']} ({c['source']})"
        if key not in seen:
            seen.add(key)
            sources.append(key)

    return {
        "answer": answer,
        "sources": sources,
        "chunks": chunks,
    }


# ── CLI usage ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python query.py \"your question here\"")
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    print(f"\nQuestion: {question}\n")

    result = ask(question)

    print("Answer:")
    print(result["answer"])
    print("\nSources:")
    for s in result["sources"]:
        print(f"  • {s}")
    print("\nRetrieved chunks (with distances):")
    for i, c in enumerate(result["chunks"], 1):
        print(f"  [{i}] dist={c['distance']} | {c['professor']} | {c['text'][:100]}...")
