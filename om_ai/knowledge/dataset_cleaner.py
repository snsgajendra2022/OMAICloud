"""
OM Dataset Cleaner

Removes low quality knowledge before ingestion.
"""


class DatasetCleaner:


    def validate_record(self, record: dict) -> dict:

        issues = []


        text = str(
            record.get("answer", "")
        ).lower()


        # Remove unrelated era contamination

        bad_patterns = [
            "industrial revolution",
            "steam engines",
            "1800-1900",
        ]


        for item in bad_patterns:

            if item in text:

                issues.append(
                    f"Unrelated historical context: {item}"
                )


        return {
            "valid": len(issues) == 0,
            "issues": issues
        }