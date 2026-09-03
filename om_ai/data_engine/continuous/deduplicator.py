"""
OM Dataset Deduplicator
"""


import hashlib




class DatasetDeduplicator:



    def remove(
        self,
        items:list[dict]
    ):


        seen=set()

        output=[]


        for item in items:


            text=(

                item.get("instruction","")

                +

                item.get("response","")

            )


            key=hashlib.md5(

                text.encode()

            ).hexdigest()



            if key not in seen:


                seen.add(key)

                output.append(item)



        return output