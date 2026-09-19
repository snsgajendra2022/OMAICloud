"""CLI commands for OM Companion — imported from om_ai/cli.py (no cli/ package)."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import webbrowser
from typing import Any


def _print(obj: Any) -> None:
    if isinstance(obj, str):
        print(obj)
    else:
        print(json.dumps(obj, indent=2, default=str))


def _port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def _pick_port(host: str, preferred: int) -> int:
    if _port_free(host, preferred):
        return preferred
    for p in (8080, 8765, 8767, 8090, 8081, 8877, 9000):
        if p != preferred and _port_free(host, p):
            return p
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return int(s.getsockname()[1])


def _api_alive(host: str, port: int) -> bool:
    try:
        import urllib.request

        with urllib.request.urlopen(f"http://{host}:{port}/api/companion/status", timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False


def _companion_page_alive(host: str, port: int) -> bool:
    try:
        import urllib.request

        with urllib.request.urlopen(f"http://{host}:{port}/companion", timeout=1.5) as r:
            return int(getattr(r, "status", 0) or 0) in {200, 304}
    except Exception:
        return False


def _repo_root() -> "Path":
    from pathlib import Path

    # om_ai/cli_commands/companion_commands.py → repo root
    return Path(__file__).resolve().parents[2]


def _ensure_api_server(host: str, port: int) -> tuple[int, subprocess.Popen | None]:
    """Start uvicorn for companion UI if not already serving OM API."""
    # Prefer an already-running OM API (any common port)
    for candidate in (port, 8080, 8765, 8767, 8090):
        if _api_alive(host, candidate):
            return candidate, None

    if not _port_free(host, port):
        port = _pick_port(host, port)

    env = os.environ.copy()
    env.setdefault("OM_MODEL_PROVIDER", "om_native")
    env.setdefault("OM_AI_CHAT_BACKEND", "om_native")
    repo_root = _repo_root()
    log_path = repo_root / "artifacts" / "companion_api.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "om_ai.api.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    log_f = open(log_path, "a", encoding="utf-8")
    log_f.write(f"\n--- start {time.strftime('%Y-%m-%d %H:%M:%S')} port={port} ---\n")
    log_f.flush()
    proc = subprocess.Popen(
        cmd,
        cwd=str(repo_root),
        env=env,
        stdout=log_f,
        stderr=subprocess.STDOUT,
    )
    for _ in range(60):
        time.sleep(0.25)
        if _api_alive(host, port):
            print(f"  API server ready on http://{host}:{port}")
            return port, proc
        if proc.poll() is not None:
            break

    # Failed — surface log tail
    print(f"  ERROR: companion API did not start on {host}:{port}")
    print(f"  See log: {log_path}")
    try:
        tail = log_path.read_text(encoding="utf-8")[-1200:]
        print(tail)
    except Exception:
        pass
    return port, proc


def cmd_companion_start(args) -> int:
    from om_ai.core.companion_runtime import get_companion_runtime, start_companion, format_banner

    host = (os.getenv("OM_COMPANION_BIND_HOST") or "127.0.0.1").strip()
    preferred = int(os.getenv("OM_COMPANION_BIND_PORT") or os.getenv("PORT") or "8080")

    # Browser companion uses Web Speech + /tts — native sounddevice is optional
    browser_ui = not bool(getattr(args, "no_avatar", False)) and not bool(
        getattr(args, "text_only", False)
    )
    status = start_companion(
        text_only=bool(getattr(args, "text_only", False)) or browser_ui,
        no_avatar=bool(getattr(args, "no_avatar", False)),
        wake_word_enabled=False
        if browser_ui
        else (
            not bool(getattr(args, "no_wake_word", False))
            and not bool(getattr(args, "text_only", False))
        ),
    )
    rt = get_companion_runtime()
    if getattr(args, "text_only", False) or browser_ui:
        rt.config.text_only = True
        rt.config.wake_word_enabled = False
    if getattr(args, "no_wake_word", False):
        rt.config.wake_word_enabled = False
    if getattr(args, "no_avatar", False):
        rt.config.no_avatar = True

    print(format_banner(status))
    if browser_ui:
        print("  Note: mic/voice run in the browser (no local sounddevice required).\n")

    api_proc = None
    if browser_ui:
        port, api_proc = _ensure_api_server(host, preferred)
        rt.config.bind_host = host
        rt.config.bind_port = port
        url = f"http://{host}:{port}/companion"
        if not _api_alive(host, port):
            print(f"\n  Companion UI failed to start at {url}")
            print("  Try:  om-ai serve --host 127.0.0.1 --port 8080")
            print("  Then open: http://127.0.0.1:8080/companion\n")
            return 1
        print(f"\n  Companion UI:  {url}")
        print("  Talk to OM — allow microphone in the browser.\n")
        if preferred != port:
            print(f"  NOTE: preferred port {preferred} unavailable — using {port}.\n")
        try:
            webbrowser.open(url)
        except Exception:
            pass
    elif getattr(args, "text_only", False):
        print("\nText mode ready. Type messages (/quit to exit).\n")
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
                acts = out.get("activities") or []
                if acts:
                    print("  · " + " → ".join(str(a) for a in acts[:6]))
                ans = str(out.get("answer") or "")
                if ans:
                    print(f"OM> {ans}\n")
        except KeyboardInterrupt:
            print("\nShutting down...")
        from om_ai.core.companion_runtime import stop_companion

        stop_companion()
        return 0
    else:
        print("\nVoice runtime active (no avatar). Ctrl+C to stop.\n")

    if browser_ui or not getattr(args, "text_only", False):
        try:
            while True:
                time.sleep(1.0)
                # If we spawned the API and it died, exit with a clear message
                if api_proc is not None and api_proc.poll() is not None:
                    print("\n  Companion API process exited — UI will stop working.")
                    print("  Restart with: om-ai start\n")
                    break
        except KeyboardInterrupt:
            print("\nShutting down...")
            from om_ai.core.companion_runtime import stop_companion

            stop_companion()
            if api_proc is not None and api_proc.poll() is None:
                api_proc.terminate()
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
    host = (os.getenv("OM_COMPANION_BIND_HOST") or "127.0.0.1").strip()
    preferred = int(os.getenv("OM_COMPANION_BIND_PORT") or os.getenv("PORT") or "8765")
    port_ok = _port_free(host, preferred) or _api_alive(host, preferred)
    detail = f"{host}:{preferred}"
    if not _port_free(host, preferred) and not _api_alive(host, preferred):
        detail += " BUSY (not OM — try 8765; Apache often owns 8080)"
        status = "FAIL"
    elif _api_alive(host, preferred):
        detail += " OM API alive"
        status = "PASS"
    else:
        status = "PASS" if port_ok else "WARN"
    doc.setdefault("checks", []).append({"name": "companion_port", "status": status, "detail": detail})
    for c in doc.get("checks") or []:
        print(f"[{c.get('status')}] {c.get('name')}: {c.get('detail')}")
    print("OK" if doc.get("ok") and status != "FAIL" else "ISSUES")
    return 0 if doc.get("ok") and status != "FAIL" else 1


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


def cmd_om_start(args) -> int:
    """STEP 112 — `om-ai start` boots Jarvis companion (consciousness + UI)."""
    try:
        from om_ai.env import load_dotenv

        load_dotenv()
    except Exception:
        pass
    from om_ai.core.om_consciousness import get_consciousness

    mind = get_consciousness()
    greeting = mind.boot_greeting()
    print("=" * 48)
    print("                 OM AI")
    print("=" * 48)
    print(f"\n  {greeting}\n")
    print("  Layers: consciousness · dialogue · memory · presence · avatar · actions\n")
    try:
        from om_ai.core.voice_engine import get_voice_engine

        st = get_voice_engine().status()
        ns = st.get("neural") or {}
        if ns.get("configured") and st.get("default") == "neural":
            print(f"  TTS: ElevenLabs neural · voice {ns.get('voice_id')}\n")
        else:
            print("  TTS: FREE macOS Aman — Indian male (no paid key required)\n")
    except Exception:
        pass

    class _A:
        text_only = bool(getattr(args, "text_only", False))
        no_avatar = bool(getattr(args, "no_avatar", False))
        no_wake_word = bool(getattr(args, "no_wake_word", False))

    return cmd_companion_start(_A())


def register_companion_parser(sp) -> None:
    """Attach `companion` subcommand tree to argparse subparsers."""
    # Top-level: om-ai start
    start_top = sp.add_parser("start", help="Start OM Jarvis companion (3D presence + consciousness)")
    start_top.add_argument("--text-only", action="store_true")
    start_top.add_argument("--no-avatar", action="store_true")
    start_top.add_argument("--no-wake-word", action="store_true")
    start_top.set_defaults(func=cmd_om_start)

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
