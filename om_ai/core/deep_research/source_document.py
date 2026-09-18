from dataclasses import dataclass



@dataclass
class SourceDocument:


    title:str


    url:str


    content:str


    source_type:str="web"