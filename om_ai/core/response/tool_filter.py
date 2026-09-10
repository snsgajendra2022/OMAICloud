"""Strip / block tool-trace leakage from public answers."""
from __future__ import annotations

import re


class ToolOutputFilter:
    """Prevent internal tool traces from reaching the user."""

    BLOCKED_PHRASES = [
        "[tool:",
        "[tool]",
        "[tool:knowledge]",
        "code_execution",
        "terminal output",
        "tool call:",
        "tool_call",
        "function_call",
        "invoking tool",
        "running tool",
        "action_input",
        "observation:",
        "<|tool|>",
        "</tool>",
        "om_tool_trace",
        "belongs in the om genesis knowledge map",
        "variant focus:",
        "**research notes:**",
    ]

    _TOOL_BLOCK = re.compile(
        r"(?is)(?:```(?:tool|bash|shell|json)?\s*\n)?"
        r"(?:\[tool[^\]]*\]|Tool\s*Call|Function\s*Call|"
        r"Action\s*:|Observation\s*:|Action\s*Input\s*:).{0,800}"
        r"(?:```)?"
    )

    def clean(self, text: str) -> str:
        """Return cleaned text, or empty string if the whole reply is tool leakage."""
        if not text:
            return ""

        cleaned = text
        # Remove contiguous tool-trace blocks first
        cleaned = self._TOOL_BLOCK.sub("", cleaned).strip()

        lower = cleaned.lower()
        for item in self.BLOCKED_PHRASES:
            if item.lower() in lower:
                # If phrase remains after block strip, treat as unsafe
                return ""

        # Collapse leftover blank lines
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        return cleaned

    def is_leaked(self, text: str) -> bool:
        """True when text is empty after cleaning or clearly tool leakage."""
        if not text:
            return False
        cleaned = self.clean(text)
        if not cleaned:
            return True
        return cleaned != text.strip() and len(cleaned) < max(20, int(len(text) * 0.35))


# Back-compat alias used in some notes / docs
ToolFilter = ToolOutputFilter
