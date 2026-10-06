"""
OM Intelligence Dataset Deduplicator.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any


class DatasetDeduplicator:

    def normalize_for_hash(
        self,
        text: str,
    ) -> str:

        value = (
            text or ""
        ).lower().strip()

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value

    def fingerprint(
        self,
        record: dict[str, Any],
    ) -> str:

        combined = " | ".join(
            [
                self.normalize_for_hash(
                    str(
                        record.get(
                            "input_text",
                            "",
                        )
                    )
                ),
                self.normalize_for_hash(
                    str(
                        record.get(
                            "ideal_response",
                            "",
                        )
                    )
                ),
            ]
        )

        return hashlib.sha256(
            combined.encode(
                "utf-8"
            )
        ).hexdigest()

    def is_duplicate(
        self,
        record: dict[str, Any],
        seen: set[str],
    ) -> bool:

        fingerprint = self.fingerprint(
            record
        )

        if fingerprint in seen:

            return True

        seen.add(
            fingerprint
        )

        return False