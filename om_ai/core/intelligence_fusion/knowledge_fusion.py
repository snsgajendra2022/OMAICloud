class KnowledgeFusion:



    def merge(
        self,
        knowledge_items:list[dict]
    ):


        result={}


        for item in knowledge_items:


            for key,value in item.items():

                if key not in result:

                    result[key]=value



        return result