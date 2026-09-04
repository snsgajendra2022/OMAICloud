import re


class PDFStructureAnalyzer:


    def analyze(self,text):


        sections=[]


        lines=text.split("\n")


        for line in lines:

            line=line.strip()


            if len(line)>0:

                if (
                    line.isupper()
                    or
                    len(line)<80
                ):

                    sections.append(line)



        return {

            "sections":
                sections[:50],

            "word_count":
                len(text.split())

        }