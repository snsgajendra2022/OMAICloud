"""
OM Repository Intelligence Engine
"""


from .scanner import RepositoryScanner

from .file_analyzer import FileAnalyzer

from .language import LanguageDetector

from .dependency import DependencyAnalyzer

from .architecture import ArchitectureAnalyzer

from .index import CodeIndex





class CodeUnderstandingEngine:



    def __init__(self):


        self.scanner=RepositoryScanner()

        self.files=FileAnalyzer()

        self.language=LanguageDetector()

        self.dependencies=DependencyAnalyzer()

        self.architecture=ArchitectureAnalyzer()

        self.index=CodeIndex()




    def analyze(

        self,

        repository:str

    ):


        files=self.scanner.scan(

            repository

        )


        analyzed=[]



        for file in files:


            info=self.files.analyze(

                file

            )


            info["language"]=self.language.detect(

                info["extension"]

            )


            info["dependencies"]=self.dependencies.analyze(

                info["content"]

            )


            analyzed.append(

                info

            )



        result={


            "repository":

                repository,


            "files":

                analyzed,


            "architecture":

                self.architecture.analyze(

                    files

                )

        }



        self.index.save(

            result

        )



        return result