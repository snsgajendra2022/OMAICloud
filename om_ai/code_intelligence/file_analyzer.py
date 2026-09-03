"""
OM File Intelligence Analyzer
"""


from pathlib import Path





class FileAnalyzer:



    def analyze(

        self,

        file_path:str

    ):


        path=Path(file_path)



        try:

            content=path.read_text(

                encoding="utf-8",

                errors="ignore"

            )


        except Exception:


            content=""



        return {


            "file":

                str(path),


            "extension":

                path.suffix,


            "size":

                len(content),


            "lines":

                len(

                    content.splitlines()

                ),


            "content":

                content[:5000]

        }