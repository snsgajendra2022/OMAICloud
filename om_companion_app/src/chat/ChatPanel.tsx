import { useState } from "react";

type Props = { apiBase: string };
type Msg = { role: "user" | "assistant"; text: string };

export function ChatPanel({ apiBase }: Props) {
  const [text, setText] = useState("");
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [busy, setBusy] = useState(false);

  async function send() {
    const q = text.trim();
    if (!q || busy) return;
    setBusy(true);
    setMsgs((m) => [...m, { role: "user", text: q }]);
    setText("");
    try {
      const res = await fetch(`${apiBase}/api/companion/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: q, session_id: "desktop-app" }),
      });
      const data = await res.json();
      const answer = data.answer || data.spoken || "(no reply)";
      setMsgs((m) => [...m, { role: "assistant", text: answer }]);
    } catch (e) {
      setMsgs((m) => [...m, { role: "assistant", text: `Error: ${e}` }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <h2>Conversation</h2>
      <div style={{ maxHeight: "50vh", overflow: "auto" }}>
        {msgs.map((m, i) => (
          <p key={i}>
            <strong>{m.role === "user" ? "You" : "OM"}:</strong> {m.text}
          </p>
        ))}
      </div>
      <textarea
        rows={3}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Talk to OM…"
        style={{ width: "100%" }}
      />
      <button type="button" disabled={busy} onClick={send}>
        {busy ? "Thinking…" : "Send"}
      </button>
    </section>
  );
}
