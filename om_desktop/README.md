# OM Desktop Application (STEP 111)

Jarvis-class desktop shell:

```
Electron + React renderer  ←→  WebSocket  ←→  OM Python backend (consciousness)
         3D avatar / voice UI
```

## Layout

- `renderer/` — React UI (companion stage, activity stream, memory strip)
- `avatar/` — loads web Presence3D or Unity/Unreal embed
- `voice/` — mic + neural TTS playback
- `websocket/` — connects to `/api/companion/ws/{session}`
- `system_tray/` — always-on tray presence

## Quick path (today)

Until Electron packaging ships, use the web companion:

```bash
om-ai start
# opens http://127.0.0.1:8767/companion
```

## Next

1. `npm create electron-vite` inside `om_desktop/`
2. Point WebSocket at OM serve
3. Optional: Unity/Unreal MetaHuman window as avatar surface
