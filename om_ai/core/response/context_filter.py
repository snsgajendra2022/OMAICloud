from __future__ import annotations


class ContextFilter:


    BLOCKED = [

        "tool:",
        "traceback",
        "README.md",
        "package.json",
        "file structure",
        "internal path",
    ]


    def clean(
        self,
        data
    ):


        if not data:
            return []


        if isinstance(data,dict):

            data=[
                data
            ]


        cleaned=[]


        for item in data:


            text=str(item)


            blocked=False


            for word in self.BLOCKED:

                if word.lower() in text.lower():

                    blocked=True
                    break


            if not blocked:

                cleaned.append(item)


        return cleaned