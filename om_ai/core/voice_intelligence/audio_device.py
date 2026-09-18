"""Microphone / speaker device enumeration and preference persistence."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AudioDeviceManager:
    def __init__(self, prefs_path: str | Path | None = None) -> None:
        root = Path(__file__).resolve().parents[3]
        self.prefs_path = Path(prefs_path or root / "artifacts" / "companion" / "audio_device.json")
        self.prefs_path.parent.mkdir(parents=True, exist_ok=True)
        self._prefs = self._load()

    def _load(self) -> dict[str, Any]:
        if self.prefs_path.is_file():
            try:
                return json.loads(self.prefs_path.read_text())
            except Exception:
                return {}
        return {}

    def save(self) -> None:
        self.prefs_path.write_text(json.dumps(self._prefs, indent=2))

    def list_input_devices(self) -> list[dict[str, Any]]:
        devices: list[dict[str, Any]] = []
        try:
            import sounddevice as sd  # type: ignore

            for i, d in enumerate(sd.query_devices()):
                if int(d.get("max_input_channels") or 0) > 0:
                    devices.append(
                        {
                            "id": i,
                            "name": str(d.get("name") or f"input-{i}"),
                            "channels": int(d.get("max_input_channels") or 0),
                            "sample_rate": float(d.get("default_samplerate") or 16000),
                            "kind": "input",
                        }
                    )
        except Exception as exc:
            logger.debug("sounddevice unavailable: %s", exc)
            devices.append(
                {
                    "id": 0,
                    "name": "default-input (unavailable until sounddevice installed)",
                    "channels": 1,
                    "sample_rate": 16000,
                    "kind": "input",
                    "available": False,
                }
            )
        return devices

    def list_output_devices(self) -> list[dict[str, Any]]:
        devices: list[dict[str, Any]] = []
        try:
            import sounddevice as sd  # type: ignore

            for i, d in enumerate(sd.query_devices()):
                if int(d.get("max_output_channels") or 0) > 0:
                    devices.append(
                        {
                            "id": i,
                            "name": str(d.get("name") or f"output-{i}"),
                            "channels": int(d.get("max_output_channels") or 0),
                            "sample_rate": float(d.get("default_samplerate") or 22050),
                            "kind": "output",
                        }
                    )
        except Exception as exc:
            logger.debug("sounddevice output unavailable: %s", exc)
            devices.append(
                {
                    "id": 0,
                    "name": "default-output (optional)",
                    "channels": 1,
                    "sample_rate": 22050,
                    "kind": "output",
                    "available": False,
                }
            )
        return devices

    def select_input(self, device_id: int) -> dict[str, Any]:
        self._prefs["input_device_id"] = int(device_id)
        self.save()
        return {"ok": True, "input_device_id": int(device_id)}

    def selected_input(self) -> int | None:
        v = self._prefs.get("input_device_id")
        return int(v) if v is not None else None

    def status(self) -> dict[str, Any]:
        inputs = self.list_input_devices()
        outputs = self.list_output_devices()
        ready = any(d.get("available", True) for d in inputs if "unavailable" not in str(d.get("name")))
        # If sounddevice missing, mark warn not fail
        try:
            import sounddevice  # noqa: F401

            backend = "sounddevice"
            ready = len(inputs) > 0
        except Exception:
            backend = "none"
            ready = False
        return {
            "backend": backend,
            "inputs": inputs,
            "outputs": outputs,
            "selected_input": self.selected_input(),
            "ready": ready,
        }
