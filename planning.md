# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

This project focuses on FIU Computer Science professor reviews collected from Rate My Professors. Students rely on this kind of peer feedback constantly when registering for classes, but the information is scattered across individual professor pages and hard to search by specific criteria. This guide makes real student opinions searchable by question — so instead of clicking through 10 profiles, a student can just ask "which professor curves their exams?" and get a grounded answer drawn from actual reviews.

---

## Documents

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Rate My Professors | Reviews for Prof. Kianoosh Boroojeni — CDA3102 Computer Architecture | docs/Boroojeni_Reviews.txt |
| 2 | Rate My Professors | Reviews for Prof. Kiavash Bahreini — COP3337 Computer Programming II | docs/Bahreini_Reviews.txt |
| 3 | Rate My Professors | Reviews for Prof. Patricia McDermott Wells — CEN3721 Human-Computer Interaction | docs/McDermott_Reviews.txt |
| 4 | Rate My Professors | Reviews for Prof. Masoud Sadjadi — CIS3950 Capstone I | docs/Sadjadi_Reviews.txt |
| 5 | Rate My Professors | Reviews for Prof. Niemah Osman — COP4710 Database Management | docs/Osman_Reviews.txt |
| 6 | Rate My Professors | Reviews for Prof. Gregory Reis — COP4555 Principles of Programming Languages | docs/Reis_Reviews.txt |
| 7 | Rate My Professors | Reviews for Prof. Fatima Boujarwah — CDA3102 Computer Architecture | docs/Boujarwah_Reviews.txt |
| 8 | Rate My Professors | Reviews for Prof. Rehan Akbar — CEN5087 Software and Data Modeling | docs/Akbar_Reviews.txt |
| 9 | Rate My Professors | Reviews for Prof. Richard Whittaker — COP3337 Computer Programming II | docs/Wittaker_Reviews.txt |
| 10 | Rate My Professors | Reviews for Prof. Mustafa Ocal — COP3084 Intermediate Java Programming | docs/Mustafa_Ocal_Reviews.txt |

---

## Chunking Strategy

**Chunk size:** 300 characters

**Overlap:** 50 characters

**Reasoning:** Each document contains individual Rate My Professors reviews that are short and self-contained — typically 2 to 5 sentences expressing one student's complete opinion. Chunking by individual review preserves these natural boundaries so each chunk carries a complete thought. The 300-character limit catches any review that runs long and splits it cleanly, while the 50-character overlap ensures that if a key point falls near a boundary, it still appears in both adjacent chunks and remains retrievable. Larger chunks would merge unrelated opinions from different students; smaller chunks would break mid-sentence and lose meaning.

---

## Retrieval Approach

**Embedding model:** all-MiniLM-L6-v2 via sentence-transformers (runs locally, no API key required)

**Top-k:** 4

**Production tradeoff reflection:** For a real deployment I would consider OpenAI's text-embedding-3-small or Cohere's embed-v3 models. The tradeoffs I'd weigh are: context length (all-MiniLM-L6-v2 caps at 256 tokens, which is fine for short reviews but would fail on longer documents), multilingual support (relevant if serving non-English speaking students), domain-specific accuracy (a model fine-tuned on educational or review text would likely outperform a general-purpose model here), and latency vs. cost (local models like MiniLM have zero API cost and no rate limits, but API-based models tend to produce better embeddings for nuanced semantic queries). For this project's scope, MiniLM is the right call.

---

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | Which professor is best for students who struggled in their first Java class? | Mustafa Ocal — reviews specifically mention he helps students who did poorly in Java 1 |
| 2 | Does Boroojeni allow notes on his exams? | Yes — students say he allows unlimited paper notes on test day |
| 3 | What do students say about Sadjadi's organization? | He is described as disorganized and vague, rarely responds to emails, and gives unclear expectations |
| 4 | How is grading structured in Reis's COP4555? | Approximately 40% quizzes and discussions, 30% project, 30% exams (midterm and final) |
| 5 | Which professors are known for reading directly off PowerPoint slides? | Osman, Akbar, and Boujarwah are all mentioned by students for reading off slides |

---

## Anticipated Challenges

1. **Short reviews may produce low-signal embeddings.** Some reviews are only 1–2 sentences, which gives the embedding model very little text to work with. If the query uses different vocabulary than the review (e.g., query says "lenient grader" but the review says "curves a lot"), semantic similarity may be too low to retrieve the right chunk. This could cause relevant reviews to be missed entirely.

2. **Multiple professors teaching the same course.** Both Boroojeni and Boujarwah teach CDA3102, and both Bahreini and Whittaker teach COP3337. A query about "Computer Architecture" or "Programming II" without a professor name could retrieve chunks from both professors and produce a confusing or blended answer. The grounding prompt needs to be specific about citing sources so students can tell which professor a statement applies to.

---

## Architecture
┌─────────────────────────────────────────────────────────────────┐
│                         PIPELINE                                │
│                                                                 │
│  [1] Document Ingestion          [2] Chunking                   │
│      docs/*.txt                      300 chars / 50 overlap     │
│      Custom parser (ingest.py)       Split by review boundary   │
│             │                                │                  │
│             └──────────────┬─────────────────┘                  │
│                            ▼                                    │
│  [3] Embedding + Vector Store                                   │
│      all-MiniLM-L6-v2 (sentence-transformers)                   │
│      ChromaDB (local persistent store)                          │
│             │                                                   │
│             ▼                                                   │
│  [4] Retrieval                                                  │
│      Cosine similarity search, top-k = 4                        │
│      Returns chunks + source metadata                           │
│             │                                                   │
│             ▼                                                   │
│  [5] Generation                                                 │
│      Groq API — llama-3.3-70b-versatile                         │
│      Grounded prompt (context-only, source citation required)   │
│             │                                                   │
│             ▼                                                   │
│  [6] Interface                                                  │
│      Gradio web UI (app.py) — localhost:7860                    │
└─────────────────────────────────────────────────────────────────┘

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
I handled the document structure and chunking logic, and then realized splitting by review just made way more sense since each review is already complete. I gave Claude my Documents table, Chunking Strategy section, and explained the exact format of my files (professor name, course header, then quoted reviews line by line) and asked it to help me write `ingest.py` based on what I had already planned. I reviewed what it generated, made sure the `parse_document()` function actually matched my file format, and verified it worked by running `python ingest.py` and reading through 5 sample chunks to confirm each one had clean review text with professor metadata attached.

**Milestone 4 — Embedding and retrieval:**
I gave Claude my Retrieval Approach section and architecture diagram and asked it to help implement `embed.py` and the `retrieve()` function in `query.py`. I tested retrieval myself by running 3 of my evaluation questions and checking that the returned chunks were actually relevant and that distance scores were below 0.5.

**Milestone 5 — Generation and interface:**
The grounding rule was set up so the system won’t guess when the docs don’t have enough info. With that requirement and the output format in place, Claude helped implement generate(), the Gradio UI, and a cleaner ASCII diagram. The grounding was verified by asking something outside the docs and confirming it responded with not enough information.
