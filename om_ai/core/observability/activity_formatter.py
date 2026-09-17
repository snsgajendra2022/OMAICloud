from .event_types import ActivityType



class ActivityFormatter:


    def format(
        self,
        event
    ):


        mapping={


        ActivityType.SEARCH:
        "🔎 Searching information",


        ActivityType.FILE_OPERATION:
        "📄 Processing files",


        ActivityType.KNOWLEDGE_LOOKUP:
        "📚 Checking knowledge",


        ActivityType.MODEL_CALL:
        "🤖 Running intelligence model",


        ActivityType.RESPONSE:
        "✍️ Preparing response"


        }


        return mapping.get(

            event.event_type,

            event.message

        )