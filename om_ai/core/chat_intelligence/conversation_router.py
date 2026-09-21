"""
OM Conversation Router

Decides whether a user message requires:

- normal conversation
- emotional support
- problem solving
- coding/debugging
- research
- action planning

This prevents every message from entering
the Solution Engine.

Flow:

User Message
      |
      v
Conversation Router
      |
      +---- Human Conversation
      |
      +---- Problem Solving
      |
      +---- Research
      |
      +---- Action
"""

from __future__ import annotations

import re

from typing import Any


class ConversationRouter:
    """
    Intelligent routing layer before OM brain.

    Avoids robotic behavior by understanding
    user intention first.
    """

    CONVERSATION = "conversation"

    PROBLEM_SOLVING = "problem_solving"

    CODING = "coding"

    RESEARCH = "research"

    EMOTIONAL = "emotional"

    ACTION = "action"


    def route(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        analysis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:


        context = context or {}

        analysis = analysis or {}


        text = (
            message or ""
        ).strip().lower()


        if not text:

            return self._result(
                self.CONVERSATION,
                "empty_message"
            )


        # ---------------------------------------
        # Greeting / capability conversation
        # ---------------------------------------

        if self._is_social(text):

            return self._result(
                self.CONVERSATION,
                "social_message"
            )


        # ---------------------------------------
        # User asking about OM ability
        # ---------------------------------------

        if self._is_capability_question(text):

            return self._result(
                self.CONVERSATION,
                "capability_question"
            )


        # ---------------------------------------
        # Emotion / feelings
        # ---------------------------------------

        if self._is_emotional(text):

            return self._result(
                self.EMOTIONAL,
                "emotion_detected"
            )


        # ---------------------------------------
        # Coding
        # ---------------------------------------

        if self._is_coding(text):

            return self._result(
                self.CODING,
                "coding_request"
            )


        # ---------------------------------------
        # Research
        # ---------------------------------------

        if self._is_research(text):

            return self._result(
                self.RESEARCH,
                "research_request"
            )


        # ---------------------------------------
        # Actions
        # ---------------------------------------

        if self._is_action(text):

            return self._result(
                self.ACTION,
                "action_request"
            )


        # ---------------------------------------
        # Default problem solving
        # ---------------------------------------

        return self._result(
            self.PROBLEM_SOLVING,
            "requires_solution"
        )



    def _result(
        self,
        route: str,
        reason: str
    ) -> dict[str, Any]:


        return {

            "route": route,

            "reason": reason,

            "use_solution_engine":
                route in [
                    self.PROBLEM_SOLVING,
                    self.CODING
                ],

            "use_conversation_engine":
                route in [
                    self.CONVERSATION,
                    self.EMOTIONAL
                ],

            "confidence": 0.85

        }



    def _is_social(
        self,
        text: str
    ) -> bool:


        return bool(
            re.search(
                r"^(hi|hello|hey|good morning|good evening|namaste|hola)\b",
                text
            )
        )



    def _is_capability_question(
        self,
        text: str
    ) -> bool:


        patterns = [

            r"can you help",

            r"can you solve",

            r"what can you do",

            r"are you able",

            r"who are you",

            r"what are you"

        ]


        return any(
            re.search(
                p,
                text
            )
            for p in patterns
        )



    def _is_emotional(
        self,
        text: str
    ) -> bool:


        words = [

            "tired",
            "sad",
            "angry",
            "frustrated",
            "stressed",
            "worried",
            "lonely",
            "exhausted",
            "happy",
            "excited"

        ]


        return any(
            word in text
            for word in words
        )



    def _is_coding(
        self,
        text: str
    ) -> bool:


        patterns = [

            "code",
            "python",
            "javascript",
            "react",
            "api",
            "bug",
            "error",
            "exception",
            "database",
            "server",
            "function"

        ]


        return any(
            p in text
            for p in patterns
        )



    def _is_research(
        self,
        text: str
    ) -> bool:


        patterns = [

            "explain",
            "research",
            "compare",
            "difference",
            "why",
            "how does"

        ]


        return any(
            p in text
            for p in patterns
        )



    def _is_action(
        self,
        text: str
    ) -> bool:


        patterns = [

            "open",
            "create",
            "send",
            "run",
            "execute",
            "start",
            "stop"

        ]


        return any(
            text.startswith(p)
            for p in patterns
        )