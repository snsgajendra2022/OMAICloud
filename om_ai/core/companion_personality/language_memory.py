"""
User language preference memory.
"""


class LanguageMemory:



    def __init__(self):

        self.store={}



    async def get(
        self,
        user_id
    ):

        return self.store.get(

            user_id,

            {}

        )



    async def update(
        self,
        user_id,
        data
    ):


        current = self.store.get(

            user_id,

            {}

        )


        current.update(data)


        self.store[user_id]=current