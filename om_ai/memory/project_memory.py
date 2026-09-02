"""
OM Project Memory

Stores project state and development context.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ProjectMemory:


    def __init__(
        self,
        path="storage/project_memory.json"
    ):

        self.path = Path(path)

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.data = self.load()
        self.memory.get_context()

    def load(self):

        if self.path.exists():

            return json.loads(
                self.path.read_text()
            )

        return {
            "projects": {}
        }



    def save(self):

        self.path.write_text(
            json.dumps(
                self.data,
                indent=2
            )
        )



    def create_project(
        self,
        name:str
    ):

        self.data["projects"][name] = {

            "completed":[],
            "current":"",
            "next":[]

        }

        self.save()



    def update(
        self,
        project:str,
        key:str,
        value:Any
    ):

        if project not in self.data["projects"]:

            self.create_project(project)


        self.data["projects"][project][key]=value

        self.save()



    def get(
        self,
        project:str
    ):
        return self.data["projects"].get(
            project,
            {}
        )
    def get_project_context(self):
        return self.project.data