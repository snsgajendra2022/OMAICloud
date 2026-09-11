"""Local Ollama HTTP client for teacher distillation."""
from __future__ import annotations

import logging
import os
import time

import requests

logger = logging.getLogger("om.distillation.ollama")


class OllamaClient:
    """Local Ollama HTTP client (no API keys)."""

    def __init__(
        self,
        base_url: str = os.getenv("OM_OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        timeout: int = 180,
        retries: int = 2,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = int(timeout)
        self.retries = int(retries)

    def health_check(self):
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return {"status": "healthy", "code": response.status_code}
        except Exception as error:
            return {"status": "unavailable", "error": str(error)}

    def list_models(self):
        response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return [model.get("name") for model in data.get("models", []) if model.get("name")]

    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ):
        last_error = None
        for attempt in range(self.retries + 1):
            try:
                start = time.time()
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        # Keep ctx small so teachers fit in memory and finish under timeout.
                        "num_ctx": int(os.getenv("OM_OLLAMA_NUM_CTX", "2048")),
                        "num_predict": int(
                            max_tokens
                            if max_tokens is not None
                            else os.getenv("OM_OLLAMA_NUM_PREDICT", "512")
                        ),
                    },
                }
                if max_tokens:
                    payload["options"]["num_predict"] = int(max_tokens)

                # Cold load + generation; allow long waits but prefer small ctx above.
                timeout = max(self.timeout, int(os.getenv("OM_OLLAMA_GENERATE_TIMEOUT", "600")))
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=timeout,
                )
                response.raise_for_status()
                result = response.json()
                text = str(result.get("response") or "").strip()
                if not text:
                    raise RuntimeError("empty_ollama_response")
                return {
                    "status": "success",
                    "model": model,
                    "response": text,
                    "text": text,
                    "latency_ms": int((time.time() - start) * 1000),
                    "metadata": {
                        "eval_count": result.get("eval_count"),
                        "eval_duration": result.get("eval_duration"),
                    },
                }
            except Exception as error:
                last_error = error
                logger.warning("Ollama attempt failed %s: %s", attempt, error)
                time.sleep(min(2 * (attempt + 1), 8))

        return {
            "status": "failed",
            "model": model,
            "error": str(last_error),
            "response": "",
            "text": "",
            "latency_ms": 0,
            "metadata": {},
        }
