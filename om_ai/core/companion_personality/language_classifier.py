"""
AI based language classifier.

Uses OM intelligence model.
"""

from __future__ import annotations


class LanguageClassifier:



    def __init__(
        self,
        model=None
    ):

        self.model=model



    async def predict(
        self,
        *,
        text:str,
        context:dict
    ):


        if not self.model:

            return {

                "language":
                "auto",

                "confidence":
                0

            }



        result = await self.model.classify(

            task="language_detection",

            input={

                "text":text,

                "context":context

            }

        )


        return result