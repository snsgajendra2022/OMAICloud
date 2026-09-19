from __future__ import annotations

class InterruptionHandler:
    def should_yield(self, user_text: str, *, speaking: bool) -> bool:
        if not speaking:
            return False
        low = (user_text or "").lower().strip()
        return bool(low) and (
            low.startswith(("stop", "wait", "hold on", "ruk", "bas"))
            or len(low.split()) >= 2
        )

    def ack(self, address: str = "Sir") -> str:
        return f"Of course, {address}. Go ahead."
