from __future__ import annotations


class FreshnessDetector:


    SIGNALS = [

        "latest",
        "current",
        "today",
        "recent",
        "new version",
        "release",
        "price",
        "update",
        "news"

    ]


    def detect(
        self,
        message: str
    ):

        text = message.lower()

        matches = [
            word
            for word in self.SIGNALS
            if word in text
        ]


        return {

            "needs_research":
                len(matches) > 0,

            "signals":
                matches

        }