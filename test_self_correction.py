from om_ai.autonomy.evaluation import SelfCorrectionLoop



loop = SelfCorrectionLoop()



tests=[

    "Complete solution with architecture and implementation details",

    ""

]



for item in tests:


    result = loop.review(
        item
    )


    print("----------------")

    print(result)