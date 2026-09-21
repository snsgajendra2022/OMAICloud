type Props = { apiBase: string };

export function SettingsPanel({ apiBase }: Props) {
  return (
    <section className="panel" style={{ margin: "1rem" }}>
      <h2>Settings</h2>
      <p>API: {apiBase}</p>
      <p>Voice: Aman (macOS) via companion TTS</p>
      <p>Wake word: optional (Porcupine / phrase)</p>
      <p>Start with OS: enable in Tauri system tray config</p>
    </section>
  );
}
