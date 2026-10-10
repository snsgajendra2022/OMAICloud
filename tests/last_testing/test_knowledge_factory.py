from om_ai.data_engine import OMKnowledgeFactory


class DemoConnector:


    def stream(self):

        yield {

            "text":
            "Git is a distributed version control system used in software development.",

            "source":
            "demo",

            "license":
            "open"

        }


        yield {

            "text":
            "React is a JavaScript library for building user interfaces.",

            "source":
            "demo",

            "license":
            "MIT"

        }



factory = OMKnowledgeFactory(
    output="data/om-knowledge-v1/demo.jsonl"
)


result = factory.build(
    DemoConnector()
)


print(result)