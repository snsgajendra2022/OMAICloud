from __future__ import annotations
import os
import time
import requests
import logging


logger = logging.getLogger(
    "om.distillation.ollama"
)


class OllamaClient:
    """
    Local Ollama HTTP Client.

    No API keys.
    No external services.

    Uses:
    http://127.0.0.1:11434
    """


    def __init__(
        self,
        base_url: str = os.getenv("OM_OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        timeout: int = 180,
        retries: int = 2,
    ):

        self.base_url = (
            base_url.rstrip("/")
        )

        self.timeout = timeout

        self.retries = retries



    def health_check(self):

        try:

            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )

            return {
                "status": "healthy",
                "code": response.status_code
            }


        except Exception as error:

            return {
                "status": "unavailable",
                "error": str(error)
            }



    def list_models(self):

        response = requests.get(
            f"{self.base_url}/api/tags",
            timeout=self.timeout
        )


        response.raise_for_status()


        data = response.json()


        return [

            model.get("name")

            for model
            in data.get(
                "models",
                []
            )

        ]



    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ):


        last_error = None


        for attempt in range(
            self.retries + 1
        ):

            try:

                start = time.time()


                payload = {

                    "model":
                        model,

                    "prompt":
                        prompt,

                    "stream":
                        False,

                    "options": {

                        "temperature":
                            temperature

                    }

                }


                if max_tokens:

                    payload["options"][
                        "num_predict"
                    ] = max_tokens



                response = requests.post(

                    f"{self.base_url}/api/generate",

                    json=payload,

                    timeout=self.timeout

                )


                response.raise_for_status()


                result = response.json()


                return {

                    "status":
                        "success",

                    "model":
                        model,

                    "response":
                        result.get(
                            "response",
                            ""
                        ),

                    "latency_ms":
                        int(
                            (
                                time.time()
                                -
                                start
                            )
                            *
                            1000
                        ),

                    "metadata":
                        result

                }



            except Exception as error:

                last_error = error

                logger.warning(
                    "Ollama attempt failed %s",
                    attempt
                )



        return {

            "status":
                "failed",

            "model":
                model,

            "error":
                str(last_error)

        }