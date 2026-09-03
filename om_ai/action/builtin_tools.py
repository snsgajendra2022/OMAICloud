"""
OM Built-in Autonomous Tools
"""


from pathlib import Path

from .tool import Tool





def write_file(

    path:str,

    content:str

):


    file=Path(path)


    file.parent.mkdir(

        parents=True,

        exist_ok=True

    )


    file.write_text(

        content,

        encoding="utf-8"

    )


    return {

        "file":

            str(file)

    }





def list_files(

    path:str="."

):


    return [

        str(x)

        for x in Path(path).rglob("*")

        if x.is_file()

    ]





def register_builtin_tools(

    executor

):


    executor.register_tool(

        Tool(

            name="file_writer",

            description="Create files",

            function=write_file

        )

    )



    executor.register_tool(

        Tool(

            name="file_list",

            description="List files",

            function=list_files

        )

    )