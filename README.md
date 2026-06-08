# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

FIU Computer Science professor reviews collected from Rate My Professors.
This kind of knowledge is super useful when you're trying to pick classes
but it's scattered across individual professor pages and you have to click
through each one manually. There's no way to just ask "who curves their
exams?" or "which professor actually explains things well?" and get a real
answer. Official course listings tell you nothing about teaching style,
how hard the exams are, or whether the professor even responds to emails.
This system makes all that real student feedback searchable in plain
language.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Rate My Professors | .txt file | docs/Boroojeni_Reviews.txt |
| 2 | Rate My Professors | .txt file | docs/Bahreini_Reviews.txt |
| 3 | Rate My Professors | .txt file | docs/McDermott_Reviews.txt |
| 4 | Rate My Professors | .txt file | docs/Sadjadi_Reviews.txt |
| 5 | Rate My Professors | .txt file | docs/Osman_Reviews.txt |
| 6 | Rate My Professors | .txt file | docs/Reis_Reviews.txt |
| 7 | Rate My Professors | .txt file | docs/Boujarwah_Reviews.txt |
| 8 | Rate My Professors | .txt file | docs/Akbar_Reviews.txt |
| 9 | Rate My Professors | .txt file | docs/Wittaker_Reviews.txt |
| 10 | Rate My Professors | .txt file | docs/Mustafa_Ocal_Reviews.txt |

All 10 files were manually collected from Rate My Professors and saved as
plain text. Each file covers one FIU CS professor and includes 5 student
reviews. Together they cover 8 different courses across the CS department,
so questions about exams, grading, teaching style, and workload are all
represented.

---

## Chunking Strategy

**Chunk size:** 300 characters

**Overlap:** 50 characters

**Why these choices fit your documents:**
Rate My Professors reviews are short and self-contained. Each one is
basically one student's complete take on a professor, usually 2 to 5
sentences. So it made more sense to split on individual review boundaries
rather than just chopping every 300 characters blindly. The 300-character
limit is there as a fallback for any review that runs long, and the
50-character overlap makes sure nothing important gets cut off at a
boundary. Every chunk also gets a prefix with the professor name and course number like `Professor: Mustafa Ocal | Course: COP3084 ` so that retrieval always knows who the review is about, even when the student never mentions the professor by name in the review itself.

