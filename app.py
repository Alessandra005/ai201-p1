"""
app.py — Gradio web interface for the FIU CS Professor Unofficial Guide.

Run:
    python app.py
Then open http://localhost:7860 in your browser.
"""

import gradio as gr
from query import ask

SUGGESTIONS = [
    "Who should I take for Java if I struggled?",
    "Which professors curve their exams?",
    "Who reads off PowerPoint slides?",
    "What's Whittaker like as a professor?",
    "How hard is Sadjadi's Capstone?",
]


def handle_query(question: str):
    if not question.strip():
        return "Please enter a question.", "", ""

    result = ask(question)
    sources_text = "\n".join(f"• {s}" for s in result["sources"])
    chunks_text = ""
    for i, c in enumerate(result["chunks"], 1):
        chunks_text += (
            f"[{i}] {c['professor']} | dist={c['distance']}\n"
            f"    {c['text'][:200]}...\n\n"
        )
    return result["answer"], sources_text, chunks_text.strip()


def fill_and_ask(suggestion):
    answer, sources, chunks = handle_query(suggestion)
    return suggestion, answer, sources, chunks


CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Serif+Display&display=swap');

html, body {
    margin: 0 !important;
    padding: 0 !important;
    background: #F5F2EC !important;
}

body,
.gradio-container {
    font-family: 'DM Sans', sans-serif !important;
    background: #F5F2EC !important;
}

/* Main page width */
.gradio-container {
    max-width: 1200px !important;
    width: 95% !important;
    margin: 0 auto !important;
    padding: 40px !important;
    box-shadow: none !important;
}

footer {
    display: none !important;
}

/* Header */
.ug-title {
    font-family: 'DM Serif Display', serif;
    font-size: 42px;
    font-weight: 400;
    color: #111;
    margin-bottom: 8px;
    line-height: 1.1;
}

.ug-title em {
    font-style: normal;
    color: #BF5B2C;
}

.ug-sub {
    font-size: 15px;
    color: #777;
    max-width: 850px;
    margin-bottom: 32px;
    line-height: 1.6;
}

/* Suggestion pills row */
.pills {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 28px;
}

/* Pills */
.pill button,
button.pill {
    background: white !important;
    border: 1px solid #D6D2CB !important;
    border-radius: 999px !important;

    padding: 10px 18px !important;
    min-height: 42px !important;

    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #555 !important;

    cursor: pointer !important;
    box-shadow: none !important;
    transition: all 0.18s ease !important;

    white-space: normal !important;
}

.pill button:hover,
button.pill:hover {
    background: #FDF3EE !important;
    border-color: #BF5B2C !important;
    color: #BF5B2C !important;
    transform: translateY(-1px);
}

/* Textboxes */
.gradio-textbox textarea,
.gradio-textbox input {
    background: white !important;
    border: 1.5px solid #D6D2CB !important;
    border-radius: 14px !important;

    padding: 14px !important;

    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
    color: #111 !important;

    box-shadow: none !important;
    transition: all 0.18s ease !important;
}

.gradio-textbox textarea {
    min-height: 90px !important;
}

.gradio-textbox textarea:focus,
.gradio-textbox input:focus {
    border-color: #BF5B2C !important;
    box-shadow: 0 0 0 4px rgba(191,91,44,0.10) !important;
    outline: none !important;
}

/* Labels */
label {
    font-size: 14px !important;
    font-weight: 600 !important;
}

/* Ask button */
button.primary {
    background: #BF5B2C !important;
    border: none !important;
    border-radius: 12px !important;

    height: 52px !important;
    width: 100% !important;

    font-family: 'DM Sans', sans-serif !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    color: white !important;

    box-shadow: none !important;
    transition: all 0.18s ease !important;
}

button.primary:hover {
    background: #A84D25 !important;
}

/* Outputs */
.gradio-textbox {
    margin-top: 8px !important;
    margin-bottom: 12px !important;
}

/* Accordion */
.accordion {
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* Better spacing between components */
.gr-block,
.gr-form,
.gr-box,
.gr-group {
    gap: 16px !important;
}

/* Remove weird default borders */
.block {
    border: none !important;
}

/* Mobile */
@media (max-width: 768px) {
    .gradio-container {
        width: 100% !important;
        padding: 20px !important;
    }

    .ug-title {
        font-size: 32px;
    }

    .ug-sub {
        font-size: 14px;
    }
}
"""

with gr.Blocks(css=CSS, title="FIU CS Professor Unofficial Guide") as demo:

    gr.HTML("""
    <div>
        <div style="font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#999;margin-bottom:8px;">FIU Computer Science</div>
        <div class="ug-title">The <em>Unofficial</em> Guide</div>
        <div class="ug-sub">Real student reviews, made searchable. Ask anything about FIU CS professors such as exams, grading, teaching style, and more.</div>
    </div>
    """)

    # Suggestion pills
    with gr.Row(elem_classes="pills"):
        pill_btns = [gr.Button(s, elem_classes="pill") for s in SUGGESTIONS]

    # Question input
    question_input = gr.Textbox(
        label="Your question",
        placeholder="e.g. Which CS professor gives the most useful feedback?",
        lines=2,
    )

    ask_btn = gr.Button("Ask →", variant="primary")

    answer_output = gr.Textbox(
        label="Answer",
        lines=8,
        interactive=False,
    )

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

    # Interactions
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
    for btn in pill_btns:
        btn.click(
            fn=fill_and_ask,
            inputs=btn,
            outputs=[question_input, answer_output, sources_output, chunks_output],
        )

if __name__ == "__main__":
    demo.launch()