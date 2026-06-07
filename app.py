"""
app.py — Gradio web interface for the FIU CS Professor Unofficial Guide.

Run:
    python app.py
Then open http://localhost:7860 in your browser.
"""

import gradio as gr
from query import ask


def handle_query(question: str):
    """Called by Gradio when the user submits a question."""
    if not question.strip():
        return "Please enter a question.", "", ""

    result = ask(question)

    sources_text = "\n".join(f"• {s}" for s in result["sources"])

    # Show retrieved chunks with distances for transparency
    chunks_text = ""
    for i, c in enumerate(result["chunks"], 1):
        chunks_text += (
            f"[{i}] {c['professor']} | dist={c['distance']}\n"
            f"    {c['text'][:200]}...\n\n"
        )

    return result["answer"], sources_text, chunks_text.strip()


# ── Build the UI ─────────────────────────────────────────────────────────────
with gr.Blocks(title="FIU CS Professor Unofficial Guide") as demo:
    gr.Markdown(
        """
        # 🎓 FIU CS Professor Unofficial Guide
        Ask anything about FIU Computer Science professors based on real student reviews.

        **Examples:**
        - *Which professor is best for students who struggled in Java?*
        - *Does Boroojeni allow notes on his exams?*
        - *Which professors read directly off PowerPoint slides?*
        - *What do students say about Sadjadi's organization?*
        """
    )

    with gr.Row():
        question_input = gr.Textbox(
            label="Your question",
            placeholder="e.g. Which CS professor gives the most useful feedback?",
            lines=2,
            scale=4,
        )

    ask_btn = gr.Button("Ask", variant="primary")

    with gr.Row():
        answer_output = gr.Textbox(
            label="Answer",
            lines=8,
            interactive=False,
        )

    with gr.Row():
        sources_output = gr.Textbox(
            label="Sources used",
            lines=4,
            interactive=False,
        )

    with gr.Accordion("Retrieved chunks (for transparency)", open=False):
        chunks_output = gr.Textbox(
            label="Raw retrieved chunks + similarity scores",
            lines=12,
            interactive=False,
        )

    # Wire up interactions
    ask_btn.click(
        fn=handle_query,
        inputs=question_input,
        outputs=[answer_output, sources_output, chunks_output],
    )
    question_input.submit(
        fn=handle_query,
        inputs=question_input,
        outputs=[answer_output, sources_output, chunks_output],
    )

if __name__ == "__main__":
    demo.launch()
