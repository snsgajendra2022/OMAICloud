from .research_scheduler import ResearchScheduler
from .evidence_collector import EvidenceCollector
from .research_validator import ResearchValidator
from .knowledge_builder import KnowledgeBuilder



class AutonomousResearchEngine:



    def __init__(self):

        self.scheduler=ResearchScheduler()

        self.collector=EvidenceCollector()

        self.validator=ResearchValidator()

        self.builder=KnowledgeBuilder()



    def research(
        self,
        goal
    ):


        self.scheduler.add(
            goal
        )


        task=self.scheduler.next()


        evidence=self.collector.collect(
            task
        )


        validation=self.validator.validate(
            evidence
        )


        if validation["approved"]:

            return self.builder.build(
                evidence
            )


        return None