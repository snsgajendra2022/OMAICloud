"""Native OM Companion window via pywebview / Chrome app (real mic)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable


def _ensure_pywebview() -> Any:
    try:
        import webview  # type: ignore

        return webview
    except ImportError as exc:
        raise SystemExit(
            "Desktop companion needs pywebview.\n"
            "  pip install 'pywebview>=5.0'\n"
            "  # or:  pip install -e '.[companion]'\n"
            f"({exc})"
        ) from exc


def _chrome_binary() -> str | None:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    ]
    for p in candidates:
        if Path(p).is_file():
            return p
    # Linux / Windows fallbacks
    for name in ("google-chrome", "chromium", "chromium-browser", "msedge"):
        try:
            out = subprocess.check_output(["which", name], text=True).strip()
            if out:
                return out
        except Exception:
            pass
    return None


def launch_chrome_app(
    url: str,
    *,
    width: int = 980,
    height: int = 720,
) -> bool:
    """Open companion as a Chrome/Edge app window (has working microphone)."""
    binary = _chrome_binary()
    if not binary:
        return False
    profile = Path("artifacts") / "companion" / "chrome_profile"
    profile.mkdir(parents=True, exist_ok=True)
    cmd = [
        binary,
        f"--app={url}",
        f"--window-size={width},{height}",
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--disable-features=TranslateUI",
    ]
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  Opening system UI (Chrome app — microphone works): {url}")
        print("  Allow Microphone once if macOS asks (Chrome).")
        print("  Stay on this window and just talk.\n")
        return True
    except Exception as exc:
        print(f"  Chrome app launch failed: {exc}")
        return False


class _Api:
    """JS bridge — tray + native mic for WebView fallback."""

    def __init__(self, window_ref: dict[str, Any]) -> None:
        self._ref = window_ref
        self._mic = None

    def ping(self) -> str:
        return "om-alive"

    def hide_to_tray(self) -> bool:
        win = self._ref.get("window")
        if win is None:
            return False
        try:
            win.hide()
            return True
        except Exception:
            return False

    def show_window(self) -> bool:
        win = self._ref.get("window")
        if win is None:
            return False
        try:
            win.show()
            win.restore()
            return True
        except Exception:
            return False

    def set_always_on_top(self, enabled: bool = True) -> bool:
        win = self._ref.get("window")
        if win is None:
            return False
        try:
            win.on_top = bool(enabled)
            return True
        except Exception:
            return False

    def start_native_mic(self) -> dict[str, Any]:
        """Start Python-side mic → push finals into the page."""
        from om_ai.desktop.native_mic import NativeMicBridge

        if self._mic is None:
            self._mic = NativeMicBridge()

        def _on_text(text: str) -> None:
            win = self._ref.get("window")
            if win is None or not text:
                return
            payload = json.dumps(text)
            js = (
                "window.OMNativeOnFinal && window.OMNativeOnFinal("
                + payload
                + ");"
            )
            try:
                win.evaluate_js(js)
            except Exception:
                pass

        return self._mic.start(_on_text)

    def stop_native_mic(self) -> dict[str, Any]:
        if self._mic is None:
            return {"ok": True}
        return self._mic.stop()

    def set_mic_busy(self, busy: bool = True) -> bool:
        if self._mic is not None:
            self._mic.set_busy(bool(busy))
        return True


def _start_mac_tray(
    *,
    title: str,
    on_show: Callable[[], None],
    on_quit: Callable[[], None],
) -> Any | None:
    """Menu-bar presence so OM stays while you change screens."""
    if sys.platform != "darwin":
        return None
    try:
        import rumps  # type: ignore
    except ImportError:
        rumps = None

    if rumps is not None:

        class OmTray(rumps.App):
            def __init__(self) -> None:
                super().__init__(title, quit_button=None)
                self.menu = [
                    rumps.MenuItem("Show OM Companion", callback=lambda _: on_show()),
                    rumps.MenuItem("Quit OM", callback=lambda _: on_quit()),
                ]

        app = OmTray()
        threading.Thread(target=app.run, daemon=True).start()
        return app

    try:
        from AppKit import (  # type: ignore
            NSApplication,
            NSStatusBar,
            NSMenu,
            NSMenuItem,
            NSVariableStatusItemLength,
            NSObject,
        )

        class TrayDelegate(NSObject):  # type: ignore
            def show_(self, _sender) -> None:
                on_show()

            def quit_(self, _sender) -> None:
                on_quit()

        NSApplication.sharedApplication()
        bar = NSStatusBar.systemStatusBar()
        item = bar.statusItemWithLength_(NSVariableStatusItemLength)
        item.setTitle_(title)
        menu = NSMenu.alloc().init()
        show_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Show OM Companion", "show:", ""
        )
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit OM", "quit:", ""
        )
        delegate = TrayDelegate.alloc().init()
        show_item.setTarget_(delegate)
        quit_item.setTarget_(delegate)
        menu.addItem_(show_item)
        menu.addItem_(quit_item)
        item.setMenu_(menu)
        return {"item": item, "menu": menu, "delegate": delegate}
    except Exception:
        return None


def launch_companion_desktop(
    url: str,
    *,
    title: str = "OM Companion",
    width: int = 980,
    height: int = 720,
    always_on_top: bool = True,
    tray: bool = True,
) -> int:
    """Open companion as a native OS window. Prefer Chrome app (mic works)."""
    # 1) Chrome/Edge app window — real microphone + SpeechRecognition
    force_webview = (os.getenv("OM_FORCE_WEBVIEW") or "").strip() in {"1", "true", "yes"}
    prefer_chrome = (os.getenv("OM_DESKTOP_CHROME") or "1").strip() not in {"0", "false", "no"}
    if prefer_chrome and not force_webview:
        if launch_chrome_app(url, width=width, height=height):
            print("  Tip: System Settings → Privacy & Security → Microphone → enable Google Chrome.")
            print("  (pywebview has no reliable mic on macOS — Chrome app is the listening UI.)\n")
            # Keep process alive like before
            try:
                while True:
                    time.sleep(2.0)
            except KeyboardInterrupt:
                print("\nShutting down...")
            return 0

    # 2) pywebview fallback + native Python mic bridge
    webview = _ensure_pywebview()
    try:
        webview.settings["ALLOW_DOWNLOADS"] = True
    except Exception:
        pass
    ref: dict[str, Any] = {"window": None, "quitting": False}
    api = _Api(ref)

    window = webview.create_window(
        title,
        url,
        width=width,
        height=height,
        resizable=True,
        confirm_close=False,
        background_color="#0B0F14",
        text_select=True,
        easy_drag=False,
        js_api=api,
    )
    ref["window"] = window

    def _on_closing() -> bool:
        if ref.get("quitting"):
            return True
        try:
            window.hide()
        except Exception:
            pass
        print("  OM is still with you in the menu bar — click OM to show again.")
        return False

    try:
        window.events.closing += _on_closing
    except Exception:
        pass

    def _show() -> None:
        try:
            window.show()
            window.restore()
            if always_on_top:
                window.on_top = True
        except Exception:
            pass

    def _quit() -> None:
        ref["quitting"] = True
        try:
            api.stop_native_mic()
        except Exception:
            pass
        try:
            window.destroy()
        except Exception:
            pass
        threading.Timer(0.4, lambda: os._exit(0)).start()

    if tray:
        _start_mac_tray(title="OM", on_show=_show, on_quit=_quit)

    def _after_start() -> None:
        time.sleep(0.4)
        try:
            if always_on_top:
                window.on_top = True
        except Exception:
            pass
        try:
            window.evaluate_js(
                """
                (function(){
                  if (window.pywebview && window.pywebview.api) {
                    window.OMDesktop = {
                      hide: () => window.pywebview.api.hide_to_tray(),
                      show: () => window.pywebview.api.show_window(),
                      alwaysOnTop: (v) => window.pywebview.api.set_always_on_top(!!v),
                      startNativeMic: () => window.pywebview.api.start_native_mic(),
                      stopNativeMic: () => window.pywebview.api.stop_native_mic(),
                      setMicBusy: (v) => window.pywebview.api.set_mic_busy(!!v),
                      alive: true,
                      nativeMic: true
                    };
                    try { window.pywebview.api.start_native_mic(); } catch (e) {}
                  }
                })();
                """
            )
        except Exception:
            pass
        # Also start from Python in case JS injection raced
        try:
            api.start_native_mic()
        except Exception as exc:
            print(f"  Native mic start: {exc}")

    print(f"  Opening system UI (WebView + native mic): {title}")
    print(f"  URL: {url}")
    print("  Allow Microphone for Terminal/Python in macOS Privacy settings.")
    print("  Or install: pip install faster-whisper sounddevice\n")

    webview.start(
        _after_start,
        gui=os.getenv("OM_WEBVIEW_GUI") or None,
        debug=bool(os.getenv("OM_WEBVIEW_DEBUG")),
        private_mode=False,
    )
    return 0
