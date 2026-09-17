from .activity_event import ActivityEvent
from .activity_types import ActivityType



class ActivityGenerator:


    def searching(
        self,
        source,
        count=None
    ):


        return ActivityEvent(

            type=ActivityType.SEARCHING,

            title=f"Searching {source}",

            metadata={

                "results":
                    count

            }

        )



    def reading_files(
        self,
        count:int
    ):


        return ActivityEvent(

            type=ActivityType.READING,

            title="Reading files",

            description=
            f"Checked {count} files",

            metadata={

                "files":
                    count

            }

        )



    def knowledge_lookup(
        self,
        nodes:int
    ):


        return ActivityEvent(

            type=ActivityType.KNOWLEDGE,

            title="Checking OM Knowledge Brain",

            metadata={

                "nodes":
                    nodes

            }

        )



    def research_started(
        self,
        query:str
    ):


        return ActivityEvent(

            type=ActivityType.RESEARCH,

            title="Research started",

            metadata={

                "query":
                    query

            }

        )



    def response_ready(self):


        return ActivityEvent(

            type=ActivityType.RESPONSE,

            title="Response generated"

        )