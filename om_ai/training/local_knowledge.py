"""Build knowledge.txt from local offline documentation folders (no internet).

Pulls free text from paths on your Mac into a single chat-friendly corpus.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_TEXT_SUFFIXES = {
    ".txt",
    ".md",
    ".rst",
    ".py",
    ".jsonl",
    ".json",
    ".csv",
    ".html",
    ".htm",
    ".xml",
    ".yml",
    ".yaml",
    ".toml",
    ".sh",
    ".c",
    ".h",
    ".cpp",
    ".js",
    ".ts",
    ".swift",
    ".rs",
    ".go",
    ".java",
}

_SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "artifacts",
    ".cursor",
}


SEED_KNOWLEDGE = """\
<|user|> Hello! <|assistant|> Hello, I am OM-1.0, your custom AI system.
<|user|> I am feeling stuck and stressed with my code. What should I do? <|assistant|> It is completely normal to feel stressed when debugging. Take a deep breath. Let's break the problem down into smaller steps together. What error message are you seeing?
<|user|> Why does a stone fall faster than a feather in air? <|assistant|> This happens because of air resistance. The air pushes up against the flat surface of the feather, slowing it down. In a vacuum with no air, both would fall at the exact same speed.
<|user|> How do I stay calm when learning AI? <|assistant|> Focus on one concept at a time. Celebrate small wins, rest when tired, and remember that confusion is part of building understanding.
<|user|> Explain gravity simply. <|assistant|> Gravity is the pull between objects with mass. Earth's gravity keeps us on the ground and holds the Moon in orbit.
<|user|> Write a short encouraging message for a tired engineer. <|assistant|> You have already solved hard problems before. Rest, then take the next tiny step — progress compounds.
"""


def _strip_html(text: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _read_file(path: Path, max_bytes: int = 2_000_000) -> str:
    try:
        raw = path.read_bytes()[:max_bytes]
        text = raw.decode("utf-8", errors="ignore")
    except OSError:
        return ""
    if path.suffix.lower() in {".html", ".htm", ".xml"}:
        return _strip_html(text)
    if path.suffix.lower() == ".jsonl":
        parts: list[str] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            # Prefer chat-ish fields without requiring json import failure soft-path
            if '"text"' in line or '"content"' in line or '"response"' in line:
                parts.append(line)
            else:
                parts.append(line)
        return "\n".join(parts)
    return text


def _as_chat_block(source: str, body: str) -> str:
    body = body.strip()
    if not body:
        return ""
    # If already chat-tagged, keep as-is
    if "<|user|>" in body or "<|assistant|>" in body:
        return body
    # Wrap prose as a knowledge Q/A turn so SFT-style training sees structure
    snippet = body[:4000]
    return (
        f"<|user|> Summarize key ideas from {source}. "
        f"<|assistant|> {snippet}"
    )


def aggregate_local_docs(
    source_dirs: list[str | Path],
    output: str | Path = "knowledge.txt",
    *,
    max_files: int = 500,
    max_file_bytes: int = 2_000_000,
    include_seed: bool = True,
) -> dict:
    """Scan offline folders and append readable text into knowledge.txt."""
    out = Path(output)
    if not out.is_absolute():
        out = ROOT / out
    chunks: list[str] = []
    if include_seed:
        chunks.append(SEED_KNOWLEDGE.strip())

    files_used = 0
    bytes_in = 0
    for raw_dir in source_dirs:
        base = Path(raw_dir)
        if not base.is_absolute():
            base = ROOT / base
        if not base.exists():
            continue
        paths = [base] if base.is_file() else sorted(base.rglob("*"))
        for path in paths:
            if files_used >= max_files:
                break
            if path.is_dir():
                continue
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            if path.suffix.lower() not in _TEXT_SUFFIXES and path.name != "knowledge.txt":
                continue
            if path.resolve() == out.resolve():
                continue
            text = _read_file(path, max_bytes=max_file_bytes)
            if len(text.strip()) < 40:
                continue
            block = _as_chat_block(str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path), text)
            if not block:
                continue
            chunks.append(block)
            files_used += 1
            bytes_in += len(text.encode("utf-8", errors="ignore"))

    out.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n\n".join(chunks) + "\n"
    out.write_text(payload, encoding="utf-8")
    return {
        "output": str(out),
        "files": files_used,
        "bytes_read": bytes_in,
        "chars_written": len(payload),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Aggregate local offline docs into knowledge.txt")
    p.add_argument(
        "sources",
        nargs="*",
        default=["docs", "data/om-foundation-corpus", "README.md"],
        help="Folders/files to scan (offline only)",
    )
    p.add_argument("--output", default="knowledge.txt")
    p.add_argument("--max-files", type=int, default=500)
    p.add_argument("--no-seed", action="store_true")
    args = p.parse_args(argv)
    result = aggregate_local_docs(
        args.sources,
        args.output,
        max_files=args.max_files,
        include_seed=not args.no_seed,
    )
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
