"""
OM Data Engine
HuggingFace Dataset Connector
"""

from __future__ import annotations

from typing import Iterator, Dict, Any

from .base import DatasetConnector



class HuggingFaceConnector(DatasetConnector):


    def __init__(
        self,
        dataset_name: str,
        split: str = "train",
        text_field: str = "text"
    ):

        self.dataset_name = dataset_name
        self.split = split
        self.text_field = text_field



    def stream(self) -> Iterator[Dict[str, Any]]:

        try:

            from datasets import load_dataset


            dataset = load_dataset(
                self.dataset_name,
                split=self.split,
                streaming=True
            )


            for item in dataset:

                text = item.get(
                    self.text_field
                )


                if text:

                    yield {

                        "text": str(text),

                        "source":
                        self.dataset_name,

                        "license":
                        "unknown"

                    }


        except ImportError:

            raise RuntimeError(
                "Install datasets package: pip install datasets"
            )



    def metadata(self):

        return {

            "type":
            "huggingface",

            "dataset":
            self.dataset_name,

            "split":
            self.split

        }