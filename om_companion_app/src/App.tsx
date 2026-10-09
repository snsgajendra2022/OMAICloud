import { useMemo, useState } from "react";
import { AvatarPanel } from "./avatar/AvatarPanel";
import { ChatPanel } from "./chat/ChatPanel";
import { MicIndicator } from "./voice/MicIndicator";
import { SettingsPanel } from "./settings/SettingsPanel";
import { PermissionsPanel } from "./permissions/PermissionsPanel";

// const API = import.meta.env.VITE_OM_API;
const API = "http://127.0.0.1:8080";

export default function App() {
  const [tab, setTab] = useState<"companion" | "settings" | "permissions">("companion");
  const [micOn, setMicOn] = useState(false);
  const hud = useMemo(() => `${API}/companion?v=hud5&embed=1`, []);

  return (
    <div className="shell">
      <header className="top">
        <div className="brand">OM</div>
        <MicIndicator active={micOn} />
        <nav>
          <button onClick={() => setTab("companion")}>Companion</button>
          <button onClick={() => setTab("settings")}>Settings</button>
          <button onClick={() => setTab("permissions")}>Permissions</button>
        </nav>
      </header>
      <main>
        {tab === "companion" && (
          <div className="companion-grid">
            <AvatarPanel hudUrl={hud} onMic={setMicOn} />
            <ChatPanel apiBase={API} />
          </div>
        )}
        {tab === "settings" && <SettingsPanel apiBase={API} />}
        {tab === "permissions" && <PermissionsPanel />}
      </main>
    </div>
  );
}
