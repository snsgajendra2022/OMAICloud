from __future__ import annotations


class ImprovementEngine:

    def build_retry_instruction(
        self,
        *,
        issues: list[str],
        original_message: str,
    ) -> str:

        issue_text = ", ".join(
            issues
        ) or "low quality response"

        return f"""
The previous draft failed quality validation.

Original user request:
{original_message}

Detected problems:
{issue_text}

Generate a new answer from the original request.

Requirements:
- Read the complete user request.
- Answer the actual request.
- Use coherent natural language.
- Do not output random token sequences.
- Do not dump unrelated memory, README content, or tool output.
- If code was requested, provide usable implementation.
- Do not repeat the failed draft.
""".strip()