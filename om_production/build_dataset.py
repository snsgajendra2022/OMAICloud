"""Generate structured SFT dialogue rows into dataset.txt."""
from __future__ import annotations

import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent

SEED_PAIRS = [
    (
        "What is the core feature of function calling in Python?",
        "The user is asking about function calling. I need to explain the concept clearly, detailing how the LLM generates a structured JSON payload rather than text, which the application's backend code catches and executes.",
        "Function calling allows an AI model to describe tools as JSON schemas and output structured code parameters rather than plain text. Your local application code catches this output, executes the function against your system, and routes the raw calculation back to the AI.",
    ),
    (
        "Write a python loop to compute Fibonacci sequences.",
        "The user requires clean programmatic code. I must output pure, optimized Python text wrapped inside proper syntax containers.",
        "Here is the complete code to compute the sequence:\ndef fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        yield a\n        a, b = b, a + b\nprint(list(fibonacci(10)))",
    ),
    (
        "Hello! Who are you?",
        "Greet briefly and state identity as OM, a local assistant.",
        "Hello! I am OM, your local AI assistant. How can I help you today?",
    ),
    (
        "I feel stuck debugging my code.",
        "Acknowledge emotion, then give calm actionable steps.",
        "That frustration is normal. Take a breath, copy the exact error message, and check the first stack frame that points to your code. Share the error and we can trace it together.",
    ),
    (
        "What is 15% of 200?",
        "Compute carefully: 0.15 * 200 = 30.",
        "15% of 200 is 30.",
    ),
    (
        "Explain gravity in one sentence.",
        "Keep it accurate and short.",
        "Gravity is the attractive force between masses that keeps planets in orbit and objects grounded on Earth.",
    ),
    (
        "How do I train a model on a Mac?",
        "Mention MPS and local checkpoints without external APIs.",
        "Use PyTorch with Apple Metal (MPS), train on local dataset.txt, save checkpoints with torch.save, then load them in chat.py for offline inference.",
    ),
    (
        "What does Pre-LN mean in transformers?",
        "Explain Pre-Layer Normalization clearly.",
        "Pre-LN applies LayerNorm before attention and feed-forward sublayers, which stabilizes deep training compared with Post-LN designs.",
    ),
    (
        "Why use SwiGLU?",
        "Explain gated activation benefit briefly.",
        "SwiGLU uses a gated SiLU pathway in the feed-forward block, which often improves reasoning capacity per parameter versus plain ReLU or GELU MLPs.",
    ),
    (
        "How do I stop the model from repeating words?",
        "Mention repetition penalty and better SFT data.",
        "Apply a repetition penalty during sampling and train on diverse conversational SFT data so the model prefers varied, useful continuations.",
    ),
]


TOPICS = [
    ("recursion", "Recursion is when a function calls itself with a smaller subproblem until a base case stops the chain."),
    ("lists vs tuples", "Lists are mutable sequences; tuples are immutable and often used for fixed records."),
    ("dictionaries", "A dict maps unique keys to values with average O(1) lookup."),
    ("HTTP GET", "GET requests retrieve a resource and should not change server state."),
    ("HTTP POST", "POST requests submit data to create or update a resource."),
    ("JSON", "JSON is a lightweight text format for structured objects and arrays."),
    ("virtualenv", "A virtual environment isolates Python package installs per project."),
    ("git commit", "A commit snapshots staged changes with a message in your repository history."),
    ("unit tests", "Unit tests verify small pieces of code in isolation so regressions are caught early."),
    ("Big-O", "Big-O describes how runtime or memory grows as input size increases."),
    ("hashing", "Hashing maps data to a fixed-size digest for lookups, integrity, and data structures."),
    ("mutex", "A mutex serializes access so only one thread enters a critical section at a time."),
    ("deadlock", "Deadlock happens when processes wait forever for locks the others hold."),
    ("SQL JOIN", "A JOIN combines rows from tables based on a related key column."),
    ("index in SQL", "An index speeds lookups by storing ordered keys pointing to rows."),
    ("REST API", "REST APIs expose resources over HTTP with predictable methods and status codes."),
    ("OAuth", "OAuth lets apps access user data with tokens instead of sharing passwords."),
    ("encryption vs hashing", "Encryption is reversible with a key; hashing is one-way."),
    ("GPU vs CPU", "GPUs excel at parallel math; CPUs handle general control-heavy workloads."),
    ("MPS on Mac", "MPS lets PyTorch run tensor ops on Apple Silicon GPUs without CUDA."),
]


def format_row(user: str, thought: str, final: str) -> str:
    return (
        f"<|user|>{user}<|assistant|><|thought|>{thought}"
        f"<|final_response|>{final}\n\n"
    )


def build_rows(target: int) -> str:
    chunks: list[str] = []
    for user, thought, final in SEED_PAIRS:
        chunks.append(format_row(user, thought, final))

    i = 0
    while len(chunks) < target:
        topic, answer = TOPICS[i % len(TOPICS)]
        n = i + 1
        variants = [
            (
                f"Explain {topic} simply.",
                f"Provide a clear beginner-friendly explanation of {topic}.",
                answer,
            ),
            (
                f"What is {topic}?",
                f"Define {topic} accurately in plain language.",
                answer,
            ),
            (
                f"Give an example related to {topic}.",
                f"Offer a short practical example involving {topic}.",
                f"Example for {topic}: {answer}",
            ),
            (
                f"Why does {topic} matter in software engineering?",
                f"Connect {topic} to real engineering practice.",
                f"{topic.title()} matters because {answer}",
            ),
            (
                f"Summarize {topic} in two sentences for a junior developer.",
                f"Keep the tone mentoring and concise about {topic}.",
                f"{answer} Keep practicing small examples until it feels natural.",
            ),
        ]
        user, thought, final = variants[i % len(variants)]
        # slight diversity salt
        if n % 7 == 0:
            final = final + f" (note #{n})"
        chunks.append(format_row(user, thought, final))
        i += 1
    return "".join(chunks[:target])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=3000, help="Dialogue rows to write")
    ap.add_argument("--out", default=str(HERE / "dataset.txt"))
    args = ap.parse_args()
    text = build_rows(max(50, args.rows))
    Path(args.out).write_text(text, encoding="utf-8")
    print(f"Wrote {args.rows} dialogue rows → {args.out} ({len(text)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
