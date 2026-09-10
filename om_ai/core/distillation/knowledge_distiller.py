from __future__ import annotations

from .knowledge_extractor import KnowledgeItem



class KnowledgeDistiller:
    """
    Combines multiple extracted knowledge items.

    Removes duplication.
    Preserves disagreement.
    Creates OM knowledge format.
    """


    def distill(
        self,
        items: list[KnowledgeItem]
    ) -> KnowledgeItem:


        if not items:

            raise ValueError(
                "No knowledge items supplied"
            )


        base = items[0]


        for item in items[1:]:


            base.concepts.extend(
                item.concepts
            )


            base.facts.extend(
                item.facts
            )


            base.examples.extend(
                item.examples
            )


            base.code_patterns.extend(
                item.code_patterns
            )


            base.source_teachers.extend(
                item.source_teachers
            )



        base.concepts = self._unique(
            base.concepts
        )


        base.facts = self._unique(
            base.facts
        )


        base.examples = self._unique(
            base.examples
        )


        base.source_teachers = self._unique(
            base.source_teachers
        )


        base.confidence = min(

            len(
                base.source_teachers
            )
            /
            5,

            1.0

        )


        return base



    def _unique(
        self,
        values
    ):

        result=[]

        seen=set()


        for value in values:

            key=value.lower().strip()


            if key not in seen:

                seen.add(key)

                result.append(
                    value
                )


        return result