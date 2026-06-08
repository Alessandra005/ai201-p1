"""
evaluate.py — Run all 5 evaluation questions and print a report.

Run:
    python evaluate.py

Output is printed to console. Copy results into your README.
"""

from query import ask

TEST_QUESTIONS = [
    {
        "question": "Which professor is best for students who struggled in Java 1?",
        "expected": "Mustafa Ocal — multiple reviews mention he helps students who did poorly before",
    },
    {
        "question": "Does Boroojeni allow notes on his exams?",
        "expected": "Yes — students say he allows unlimited paper notes",
    },
    {
        "question": "What do students say about Sadjadi's organization?",
        "expected": "Students say he is disorganized and vague, rarely responds to emails",
    },
    {
        "question": "How is grading structured in Reis's COP4555?",
        "expected": "40% quizzes/discussions, 30% project, 30% exams (mid + final)",
    },
    {
        "question": "Which professors are known for reading off PowerPoint slides?",
        "expected": "Osman, Akbar, and Boujarwah are all mentioned for reading off slides",
    },
]


def evaluate():
    print("=" * 70)
    print("EVALUATION REPORT — FIU CS Professor Unofficial Guide")
    print("=" * 70)

    for i, test in enumerate(TEST_QUESTIONS, 1):
        print(f"\n── Question {i} {'─'*50}")
        print(f"Q: {test['question']}")
        print(f"Expected: {test['expected']}")

        result = ask(test["question"])

        print(f"\nSystem answer:\n{result['answer']}")

        print(f"\nSources retrieved:")
        for s in result["sources"]:
            print(f"  • {s}")

        print(f"\nTop chunks (distances):")
        for c in result["chunks"]:
            print(f"  [{c['distance']}] {c['professor']}: {c['text'][:120]}...")

        print(f"\nAccuracy judgment: [ accurate / partially accurate / inaccurate ]")
        print("  → (fill this in manually after reviewing the answer above)")
        print()

    print("=" * 70)
    print("Done. Copy this output into your README evaluation section.")
    print("=" * 70)


if __name__ == "__main__":
    evaluate()
