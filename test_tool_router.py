from om_ai.tools import ToolRouter



router = ToolRouter()



for q in [

    "read this file",

    "debug python error",

    "analyze excel report"

]:


    result = router.route(q)


    print(
        q
    )


    print(
        result["name"],
        result["score"]
    )