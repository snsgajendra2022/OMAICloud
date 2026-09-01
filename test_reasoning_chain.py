from om_ai.core.reasoning.reasoning_chain import ReasoningChain


engine = ReasoningChain()


result = engine.analyze(

    "create react native login and dashboard app",

    intent={
        "domain":"programming",
        "task":"development"
    },

    technology={

        "technology":"react native",

        "category":"mobile",

        "platform":"android_ios"

    },

    tasks={

        "tasks":[

            "Create Login Screen",

            "Create Dashboard Screen",

            "Setup Navigation",

            "Implement Authentication",

            "Testing"

        ]

    }

)


print(result)