"""
OM Programming Language Detector
"""





class LanguageDetector:



    def detect(

        self,

        extension:str

    ):



        languages={


            ".py":

                "python",


            ".php":

                "php",


            ".js":

                "javascript",


            ".ts":

                "typescript",


            ".java":

                "java",


            ".cs":

                "csharp",


            ".go":

                "golang"

        }



        return languages.get(

            extension,

            "unknown"

        )