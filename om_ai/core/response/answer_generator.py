"""
OM-1.0 Answer Generator

Creates final human readable responses.

Modes:

user:
    Clean ChatGPT style answer

developer:
    Full reasoning/debug information

Supports:

- Memory injection
- Knowledge context
- Solution formatting
- Plan formatting
"""


from __future__ import annotations


from typing import Any





class AnswerGenerator:



    def generate(
        self,
        question: str,
        reasoning: dict[str, Any] | None = None,
        knowledge: dict[str, Any] | list | None = None
    ) -> dict[str, Any]:


        reasoning = reasoning or {}


        sections: list[dict[str,str]] = []


        # --------------------------------
        # Memory Context
        # --------------------------------

        memory = reasoning.get(
            "memory_context",
            []
        )


        memory_hint = ""


        if memory:


            memory_hint = (

                "Relevant previous memory:\n"

                +

                "\n".join(

                    self._memory_text(x)

                    for x in memory[:5]

                )

            )


            reasoning["memory_hint"] = memory_hint



        # --------------------------------
        # Understanding
        # --------------------------------

        understanding = reasoning.get(
            "understanding",
            {}
        )


        technology = ""


        if isinstance(
            understanding,
            dict
        ):

            technology = str(

                understanding.get(
                    "technology",
                    ""

                )
                or ""

            )



        # --------------------------------
        # Solution
        # --------------------------------

        solution = str(

            reasoning.get(
                "solution",
                ""

            )
            or ""

        ).strip()



        answer_parts=[]



        if technology:


            text = (

                f"Technology: **{technology}**"

            )


            answer_parts.append(text)


            sections.append({

                "title":"Technology",

                "body":text

            })



        if solution:


            answer_parts.append(
                solution
            )


            sections.append({

                "title":"Solution",

                "body":solution

            })



        elif understanding:


            answer_parts.append(

                self._format_understanding(
                    understanding
                )

            )



        # --------------------------------
        # Knowledge
        # --------------------------------


        knowledge_text = self._extract_knowledge(
            knowledge
        )


        if knowledge_text:


            answer_parts.append(
                knowledge_text
            )


            sections.append({

                "title":"Knowledge",

                "body":knowledge_text

            })



        # --------------------------------
        # Memory Injection
        # --------------------------------


        if memory_hint:


            sections.append({

                "title":"Memory",

                "body":memory_hint

            })



        # --------------------------------
        # Plan
        # --------------------------------


        plan = list(

            reasoning.get(
                "plan",
                []
            )
            or []

        )


        if plan:


            plan_text = self._format_plan(
                plan
            )


            answer_parts.append(
                plan_text
            )


            sections.append({

                "title":"Plan",

                "body":plan_text

            })



        # --------------------------------
        # Final Response
        # --------------------------------


        answer = "\n\n".join(

            x.strip()

            for x in answer_parts

            if x and x.strip()

        )


        if not answer:


            answer = (

                "I need more information "

                "to provide a precise solution."

            )



        return {


            "answer": answer,


            "sections": sections,


            "memory_used": bool(memory),


            "memory_count": len(memory),


            "question": question


        }





    def _memory_text(
        self,
        item: Any
    ) -> str:


        if isinstance(
            item,
            dict
        ):

            return str(

                item.get(
                    "memory",
                    item

                )

            )


        return str(item)




    def _extract_knowledge(
        self,
        knowledge
    ) -> str:


        if isinstance(
            knowledge,
            dict
        ):

            return str(

                knowledge.get(
                    "answer",
                    ""

                )
                or ""

            ).strip()



        if isinstance(
            knowledge,
            list
        ):


            return "\n".join(

                str(x)

                for x in knowledge[:3]

            )


        return ""





    def _format_understanding(
        self,
        understanding
    ) -> str:


        if isinstance(
            understanding,
            dict
        ):


            return "\n".join(

                f"{key}: {value}"

                for key,value in understanding.items()

                if value

            )


        return str(understanding)




    def _format_plan(
        self,
        plan
    ) -> str:


        if not plan:

            return ""


        lines=[

            "Next steps:"

        ]


        for index,item in enumerate(
            plan,
            1
        ):

            lines.append(

                f"{index}. {item}"

            )


        return "\n".join(lines)