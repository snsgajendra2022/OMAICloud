from __future__ import annotations
from typing import Any

class TTSEngine:
    def synthesize(self, text: str, *, emotion: str = "calm") -> dict[str, Any]:
        try:
            from om_ai.core.voice_engine.neural_tts import NeuralTTS
            n = NeuralTTS()
            if n.available().get("ok"):
                return n.synthesize(text, emotion=emotion)
        except Exception as exc:
            return {"ok": False, "reason": str(exc)}
        return {"ok": False, "reason": "neural_tts_not_configured", "fallback": "system_say"}