**Final chunk count:** 53 chunks across 10 documents

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`, stored
in ChromaDB locally using cosine similarity. Top-k set to 4.

**Production tradeoff reflection:**
MiniLM worked well for this project because it runs locally, needs no API key, and made testing fast and free. Its small context window is fine for short RMP reviews, but it would struggle with longer documents like syllabi or anything more detailed. If this were a real deployment, I’d probably look at something stronger like OpenAI’s text‑embedding‑3‑small since it handles academic language better and supports more use cases, though it comes with cost and rate limits. For this specific setup with short, opinion‑based reviews, MiniLM actually performs well and the retrieval results showed that.

---

## Grounded Generation

**System prompt grounding instruction:**
The system prompt passed to `llama-3.3-70b-versatile` via Groq contains
two hard rules:

1. "Answer ONLY using the information in the provided review excerpts."
2. "If the provided excerpts do not contain enough information to answer
   the question, respond with exactly: 'I don't have enough information
   in the available reviews to answer that.'"

Retrieved chunks are passed to the model as numbered [Source N] blocks, each one labeled with the professor name and the file it came from. The model is instructed to refer to these sources by their number, which keeps the answer grounded. I set the temperature to 0.2 so the responses stay consistent and don’t drift into general knowledge. The word “ONLY” in the prompt is intentional because softer instructions like “try to use the documents” aren’t strong enough to stop an LLM from relying on what it already knows.

**How source attribution is surfaced in the response:**
Two ways. First, the model is instructed to cite `[Source N]` labels
inline in its answer. Second, the source filenames and professor names
are appended programmatically after generation from the chunk metadata,
so they always show up in the Sources field of the UI regardless of
whether the model remembered to cite them.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Which professor is best for students who struggled in Java 1? | Mustafa Ocal | Correctly identified Ocal, cited his review about going from a C to an A | Relevant | Accurate |
| 2 | Does Boroojeni allow notes on his exams? | Yes, unlimited paper notes | Correctly said yes, cited unlimited notes and open-notes policies | Relevant | Accurate |
| 3 | What do students say about Sadjadi's organization? | Disorganized, vague, hard to contact | Correctly called him disorganized but also retrieved a Boujarwah chunk about being organized | Partially relevant | Partially accurate |
| 4 | How is grading structured in Reis's COP4555? | 40% quizzes, 30% project, 30% exams | Returned exact breakdown: 40% HW/quizzes, 30% project, 30% exams | Relevant | Accurate |
| 5 | Which professors are known for reading off PowerPoint slides? | Osman, Akbar, and Boujarwah | Got Akbar and Osman right, missed Boujarwah, pulled in McDermott instead | Partially relevant | Partially accurate |

---

## Failure Case Analysis

**Question that failed:** Question 3 — "What do students say about
Sadjadi's organization?"

**What the system returned:** The system did say Sadjadi is disorganized, which is correct. But one of the retrieved chunks was actually a Boujarwah review saying she is “organized and concise,” which is the complete opposite and not even about the same professor. The model tried to work around it, but it made the answer sound weird.

**Root cause (tied to a specific pipeline stage):** This is a retrieval mistake. The embedding model matched on the word “organized” and pulled in Boujarwah’s review just because it shared that word, even though the question was clearly about Sadjadi. Since all chunks from all professors live in the same ChromaDB collection with no filters, the retriever can’t tell that the query is professor‑specific.

**What you would change to fix it:** Add metadata filtering during retrieval. If the question mentions a professor by name, only return chunks where the professor field matches. ChromaDB supports this with a simple where filter, and adding that one line would have stopped Boujarwah’s chunk from ever showing up for a Sadjadi question.

---

## Spec Reflection

**One way the spec helped you during implementation:**
Writing the chunking plan in planning.md before coding actually helped a lot. It made me think about how the reviews were structured and pushed me to choose review‑based chunks instead of random character cuts. Because of that, the ingestion code had a clear goal and the chunks came out clean on the first try. I don’t think that would have happened if I had just guessed a number and started coding.

**One way your implementation diverged from the spec, and why:**
One way your implementation diverged from the spec, and why:  
The spec assumed retrieval issues would come from chunks being too small or messy, but the real problem was different. Some professors shared words like “organized,” so the retriever sometimes pulled chunks from the wrong person. I didn’t expect that at all when writing the spec. The fix was adding metadata filtering so the system only returns chunks for the professor mentioned in the question. That wasn’t in the original plan, but it ended up being the right solution and a good reminder that the spec is a starting point, not a perfect prediction.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* I shared my Documents table, the Chunking Strategy from `planning.md`, and an explanation of how my text files are structured. Each file starts with the professor name and course, followed by individual quoted reviews on separate lines.
- *What it produced:* It generated a working `ingest.py` with a `parse_document()` function that used regex to pull out reviews and a `chunk_text()` fallback for longer ones.
- *What I changed or overrode:* The generated code didn’t add any professor context to the chunks, so reviews that never mentioned the professor would lose their attribution. I fixed that by adding a prefix like `Professor: X | Course: Y |` to every chunk so retrieval always knows who the review is about.

**Instance 2**

- *What I gave the AI:* I gave it my grounding requirement that the system should refuse to answer when the documents don’t cover the topic. I also gave it the answer format I wanted, including the `[Source N]` citations, and the Groq model I was using.
- *What it produced:* It wrote a `generate()` function with a system prompt that said the model should “try to answer only from the provided documents.”
- *What I changed or overrode:* “Try” is too weak. Models will still guess if the context is thin. I rewrote the instruction to say “Answer ONLY using the information in the provided review excerpts” and added a specific fallback phrase for when there isn’t enough information. That made the refusal behavior consistent instead of unpredictable.
