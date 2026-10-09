from om_ai.data_engine.pipeline import DatasetBuilder


data = [

    {
        "text":
        "Git is a distributed version control system used by developers.",

        "source":
        "wikipedia",

        "license":
        "CC BY-SA"
    },


    {
        "text":
        "React is a JavaScript library for building user interfaces.",

        "source":
        "documentation",

        "license":
        "MIT"
    }

]


builder = DatasetBuilder()


result = builder.build_to_file(
    iter(data),
    "data/om-knowledge-v1/train.jsonl"
)


print(result)