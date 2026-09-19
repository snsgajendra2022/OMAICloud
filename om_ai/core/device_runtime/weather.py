"""Live weather lookup (Open-Meteo — no API key)."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any


def fetch_weather_spoken(query: str = "", *, locale_hi: bool = False) -> dict[str, Any]:
    """Return spoken weather summary. Best-effort; never raises to caller path."""
    city = (query or "").strip() or "Delhi"
    try:
        geo_url = (
            "https://geocoding-api.open-meteo.com/v1/search?"
            + urllib.parse.urlencode({"name": city, "count": 1, "language": "en", "format": "json"})
        )
        with urllib.request.urlopen(geo_url, timeout=4.0) as resp:
            geo = json.loads(resp.read().decode("utf-8"))
        results = geo.get("results") or []
        if not results:
            msg = (
                f"Mujhe {city} ka mausam nahi mila."
                if locale_hi
                else f"I couldn't find weather for {city}."
            )
            return {"ok": False, "spoken": msg, "city": city}
        place = results[0]
        lat = place.get("latitude")
        lon = place.get("longitude")
        name = place.get("name") or city
        wx_url = (
            "https://api.open-meteo.com/v1/forecast?"
            + urllib.parse.urlencode(
                {
                    "latitude": lat,
                    "longitude": lon,
                    "current_weather": "true",
                    "timezone": "auto",
                }
            )
        )
        with urllib.request.urlopen(wx_url, timeout=4.0) as resp:
            wx = json.loads(resp.read().decode("utf-8"))
        cur = wx.get("current_weather") or {}
        temp = cur.get("temperature")
        wind = cur.get("windspeed")
        code = int(cur.get("weathercode") or 0)
        cond = _code_to_label(code, hi=locale_hi)
        if locale_hi:
            spoken = f"{name} mein abhi {cond}, lagbhag {temp} degree Celsius."
            if wind is not None:
                spoken += f" Hawa {wind} kilometer per hour."
        else:
            spoken = f"In {name} it's {cond}, about {temp}°C."
            if wind is not None:
                spoken += f" Wind around {wind} km/h."
        return {
            "ok": True,
            "spoken": spoken,
            "city": name,
            "temperature": temp,
            "condition": cond,
            "raw": cur,
        }
    except Exception as exc:
        msg = (
            "Mausam abhi nahi nikal paya — thodi der baad try kijiye."
            if locale_hi
            else "I couldn't fetch the weather right now."
        )
        return {"ok": False, "spoken": msg, "error": str(exc)[:160]}


def _code_to_label(code: int, *, hi: bool = False) -> str:
    mapping = {
        0: ("clear", "saaf"),
        1: ("mainly clear", "zyada tar saaf"),
        2: ("partly cloudy", "thoda badal"),
        3: ("overcast", "badalon se bhara"),
        45: ("foggy", "kohra"),
        48: ("foggy", "kohra"),
        51: ("light drizzle", "halki boond"),
        61: ("light rain", "halki baarish"),
        63: ("rain", "baarish"),
        65: ("heavy rain", "tez baarish"),
        71: ("snow", "barf"),
        80: ("showers", "jhadis"),
        95: ("thunderstorm", "garaj ke saath baarish"),
    }
    en, hin = mapping.get(code, ("mixed conditions", "mila-jula mausam"))
    return hin if hi else en
