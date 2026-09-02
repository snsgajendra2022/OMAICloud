"""
OM Knowledge Document Store

Stores large scale knowledge documents.

Designed for:
- RAG
- Training datasets
- Research corpus
- Code knowledge
"""


from pathlib import Path
import json
from datetime import datetime
from typing import Any


class DocumentStore:


    def __init__(
        self,
        base_path="storage/knowledge/documents"
    ):

        self.base = Path(base_path)

        self.base.mkdir(
            parents=True,
            exist_ok=True
        )



    def save_document(
        self,
        document_id:str,
        text:str,
        metadata:dict[str,Any] | None=None
    ):


        data={

            "id":document_id,

            "text":text,

            "metadata":metadata or {},

            "created":
            datetime.utcnow().isoformat()

        }


        file=self.base / f"{document_id}.json"


        file.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False
            )
        )


        return str(file)



    def load_document(
        self,
        document_id:str
    ):


        file=self.base / f"{document_id}.json"


        if not file.exists():

            return None


        return json.loads(
            file.read_text()
        )



    def list_documents(self):


        return [

            x.stem

            for x in self.base.glob(
                "*.json"
            )

        ]