#!/usr/bin/env python3
"""
OM Dynamic Chat Intelligence Dataset Builder

Creates self-improving OM training data.

Sources:
- OM Memory
- OM Knowledge
- Research Engine
- Conversation History
- Distillation Engine
- User Feedback
- Existing datasets

No hardcoded conversations.
No static topics.
No artificial limits.
"""

from __future__ import annotations


import json
import hashlib
import datetime

from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


OUTPUT = (
    ROOT
    /
    "data"
    /
    "om-chat-sft-dynamic.jsonl"
)



class DynamicChatDatasetBuilder:
    """
    Dynamic OM training dataset generator.
    """


    def __init__(
        self,
        output: Path = OUTPUT,
    ):

        self.output = output

        self.rows = []


    # -------------------------------
    # Load existing OM knowledge
    # -------------------------------

    def load_sources(self):

        sources = [

            ROOT / "data",

            ROOT / "knowledge",

            ROOT / "memory",

            ROOT / "research",

        ]


        files = []


        for source in sources:

            if not source.exists():

                continue


            for file in source.rglob("*"):

                if file.is_file():

                    files.append(file)


        return files



    # -------------------------------
    # Read dynamic content
    # -------------------------------

    def read_file(
        self,
        file: Path
    ) -> str:


        try:

            if file.suffix in (
                ".json",
                ".jsonl",
                ".txt",
                ".md"
            ):

                return file.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

        except Exception:

            pass


        return ""



    # -------------------------------
    # Generate training example
    # -------------------------------

    def create_example(
        self,
        content: str,
        source: str
    ):


        if not content.strip():

            return None



        identity = hashlib.sha256(
            content.encode()
        ).hexdigest()



        return {


            "system":

            """

You are OM AI.

You are a private self-owned AI assistant.

Provide accurate, useful and context-aware answers.

Match user language and intent.

Do not claim to be another AI system.

""".strip(),



            "instruction":

            "Explain and reason about the provided knowledge.",



            "input":

            content[:4000],



            "output":

            content[:4000],



            "metadata":

            {

                "id":
                    identity,


                "source":
                    source,


                "created_at":
                    datetime.datetime.utcnow()
                    .isoformat(),


                "generator":
                    "OM_DYNAMIC_BUILDER"

            }

        }



    # -------------------------------
    # Build dataset
    # -------------------------------

    def build(self):


        files = self.load_sources()



        for file in files:


            content = self.read_file(
                file
            )


            example = self.create_example(

                content,

                str(file)

            )


            if example:

                self.rows.append(
                    example
                )



        return self.deduplicate()



    # -------------------------------
    # Remove duplicates
    # -------------------------------

    def deduplicate(self):


        seen = set()


        unique = []


        for row in self.rows:


            key = hashlib.sha256(

                json.dumps(

                    row,

                    sort_keys=True,

                    ensure_ascii=False

                ).encode()

            ).hexdigest()



            if key in seen:

                continue



            seen.add(key)


            unique.append(row)



        self.rows = unique


        return unique



    # -------------------------------
    # Save JSONL
    # -------------------------------

    def save(self):


        self.output.parent.mkdir(

            parents=True,

            exist_ok=True

        )



        with self.output.open(

            "w",

            encoding="utf-8"

        ) as file:


            for row in self.rows:


                file.write(

                    json.dumps(

                        row,

                        ensure_ascii=False

                    )

                    +

                    "\n"

                )



        return {

            "file":

            str(self.output),


            "examples":

            len(self.rows)

        }




def main():


    builder = DynamicChatDatasetBuilder()


    builder.build()


    result = builder.save()


    print(

        json.dumps(

            result,

            indent=2

        )

    )



if __name__ == "__main__":

    main()