from om_ai.core.response import ResponseEngine


engine = ResponseEngine()


tests=[

(
"hello OM",
"Hello, I am OM. How can I help?"
),


(
"create react dashboard",
"Here is a React dashboard architecture..."
),


(
"what is react",
"React is a JavaScript library..."
),


(
"random",
"ressive wastinta originals HinesCLICK Dixon"
)

]


for q,a in tests:

    print("================")

    print(q)


    print(
        engine.critic_check(
            q,
            a
        )
    )