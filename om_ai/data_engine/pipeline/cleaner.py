"""
OM Data Engine
Text Cleaning Pipeline
"""

from __future__ import annotations

import re
import unicodedata



class TextCleaner:


    def clean(
        self,
        text: str
    ) -> str:


        if not text:
            return ""


        # Unicode normalization

        text = unicodedata.normalize(
            "NFKC",
            text
        )


        # Remove null chars

        text = text.replace(
            "\x00",
            " "
        )


        # Remove HTML

        text = re.sub(
            r"<[^>]+>",
            " ",
            text
        )


        # Remove URLs

        text = re.sub(
            r"https?://\S+",
            " ",
            text
        )


        # Normalize spaces

        text = re.sub(
            r"[ \t]+",
            " ",
            text
        )


        # Normalize lines

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text
        )


        return text.strip()



    def valid(
        self,
        text: str,
        minimum_length: int = 20
    ) -> bool:


        if not text:
            return False


        return len(text.strip()) >= minimum_length