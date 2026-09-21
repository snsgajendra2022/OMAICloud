# OM Companion Desktop App (STEP 69)

Tauri + React shell for the living OM voice companion.

## Run (dev)

```bash
# Backend (required)
cd "/path/to/om-ai-operating-brain 3"
.venv/bin/om-ai serve --host 127.0.0.1 --port 8080

# UI (when Tauri toolchain installed)
cd om_companion_app
npm install
npm run tauri dev
```

Until Tauri is installed, open the HUD: http://127.0.0.1:8080/companion

## Features

- System tray / always available
- Microphone indicator
- Avatar window (embeds companion HUD)
- Notifications
- Settings + permissions
- OS start (optional)

Connects to OM FastAPI companion APIs — does not duplicate the brain.
