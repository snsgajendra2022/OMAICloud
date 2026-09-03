from om_ai.multimodal import MultimodalAgent



agent = MultimodalAgent()



result = agent.process(

    {

        "text":

        "Analyze this restaurant dashboard",


        "image":

        "dashboard.png",


        "audio":

        None

    }

)



print(result)