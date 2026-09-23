"""
OM Speech Meaning Intelligence Engine

Purpose:

Convert raw speech/text into human meaning.

Not a response generator.

Input:

"are what are you doing"

Output:

{
    corrected_meaning:
        "what are you doing",

    intent:
        "casual_conversation",

    goal:
        "social_interaction",

    confidence:
        0.94
}

"""

from __future__ import annotations

from typing import Any
import re


class SpeechMeaningEngine:


    def __init__(
        self,
        semantic_engine=None,
        context_engine=None,
        emotion_engine=None
    ):

        self.semantic_engine = semantic_engine

        self.context_engine = context_engine

        self.emotion_engine = emotion_engine



    def analyze(
        self,
        text: str,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:


        context = context or {}

        raw = (
            text or ""
        ).strip()


        if not raw:

            return {

                "raw_text": "",

                "meaning": "",

                "intent": "unknown",

                "goal": "unknown",

                "confidence": 0.0

            }



        # Step 1
        # normalize speech errors

        meaning = self.normalize_meaning(
            raw,
            context
        )



        # Step 2
        # semantic understanding

        semantic = self.semantic_analysis(
            meaning,
            context
        )



        # Step 3
        # emotion

        emotion = self.detect_emotion(
            meaning,
            context
        )


        return {


            "raw_text":
                raw,


            "meaning":
                meaning,


            "intent":
                semantic["intent"],


            "goal":
                semantic["goal"],


            "conversation_type":
                semantic["conversation_type"],


            "needs_action":
                semantic["needs_action"],


            "emotion":
                emotion,


            "confidence":
                semantic["confidence"]

        }



    def normalize_meaning(
        self,
        text: str,
        context: dict[str, Any]
    ) -> str:


        value = (
            text.lower()
            .strip()
        )


        # speech recognition cleanup

        corrections = {

            "are what are you doing":
                "what are you doing",

            "what you doing":
                "what are you doing",

            "wat are you doing":
                "what are you doing",

            "how r u":
                "how are you",

            "i am fine":
                "i am fine"

        }


        if value in corrections:

            return corrections[value]



        # remove repeated words

        value = re.sub(
            r"\b(\w+)\s+\1\b",
            r"\1",
            value
        )


        return value



    def semantic_analysis(
        self,
        message: str,
        context: dict[str, Any]
    ) -> dict[str, Any]:


        if self.semantic_engine:


            result = self.semantic_engine.analyze(
                message,
                context=context
            )


            return {

                "intent":
                    result.intent,


                "goal":
                    result.goal,


                "conversation_type":
                    result.type,


                "needs_action":
                    result.needs_action,


                "confidence":
                    result.confidence

            }



        return self.basic_semantic_reasoning(
            message,
            context
        )



    def basic_semantic_reasoning(
        self,
        message: str,
        context: dict[str, Any]
    ):


        text = message.lower()



        # social conversation

        if any(
            x in text
            for x in [

                "what are you doing",

                "how are you",

                "what's up",

                "hello",

                "hi"

            ]
        ):

            return {

                "intent":
                    "conversation",

                "goal":
                    "social_interaction",

                "conversation_type":
                    "casual",

                "needs_action":
                    False,

                "confidence":
                    0.90

            }



        # question

        if "?" in message:

            return {

                "intent":
                    "information_request",

                "goal":
                    "get_answer",

                "conversation_type":
                    "question",

                "needs_action":
                    False,

                "confidence":
                    0.75

            }



        # action

        if any(
            x in text
            for x in [

                "open",

                "create",

                "send",

                "run",

                "start"

            ]
        ):

            return {

                "intent":
                    "action_request",

                "goal":
                    "execute_action",

                "conversation_type":
                    "command",

                "needs_action":
                    True,

                "confidence":
                    0.80

            }



        return {

            "intent":
                "general",

            "goal":
                "understand_user",

            "conversation_type":
                "unknown",

            "needs_action":
                False,

            "confidence":
                0.50

        }



    def detect_emotion(
        self,
        message: str,
        context: dict[str, Any]
    ):


        if self.emotion_engine:

            return self.emotion_engine.detect(
                message,
                context=context
            )


        text = message.lower()


        if any(
            x in text
            for x in [
                "tired",
                "sad",
                "frustrated",
                "angry",
                "stress"
            ]
        ):

            return "negative"



        return "neutral"