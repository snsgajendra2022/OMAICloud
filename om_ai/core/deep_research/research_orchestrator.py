from .research_router import ResearchRouter
from .research_plan import ResearchPlan
from .research_report_builder import ResearchReportBuilder



class DeepResearchEngine:



    def __init__(
        self,
        search_agent,
        reader,
        extractor
    ):


        self.router=ResearchRouter()

        self.search=search_agent

        self.reader=reader

        self.extractor=extractor

        self.builder=ResearchReportBuilder()



    def research(
        self,
        query
    ):


        decision = (
            self.router.decide(
                query
            )
        )


        if not decision["research_needed"]:


            return {

                "research":
                    False,

                "query":
                    query

            }



        documents = (
            self.search.search(
                query
            )
        )


        extracted=[]


        for doc in documents:


            data=self.reader.read(
                doc
            )


            extracted.append(

                self.extractor.extract(
                    data
                )

            )


        return self.builder.build(

            query,

            extracted

        )