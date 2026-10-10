import { KeyboardEvent, useEffect, useRef, useState } from "react";

type Props = { apiBase: string };
type Msg = { role: "user" | "assistant"; text: string; failed?: boolean };

export function ChatPanel({ apiBase }: Props) {
  const [text, setText] = useState("");
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sessionId] = useState(() => `desktop-${Date.now().toString(36)}`);
  const transcriptRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = transcriptRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [msgs, busy]);

  async function sendMessage(raw: string, retryIndex?: number) {
    const question = raw.trim();
    if (!question || busy) return;
    setBusy(true);
    setError("");
    if (retryIndex === undefined) {
      setMsgs((current) => [...current, { role: "user", text: question }]);
      setText("");
    }
    try {
      const controller = new AbortController();
      const timeout = window.setTimeout(() => controller.abort(), 120_000);
      let response: Response;
      try {
        response = await fetch(`${apiBase.replace(/\/$/, "")}/api/companion/message`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({ text: question, session_id: sessionId }),
          signal: controller.signal,
        });
      } finally {
        window.clearTimeout(timeout);
      }
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = typeof data.detail === "string" ? data.detail : `Request failed (${response.status})`;
        throw new Error(detail);
      }
      const answer = [data.answer, data.spoken, data.message].find(
        (value) => typeof value === "string" && value.trim()
      );
      if (!answer) throw new Error("OM returned an empty response. Check the active model and server logs.");
      setMsgs((current) => retryIndex === undefined
        ? [...current, { role: "assistant", text: answer }]
        : current.map((message, index) => index === retryIndex ? { role: "assistant", text: answer } : message));
    } catch (err) {
      const message = err instanceof Error
        ? (err.name === "AbortError" ? "OM took too long to respond. Please try again." : err.message)
        : "Could not reach OM. Check that the API server is running.";
      setError(message);
      setMsgs((current) => retryIndex === undefined
        ? [...current, { role: "assistant", text: message, failed: true }]
        : current.map((item, index) => index === retryIndex ? { role: "assistant", text: message, failed: true } : item));
    } finally {
      setBusy(false);
    }
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void sendMessage(text);
    }
  }

  function clearChat() {
    if (busy) return;
    setMsgs([]);
    setError("");
    inputRef.current?.focus();
  }

  return (
    <section className="panel chat-panel" aria-label="OM conversation">
      <header className="chat-heading">
        <div>
          <div className="eyebrow">OM AI · NATIVE COMPANION</div>
          <h2>Conversation</h2>
          <p className="chat-subtitle">Ask a question, explore an idea, or work through a task.</p>
        </div>
        <div className="chat-actions">
          <span className={`connection-pill ${busy ? "working" : "idle"}`}>
            <span className="status-dot" />{busy ? "Thinking" : "Ready"}
          </span>
          <button className="secondary-button" type="button" onClick={clearChat} disabled={busy || msgs.length === 0}>
            Clear
          </button>
        </div>
      </header>

      <div className={`transcript ${msgs.length ? "" : "transcript-empty"}`} ref={transcriptRef} aria-live="polite" aria-busy={busy}>
        {msgs.length === 0 ? (
          <div className="welcome">
            <div className="welcome-mark">OM</div>
            <h3>What can we work on?</h3>
            <p>Start with a question. OM will respond using the model and tools configured on your server.</p>
            <div className="suggestions">
              {["Explain a difficult topic simply", "Help me debug Python code", "Make a practical learning plan"].map((suggestion) => (
                <button key={suggestion} type="button" onClick={() => { setText(suggestion); inputRef.current?.focus(); }}>
                  <span>{suggestion}</span><span aria-hidden="true">↗</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="message-list">
            {msgs.map((message, index) => (
              <article className={`message ${message.role} ${message.failed ? "message-failed" : ""}`} key={`${index}-${message.role}`}>
                <div className="message-avatar">{message.role === "user" ? "Y" : "OM"}</div>
                <div className="message-body">
                  <div className="message-author">{message.role === "user" ? "You" : "OM AI"}</div>
                  <div className="message-text">{message.text}</div>
                  {message.failed && index > 0 && (
                    <button className="retry-button" type="button" disabled={busy} onClick={() => {
                      const previousUser = [...msgs.slice(0, index)].reverse().find((item) => item.role === "user");
                      if (previousUser) void sendMessage(previousUser.text, index);
                    }}>Try again</button>
                  )}
                </div>
              </article>
            ))}
            {busy && <div className="thinking-row"><span className="thinking-dots"><i /><i /><i /></span><span>OM is working on your response…</span></div>}
          </div>
        )}
      </div>

      {error && <div className="chat-error" role="alert">{error}</div>}
      <form className="composer" onSubmit={(event) => { event.preventDefault(); void sendMessage(text); }}>
        <textarea
          ref={inputRef}
          rows={2}
          value={text}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Message OM…"
          aria-label="Message OM"
          disabled={busy}
          maxLength={20000}
        />
        <div className="composer-footer">
          <span>Enter to send · Shift + Enter for a new line</span>
          <button className="send-button" type="submit" disabled={busy || !text.trim()}>
            {busy ? "Working…" : "Send"} <span aria-hidden="true">↑</span>
          </button>
        </div>
      </form>
      <p className="chat-disclaimer">OM can make mistakes. Verify important information.</p>
    </section>
  );
}
