"""
OM Coding Intelligence Engine

Purpose:
Understand software requests and create
dynamic coding plans.

This module does NOT use fixed templates.
It analyzes:
- user requirement
- context
- technology
- project state
- architecture needs

Output:
Dynamic Coding Plan
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CodingPlan:

    user_goal: str

    intent: str = ""

    technologies: list[str] = field(
        default_factory=list
    )

    architecture: dict[str, Any] = field(
        default_factory=dict
    )

    files: list[str] = field(
        default_factory=list
    )

    implementation_steps: list[str] = field(
        default_factory=list
    )

    testing_plan: list[str] = field(
        default_factory=list
    )

    risks: list[str] = field(
        default_factory=list
    )

    confidence: float = 0.0



class CodingIntelligence:


    def __init__(
        self,
        reasoning_engine=None,
        memory=None,
        project_context=None
    ):

        self.reasoning_engine = (
            reasoning_engine
        )

        self.memory = memory

        self.project_context = (
            project_context
        )



    def analyze(
        self,
        message: str,
        context: dict | None = None
    ) -> CodingPlan:


        context = context or {}


        understanding = (
            self._understand_requirement(
                message,
                context
            )
        )


        architecture = (
            self._design_architecture(
                understanding
            )
        )


        files = (
            self._create_file_plan(
                architecture
            )
        )


        steps = (
            self._create_steps(
                understanding,
                architecture
            )
        )


        tests = (
            self._create_tests(
                architecture
            )
        )


        return CodingPlan(

            user_goal=message,

            intent=
                understanding["intent"],

            technologies=
                understanding["technologies"],

            architecture=
                architecture,

            files=files,

            implementation_steps=steps,

            testing_plan=tests,

            risks=
                self._detect_risks(
                    architecture
                ),

            confidence=0.85

        )



    # -----------------------------
    # Understanding Layer
    # -----------------------------


    def _understand_requirement(
        self,
        message,
        context
    ):


        if self.reasoning_engine:

            return (
                self.reasoning_engine.analyze(
                    message,
                    context
                )
            )


        return {

            "intent":
                "software_creation",

            "technologies":
                self._detect_technology(
                    message
                ),

            "goal":
                message

        }



    # -----------------------------
    # Architecture Reasoning
    # -----------------------------


    def _design_architecture(
        self,
        understanding
    ):


        technologies = (
            understanding.get(
                "technologies",
                []
            )
        )


        architecture = {

            "frontend": [],

            "backend": [],

            "database": [],

            "security": [],

            "deployment": []

        }


        for tech in technologies:


            if tech.lower() in [
                "react",
                "vue",
                "angular",
                "nextjs"
            ]:

                architecture[
                    "frontend"
                ].append(
                    tech
                )


            elif tech.lower() in [
                "python",
                "fastapi",
                "django",
                "node",
                "laravel"
            ]:

                architecture[
                    "backend"
                ].append(
                    tech
                )


        return architecture



    # -----------------------------
    # Dynamic File Planning
    # -----------------------------


    def _create_file_plan(
        self,
        architecture
    ):


        files=[]


        if architecture["frontend"]:

            files.extend([

                "src/components/",

                "src/pages/",

                "src/services/",

                "src/hooks/"

            ])



        if architecture["backend"]:

            files.extend([

                "api/",

                "services/",

                "models/",

                "tests/"

            ])



        if not files:

            files.append(
                "project structure determined after repository analysis"
            )


        return files



    # -----------------------------
    # Implementation Planning
    # -----------------------------


    def _create_steps(
        self,
        understanding,
        architecture
    ):


        return [

            "Analyze user requirement",

            "Select suitable architecture",

            "Create required components",

            "Implement business logic",

            "Connect required services",

            "Validate functionality",

            "Improve code quality"

        ]



    # -----------------------------
    # Testing Intelligence
    # -----------------------------


    def _create_tests(
        self,
        architecture
    ):


        return [

            "Validate expected user flow",

            "Handle invalid input",

            "Test error conditions",

            "Verify integration"

        ]



    def _detect_risks(
        self,
        architecture
    ):


        return [

            "Security validation required",

            "Dependencies should be verified",

            "Production configuration required"

        ]



    def _detect_technology(
        self,
        message
    ):


        text = message.lower()

        technologies=[]


        possible = [

            "react",

            "react native",

            "python",

            "fastapi",

            "django",

            "laravel",

            "node",

            "typescript",

            "flutter"

        ]


        for tech in possible:

            if tech in text:

                technologies.append(
                    tech
                )


        return technologies