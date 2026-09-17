class TimelineBuilder:


    def build(
        self,
        events
    ):


        timeline=[]


        for event in events:


            timeline.append({

                "time":
                    event.timestamp,

                "icon":
                    self.icon(
                        event.type.value
                    ),

                "title":
                    event.title,

                "description":
                    event.description

            })


        return timeline



    def icon(
        self,
        event_type
    ):


        icons={

            "searching":"🔎",

            "reading":"📄",

            "knowledge":"📚",

            "research":"🌐",

            "agent":"🤖",

            "validation":"✅",

            "response":"✍️",

            "thinking":"🧠"

        }


        return icons.get(
            event_type,
            "⚡"
        )