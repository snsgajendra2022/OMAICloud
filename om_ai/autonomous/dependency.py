"""
OM Task Dependency Graph
"""




class DependencyGraph:



    def build(

        self,

        tasks

    ):


        graph={}



        for task in tasks:


            graph[task.id]=task.depends_on



        return graph




    def ready_tasks(

        self,

        tasks

    ):


        completed={

            t.id

            for t in tasks

            if t.status=="completed"

        }



        return [

            t

            for t in tasks

            if t.status=="pending"

            and all(

                x in completed

                for x in t.depends_on

            )

        ]