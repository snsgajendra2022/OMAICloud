"""Prepare Chrome app profile so localhost mic is allowed (not blocked)."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def ensure_chrome_mic_allowed(profile_root: Path, *, ports: tuple[int, ...] = (8765, 8080, 8767)) -> None:
    """Patch Chrome Preferences so getUserMedia is ALLOW for local companion URLs.

    Chrome remembers Deny/Dismiss and then silently blocks mic forever for that
    profile — which looks like LISTENING UI with no ears.
    """
    default = profile_root / "Default"
    default.mkdir(parents=True, exist_ok=True)
    prefs_path = default / "Preferences"

    prefs: dict[str, Any] = {}
    if prefs_path.is_file():
        try:
            prefs = json.loads(prefs_path.read_text(encoding="utf-8"))
        except Exception:
            prefs = {}

    profile = prefs.setdefault("profile", {})
    content = profile.setdefault("content_settings", {})
    exceptions = content.setdefault("exceptions", {})

    mic = exceptions.setdefault("media_stream_mic", {})
    now = str(int(time.time() * 1_000_000) + 11644473600000000)

    keys = [f"http://127.0.0.1:{port},*" for port in ports]
    keys.append("http://localhost:8765,*")
    keys.append("http://127.0.0.1:*,*")
    for key in keys:
        mic[key] = {
            "last_modified": now,
            "setting": 1,  # ALLOW
        }

    # Clear auto-block so Chrome stops silently denying AudioCapture
    auto = exceptions.get("permission_autoblocking_data")
    if isinstance(auto, dict):
        for key in list(auto.keys()):
            if "127.0.0.1" in key or "localhost" in key:
                auto.pop(key, None)

    # Wipe past deny/dismiss history for mic prompts
    actions = content.setdefault("permission_actions", {})
    if isinstance(actions, dict):
        actions["mic_stream"] = []
        actions["audio_capture"] = []

    # Ensure default isn't block-all
    defaults = profile.setdefault("default_content_setting_values", {})
    if defaults.get("media_stream_mic") == 2:
        defaults["media_stream_mic"] = 1

    prefs_path.write_text(json.dumps(prefs, ensure_ascii=False), encoding="utf-8")
