"""
OM AI Autonomous Agent Civilization Layer

Provides:
- Agent foundation
- Agent registry
- Agent manager
- Agent communication
- Agent memory
- Agent evaluation
- Agent team building
"""


from .agent import Agent

from .agent_registry import AgentRegistry

from .agent_manager import AgentManager

from .agent_communication import AgentCommunication

from .agent_memory import AgentMemory

from .agent_evaluator import AgentEvaluator

from .team_builder import TeamBuilder
from .coding_agent import CodingAgent
from .research_agent import ResearchAgent
from .memory_agent import MemoryAgent
from .knowledge_agent import KnowledgeAgent
from .security_agent import SecurityAgent
from .quality_agent import QualityAgent


__all__ = [

    "Agent",

    "AgentRegistry",

    "AgentManager",

    "AgentCommunication",

    "AgentMemory",

    "AgentEvaluator",

    "TeamBuilder",
    
    "CollaborationEngine",

    "CodingAgent",

    "ResearchAgent",

    "MemoryAgent",

    "KnowledgeAgent",

    "SecurityAgent",

    "QualityAgent"

]