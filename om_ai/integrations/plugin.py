from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Any

@dataclass(slots=True)
class ActionSpec:
    name:str
    description:str
    input_schema:dict
    write:bool=False

class IntegrationPlugin(ABC):
    @abstractmethod
    def health(self)->dict: ...
    @abstractmethod
    def actions(self)->list[ActionSpec]: ...
    @abstractmethod
    def execute(self,action:str,arguments:dict)->Any: ...

class PluginRegistry:
    def __init__(self): self._plugins={}
    def register(self,name:str,plugin:IntegrationPlugin): self._plugins[name]=plugin
    def get(self,name:str)->IntegrationPlugin: return self._plugins[name]
    def discover(self): return {n:[asdict(a) for a in p.actions()] for n,p in self._plugins.items()}
