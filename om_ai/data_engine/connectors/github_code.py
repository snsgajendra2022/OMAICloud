"""
OM Data Engine
Code Dataset Connector
"""

from __future__ import annotations

from pathlib import Path

from typing import Iterator, Dict, Any

from .base import DatasetConnector



class GitHubCodeConnector(DatasetConnector):


    def __init__(
        self,
        directory: str
    ):

        self.directory = Path(directory)



    def stream(self) -> Iterator[Dict[str, Any]]:


        for file in self.directory.rglob("*"):


            if file.is_file():


                try:

                    content = file.read_text(
                        encoding="utf-8",
                        errors="ignore"
                    )


                    if content.strip():

                        yield {

                            "text":
                            content,

                            "source":
                            "github_code",

                            "license":
                            "unknown",

                            "language":
                            file.suffix

                        }


                except Exception:

                    continue



    def metadata(self):

        return {

            "type":
            "code",

            "source":
            "github",

            "language":
            "multiple"

        }