import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import ReactMarkdown from "react-markdown";
import "./styles.css";

const API_BASE = (import.meta.env.VITE_OM_API_URL || "http://127.0.0.1:8080").replace(/\/$/, "");
const API_KEY = import.meta.env.VITE_OM_API_KEY || "";
const STORAGE_KEY = "om-chat-conversations-v1";

function readSavedMessages() {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(value) ? value.filter((m) => ["user", "assistant"].includes(m.role) && typeof m.content === "string") : [];
  } catch {
    return [];
  }
}

function App() {
  const [messages, setMessages] = useState(readSavedMessages);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [model, setModel] = useState("OM-1.0");
  const [backend, setBackend] = useState("Your configured OM AI backend");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-80))); } catch { /* storage may be disabled */ }
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, busy]);

  async function sendMessage(event) {
    event?.preventDefault();
    const prompt = input.trim();
    if (!prompt || busy) return;
    const next = [...messages, { role: "user", content: prompt }];
    setMessages(next);
    setInput("");
    setError("");
    setBusy(true);
    try {
      const headers = { "Content-Type": "application/json" };
      if (API_KEY) headers.Authorization = `Bearer ${API_KEY}`;
      const response = await fetch(`${API_BASE}/v1/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          messages: next.slice(-30).map(({ role, content }) => ({ role, content })),
          model,
          max_new_tokens: 256,
          temperature: 0.7,
          top_p: 0.9,
          top_k: 50,
          repetition_penalty: 1.15
        })
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = typeof data.detail === "string" ? data.detail : `Request failed (${response.status})`;
        throw new Error(detail);
      }
      const answer = typeof data.reply === "string" ? data.reply.trim() : "";
      if (!answer) throw new Error("The OM API returned an empty response. Check the model checkpoint and server logs.");
      setBackend(data.provider ? `${data.provider} · ${data.model || model}` : data.om_backend || "OM AI");
      setMessages((current) => [...current, { role: "assistant", content: answer }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reach the OM AI server.");
    } finally {
      setBusy(false);
      inputRef.current?.focus();
    }
  }

  function newChat() {
    if (busy) return;
    setMessages([]);
    setError("");
    setInput("");
    try { localStorage.removeItem(STORAGE_KEY); } catch { /* storage may be disabled */ }
    inputRef.current?.focus();
  }

  const suggestions = [
    "Explain this code step by step",
    "Help me debug an error",
    "Create a React component",
    "Summarize the key idea"
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="OM AI home"><span className="brand-mark">OM</span><span><b>OM AI</b><small>Workspace chat</small></span></a>
        <button className="new-chat" onClick={newChat} disabled={busy}>＋ <span>New chat</span></button>
        <div className="side-label">MODEL</div>
        <label className="model-label" htmlFor="model-select">Active model</label>
        <select id="model-select" value={model} onChange={(e) => setModel(e.target.value)} disabled={busy}>
          <option value="OM-1.0">OM-1.0</option>
          <option value="OM-L1">OM Level 1</option>
          <option value="OM-L2">OM Level 2</option>
          <option value="OM-L3">OM Level 3</option>
          <option value="OM-L4">OM Level 4</option>
          <option value="OM-L5">OM Level 5</option>
        </select>
        <div className="sidebar-foot"><span className="status-dot" /> <span>API connection is checked on send</span></div>
      </aside>

      <main className="main-panel">
        <header className="topbar"><div><span className="mobile-mark">OM</span><strong>OM Chat</strong><span className="topbar-divider">/</span><span className="backend-label">{backend}</span></div><button className="clear-btn" onClick={newChat} disabled={busy}>New conversation</button></header>
        <section className={messages.length ? "conversation" : "conversation empty"}>
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-mark">OM</div>
              <p className="eyebrow">YOUR AI WORKSPACE</p>
              <h1>What can we work on?</h1>
              <p className="welcome-copy">Ask a question, explore an idea, or work through a coding problem with your configured OM AI backend.</p>
              <div className="suggestions">{suggestions.map((s) => <button key={s} onClick={() => { setInput(s); inputRef.current?.focus(); }} disabled={busy}>{s}<span>↗</span></button>)}</div>
            </div>
          ) : (
            <div className="message-list">
              {messages.map((message, index) => <article className={`message ${message.role}`} key={`${index}-${message.role}`}>
                <div className={`avatar ${message.role}`}>{message.role === "user" ? "Y" : "OM"}</div>
                <div className="message-body"><div className="message-author">{message.role === "user" ? "You" : "OM AI"}</div><div className="markdown"><ReactMarkdown>{message.content}</ReactMarkdown></div></div>
              </article>)}
              {busy && <article className="message assistant"><div className="avatar assistant">OM</div><div className="message-body"><div className="message-author">OM AI</div><div className="thinking"><span /><span /><span /> <small>Generating with your selected backend…</small></div></div></article>}
              <div ref={bottomRef} />
            </div>
          )}
        </section>
        <div className="composer-wrap">
          {error && <div className="error-banner" role="alert"><span>{error}</span><button onClick={() => setError("")} aria-label="Dismiss error">×</button></div>}
          <form className="composer" onSubmit={sendMessage}>
            <textarea ref={inputRef} value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }} placeholder="Message OM AI…" rows={1} disabled={busy} aria-label="Message OM AI" />
            <button className="send-btn" type="submit" disabled={busy || !input.trim()} aria-label="Send message">{busy ? <span className="spinner" /> : "↑"}</button>
          </form>
          <p className="disclaimer">OM AI uses the backend configured on your server. Responses depend on the active model and its trained checkpoint.</p>
        </div>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<React.StrictMode><App /></React.StrictMode>);
