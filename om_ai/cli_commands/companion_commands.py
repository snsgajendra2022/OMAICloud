"""CLI commands for OM Companion — imported from om_ai/cli.py (no cli/ package)."""
from __future__ import annotations

import json
from typing import Any


def _print(obj: Any) -> None:
    if isinstance(obj, str):
        print(obj)
    else:
        print(json.dumps(obj, indent=2, default=str))


def cmd_companion_start(args) -> int:
    from om_ai.core.companion_runtime import start_companion, format_banner

    status = start_companion(
        text_only=bool(getattr(args, "text_only", False)),
        no_avatar=bool(getattr(args, "no_avatar", False)),
        wake_word_enabled=not bool(getattr(args, "no_wake_word", False))
        and not bool(getattr(args, "text_only", False)),
    )
    # force flags onto runtime config
    from om_ai.core.companion_runtime import get_companion_runtime

    rt = get_companion_runtime()
    if getattr(args, "text_only", False):
        rt.config.text_only = True
        rt.config.wake_word_enabled = False
    if getattr(args, "no_wake_word", False):
        rt.config.wake_word_enabled = False
    if getattr(args, "no_avatar", False):
        rt.config.no_avatar = True
    print(format_banner(status))
    if getattr(args, "text_only", False):
        print("\nText mode ready. Type messages (empty line / Ctrl+C to exit).\n")
        try:
            while True:
                try:
                    line = input("You> ").strip()
                except EOFError:
                    break
                if not line:
                    continue
                if line.lower() in {"/quit", "/exit", "quit", "exit"}:
                    break
                out = rt.handle_text(line)
                ans = str(out.get("answer") or "")
                acts = out.get("activities") or []
                if acts:
                    print("  · " + " → ".join(str(a) for a in acts[:6]))
                if ans:
                    print(f"OM> {ans}\n")
                elif out.get("waiting_for_wake"):
                    print("(waiting for wake word — say 'hey om' or disable wake word)\n")
        except KeyboardInterrupt:
            print("\nShutting down...")
        from om_ai.core.companion_runtime import stop_companion

        stop_companion()
    return 0


def cmd_companion_stop(args) -> int:
    from om_ai.core.companion_runtime import stop_companion

    _print(stop_companion())
    return 0


def cmd_companion_status(args) -> int:
    from om_ai.core.companion_runtime import get_companion_runtime, format_banner

    rt = get_companion_runtime()
    if not rt._started:
        banner = rt.status_banner()
        banner["note"] = "Runtime not started — showing component probe"
    else:
        banner = rt.status_banner()
    print(format_banner(banner))
    if getattr(args, "json", False):
        _print(banner)
    return 0


def cmd_companion_doctor(args) -> int:
    from om_ai.core.companion_runtime import get_companion_runtime

    doc = get_companion_runtime().doctor()
    for c in doc.get("checks") or []:
        print(f"[{c.get('status')}] {c.get('name')}: {c.get('detail')}")
    print("OK" if doc.get("ok") else "ISSUES")
    return 0 if doc.get("ok") else 1


def cmd_companion_devices(args) -> int:
    from om_ai.core.voice_intelligence import AudioDeviceManager

    _print(AudioDeviceManager().status())
    return 0


def cmd_companion_permissions(args) -> int:
    from pathlib import Path

    path = Path("artifacts/companion/actions_audit.jsonl")
    if not path.is_file():
        _print({"permissions": [], "note": "no audit log yet"})
        return 0
    rows = []
    for line in path.read_text().splitlines()[-50:]:
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    _print({"recent_audit": rows})
    return 0


def cmd_companion_memory(args) -> int:
    from om_ai.core.companion_runtime import get_companion_runtime

    rt = get_companion_runtime()
    if rt.memory is None:
        try:
            from om_ai.core.companion_memory import MemoryService

            mem = MemoryService()
        except Exception as exc:
            _print({"error": str(exc)})
            return 1
    else:
        mem = rt.memory
    if getattr(args, "clear", False):
        if hasattr(mem, "clear"):
            mem.clear()
        _print({"cleared": True})
        return 0
    if hasattr(mem, "list_all"):
        _print(mem.list_all())
    elif hasattr(mem, "snapshot"):
        _print(mem.snapshot())
    else:
        _print({"memory": str(mem)})
    return 0


def cmd_companion_config(args) -> int:
    from om_ai.core.companion_runtime import CompanionConfig

    cfg = CompanionConfig.from_env()
    _print(cfg.__dict__)
    return 0


def register_companion_parser(sp) -> None:
    """Attach `companion` subcommand tree to argparse subparsers."""
    comp = sp.add_parser("companion", help="OM Companion Runtime (voice + avatar + actions)")
    csp = comp.add_subparsers(dest="companion_sub", required=True)

    start = csp.add_parser("start", help="Start companion runtime")
    start.add_argument("--text-only", action="store_true", help="No audio hardware")
    start.add_argument("--no-avatar", action="store_true", help="Skip avatar UI launch")
    start.add_argument("--no-wake-word", action="store_true", help="Skip wake-word gate")
    start.set_defaults(func=cmd_companion_start)

    stop = csp.add_parser("stop", help="Stop companion runtime")
    stop.set_defaults(func=cmd_companion_stop)

    status = csp.add_parser("status", help="Show companion status")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_companion_status)

    doctor = csp.add_parser("doctor", help="Health diagnostics")
    doctor.set_defaults(func=cmd_companion_doctor)

    devices = csp.add_parser("devices", help="List audio devices")
    devices.set_defaults(func=cmd_companion_devices)

    perms = csp.add_parser("permissions", help="Show recent permission/action audit")
    perms.set_defaults(func=cmd_companion_permissions)

    mem = csp.add_parser("memory", help="Show or clear companion memory")
    mem.add_argument("--clear", action="store_true")
    mem.set_defaults(func=cmd_companion_memory)

    cfg = csp.add_parser("config", help="Show companion configuration")
    cfg.set_defaults(func=cmd_companion_config)
