"""Realtime event bus tests."""
from om_ai.core.realtime.event import CompanionEvent
from om_ai.core.realtime.event_bus import RealtimeEventBus
from om_ai.core.realtime.event_types import EventType


def test_publish_subscribe():
    bus = RealtimeEventBus()
    seen = []

    def handler(ev: CompanionEvent) -> None:
        seen.append(ev.event_type)

    bus.subscribe("companion.state", handler)
    bus.publish(
        CompanionEvent(
            event_type="companion.state",
            session_id="s1",
            trace_id="t1",
            payload={"state": "LISTENING"},
        )
    )
    assert seen == ["companion.state"]
    recent = bus.recent(1)
    assert recent[0]["event_type"] == "companion.state"
    assert recent[0]["session_id"] == "s1"
    assert "event_id" in recent[0]
    assert "timestamp" in recent[0]


def test_event_types_cover_core():
    assert EventType.COMPANION_STATE == "companion.state"
    assert EventType.PERMISSION_REQUIRED == "permission.required"
    assert EventType.TTS_AUDIO == "tts.audio"
    assert EventType.RUNTIME_ERROR == "runtime.error"
