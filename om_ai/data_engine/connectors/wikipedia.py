"""
OM Data Engine
Wikipedia Connector
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, Dict, Any

from .base import DatasetConnector



class WikipediaConnector(DatasetConnector):


    def __init__(
        self,
        file_path: str
    ):

        self.file_path = Path(file_path)



    def stream(self) -> Iterator[Dict[str, Any]]:


        if not self.file_path.exists():

            raise FileNotFoundError(
                self.file_path
            )


        with self.file_path.open(
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as file:


            for line in file:


                text = line.strip()


                if text:

                    yield {

                        "text": text,

                        "source":
                        "wikipedia",

                        "license":
                        "CC BY-SA"

                    }



    def metadata(self):

        return {

            "type":
            "encyclopedia",

            "source":
            "wikipedia",

            "license":
            "CC BY-SA"

        }