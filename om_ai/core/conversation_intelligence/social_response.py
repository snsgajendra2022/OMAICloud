import random


class SocialResponseEngine:


    def respond(
        self,
        intent
    ):


        responses = {


            "identity":[

                "I’m OM AI, your private AI assistant.",

                "My name is OM. I’m your AI assistant."

            ],



            "morning":[

                "Good morning! ☀️ How can I help you today?",

                "Good morning! Hope you have a great day. What would you like to work on?"

            ],



            "evening":[

                "Good evening! How can I help you?",

            ],



            "greeting":[

                "Hello! I’m OM. How can I help you today?",

                "Hi! Nice to meet you. What can I do for you?"

            ]

        }


        return random.choice(
            responses.get(
                intent,
                [
                    "Hello! How can I help you?"
                ]
            )
        )