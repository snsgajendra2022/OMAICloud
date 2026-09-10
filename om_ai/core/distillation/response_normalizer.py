from __future__ import annotations

import re


class ResponseNormalizer:
    """
    Cleans teacher outputs.

    Does NOT remove useful code blocks.
    Removes only obvious noise.
    """


    def normalize(
        self,
        text: str
    ) -> str:


        if not text:
            return ""


        text = str(text)


        # remove invalid control characters

        text = "".join(
            ch
            for ch in text
            if ch.isprintable()
            or ch in "\n\t"
        )


        # remove obvious tool leakage

        leakage_patterns = [

            r"\[tool:.*?\]",

            r"tool_execution",

            r"code_execution",

            r"internal tool",

        ]


        for pattern in leakage_patterns:

            text = re.sub(
                pattern,
                "",
                text,
                flags=re.I
            )


        # remove repeated headers

        text = re.sub(

            r"^(answer:|response:|output:)\s*",

            "",

            text,

            flags=re.I

        )


        # remove empty markdown wrapper

        if (
            text.startswith("```")
            and
            text.endswith("```")
        ):

            text = text[3:-3]


        return text.strip()