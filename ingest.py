"""
ingest.py — Load, clean, and chunk FIU professor review documents.

Each .txt file contains one professor's reviews. We extract individual
reviews as the primary chunks (natural boundaries), then apply a
character-based sliding window for any review longer than 300 chars.
"""

import os
import re

DOCS_DIR = "documents"
CHUNK_SIZE = 300      # characters
CHUNK_OVERLAP = 50    # characters


def parse_document(filepath: str) -> dict:
    """
    Parse a professor review .txt file into structured metadata + reviews.
    Returns a dict with professor, course, department, university, and
    a list of individual review strings.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    # --- Extract header metadata ---
    meta = {}
    for field in ["Professor", "Course", "Department", "University"]:
        match = re.search(rf"^{field}:\s*(.+)$", raw, re.MULTILINE)
        meta[field.lower()] = match.group(1).strip() if match else "Unknown"

    # --- Extract individual reviews (text inside double quotes) ---
    # Each review is on its own line wrapped in "..."
    reviews = re.findall(r'"([^"]{10,})"', raw)

    return {
        "professor": meta["professor"],
        "course": meta["course"],
        "department": meta["department"],
        "university": meta["university"],
        "source": os.path.basename(filepath),
        "reviews": reviews,
    }


def clean_text(text: str) -> str:
    """
    Clean a review string:
    - Collapse multiple spaces/newlines
    - Remove stray HTML entities if any
    - Strip leading/trailing whitespace
    """
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&#39;", "'", text)
    text = re.sub(r"<[^>]+>", "", text)          # strip any stray HTML tags
    text = re.sub(r"\s+", " ", text).strip()
    return text


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split a text string into overlapping character-based chunks.
    Used only when a single review exceeds chunk_size.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start += chunk_size - overlap
    return [c for c in chunks if len(c) > 20]    # drop tiny fragments


def build_chunks(docs_dir: str = DOCS_DIR) -> list[dict]:
    """
    Load all .txt files from docs_dir, parse and clean them, and
    produce a flat list of chunk dicts ready for embedding.

    Each chunk dict:
      {
        "text":       str,   # the chunk content
        "source":     str,   # filename (e.g. Boroojeni_Reviews.txt)
        "professor":  str,
        "course":     str,
        "chunk_id":   str,   # unique ID: source + index
      }
    """
    all_chunks = []
    txt_files = sorted([
        f for f in os.listdir(docs_dir) if f.endswith(".txt")
    ])

    if not txt_files:
        raise FileNotFoundError(
            f"No .txt files found in '{docs_dir}/'. "
            "Make sure your review files are in the docs/ folder."
        )

    for filename in txt_files:
        filepath = os.path.join(docs_dir, filename)
        doc = parse_document(filepath)

        # Prefix added to each chunk so retrieval carries professor context
        context_prefix = (
            f"Professor: {doc['professor']} | "
            f"Course: {doc['course']} | "
        )

        chunk_index = 0
        for review in doc["reviews"]:
            cleaned = clean_text(review)
            if not cleaned:
                continue

            full_text = context_prefix + cleaned

            # If the review fits in one chunk, keep it whole
            if len(full_text) <= CHUNK_SIZE * 1.5:
                all_chunks.append({
                    "text": full_text,
                    "source": doc["source"],
                    "professor": doc["professor"],
                    "course": doc["course"],
                    "chunk_id": f"{filename}_{chunk_index}",
                })
                chunk_index += 1
            else:
                # Long review: split with overlap, keep prefix on each sub-chunk
                sub_chunks = chunk_text(cleaned, CHUNK_SIZE, CHUNK_OVERLAP)
                for sub in sub_chunks:
                    all_chunks.append({
                        "text": context_prefix + sub,
                        "source": doc["source"],
                        "professor": doc["professor"],
                        "course": doc["course"],
                        "chunk_id": f"{filename}_{chunk_index}",
                    })
                    chunk_index += 1

    return all_chunks


# ── Quick inspection when run directly ─────────────────────────────────────
if __name__ == "__main__":
    chunks = build_chunks()

    print(f"\n{'='*60}")
    print(f"Total chunks produced: {len(chunks)}")
    print(f"{'='*60}\n")

    print("── 5 sample chunks ──────────────────────────────────────\n")
    import random
    for c in random.sample(chunks, min(5, len(chunks))):
        print(f"[{c['chunk_id']}]")
        print(f"  Source    : {c['source']}")
        print(f"  Professor : {c['professor']}")
        print(f"  Text      : {c['text'][:200]}...")
        print()

    # Sanity checks
    empty = [c for c in chunks if not c["text"].strip()]
    print(f"Empty chunks     : {len(empty)}  (should be 0)")
    print(f"Shortest chunk   : {min(len(c['text']) for c in chunks)} chars")
    print(f"Longest chunk    : {max(len(c['text']) for c in chunks)} chars")
    print(f"Average length   : {sum(len(c['text']) for c in chunks)//len(chunks)} chars")
