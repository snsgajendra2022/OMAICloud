from .semantic_parser import SemanticParser
from .entity_extractor import EntityExtractor
from .context_analyzer import ContextAnalyzer
from .confidence_engine import ConfidenceEngine
from .intent_state import IntentState



class IntentEngine:


    def __init__(self):

        self.parser = SemanticParser()

        self.entities = EntityExtractor()

        self.context = ContextAnalyzer()

        self.confidence = ConfidenceEngine()



    def analyze(
        self,
        text,
        previous_context=None
    ):


        semantic = self.parser.parse(
            text
        )


        entities = self.entities.extract(
            text
        )


        context = self.context.analyze(
            semantic,
            previous_context
        )


        intent = self.detect_intent(
            text,
            context
        )


        confidence = self.confidence.calculate(
            intent,
            entities
        )


        return IntentState(

            intent=intent,

            confidence=confidence,

            entities=entities,

            requires_tool=
                self.requires_tool(intent),

            tool_name=
                self.tool(intent),

            context=context

        )



    def detect_intent(
        self,
        text,
        context
    ):


        text=text.lower()


        # Real date request

        if (
            "what is today's date" in text
            or
            "current date" in text
            or
            "what date is today" in text
        ):

            return "date_query"



        # Greeting conversation

        if context["conversation_type"]=="conversation":

            return "casual_conversation"



        if "create" in text:

            return "creation"



        return "general"



    def requires_tool(
        self,
        intent
    ):

        return intent=="date_query"



    def tool(
        self,
        intent
    ):

        if intent=="date_query":

            return "date"


        return None