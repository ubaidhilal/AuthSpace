import { useCallback, useEffect, useRef, useState } from "react";
import {
  Bot, Check, Command, LogOut, Menu, MessageSquare, Plus, Send,
  Settings, ShieldCheck, Sparkles, UserRound, X, Zap, Trash2, Copy, Square, Plug, ExternalLink,
} from "lucide-react";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
const suggestions = [
  { icon: "✦", title: "Summarize my latest emails", text: "Summarize my latest emails and highlight anything that needs a reply." },
  { icon: "↗", title: "Help me organize my work", text: "Help me organize my work into a clear list of priorities." },
  { icon: "⌘", title: "What can you help me with?", text: "What can you help me with? Explain the integrations available to you." },
];

function GoogleMark() {
  return <svg viewBox="0 0 48 48" aria-hidden="true"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.72 7.18l7.63 5.91c4.45-4.1 7.13-10.15 7.13-17.56z"/><path fill="#FBBC05" d="M10.53 28.59A14.4 14.4 0 0 1 9.75 24c0-1.59.27-3.13.76-4.59l-7.98-6.2A23.9 23.9 0 0 0 0 24c0 3.87.93 7.52 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.9-5.79l-7.63-5.91c-2.12 1.42-4.84 2.26-8.27 2.26-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>;
}

function Login({ onLogin }) {
  return <main className="login-page"><div className="login-orb orb-one"/><div className="login-orb orb-two"/><header className="brand login-brand"><div className="brand-icon"><Sparkles size={19}/></div><span>authspace<span className="brand-dot">.</span></span></header><section className="login-layout"><div className="login-copy"><div className="eyebrow"><span className="status-dot"/> YOUR WORKSPACE, REIMAGINED</div><h1>Make room for<br/><span>what matters.</span></h1><p className="login-description">One intelligent workspace for your tools, ideas, and everyday work. Let your AI assistant take care of the busywork.</p><div className="feature-list"><div><span className="feature-icon"><Zap size={17}/></span><span><b>Work smarter</b><small>Get more done with your AI assistant</small></span></div><div><span className="feature-icon"><ShieldCheck size={17}/></span><span><b>Your space, secured</b><small>Secure sign-in with your Google account</small></span></div><div><span className="feature-icon"><Command size={17}/></span><span><b>Your tools, connected</b><small>Bring your everyday workflows together</small></span></div></div></div><div className="login-card"><div className="card-spark"><Sparkles size={23}/></div><h2>Welcome to AuthSpace</h2><p className="muted">Sign in to continue to your workspace.</p><button className="google-button" onClick={onLogin}><GoogleMark/><span>Continue with Google</span></button><div className="login-divider"><span/><small>QUICK & SECURE ACCESS</small><span/></div><div className="privacy-note"><ShieldCheck size={16}/><span>Your account is protected with Google's secure authentication.</span></div><div className="login-card-bottom"><span>Simple by design.</span><span>Built for your flow <Sparkles size={12}/></span></div></div></section><footer className="login-footer"><span>© 2026 AuthSpace</span><span><span className="footer-dot"/> Your personal AI workspace</span></footer></main>;
}

async function readError(response) {
  const raw = await response.text();
  try { const parsed = JSON.parse(raw); return parsed.detail || parsed.message || raw; } catch { return raw || `Request failed (${response.status})`; }
}


function AssistantMessage({ content }) {
  const authUrlMatch = content.match(/https:\/\/connect\.composio\.dev\/link\/[a-zA-Z0-9_-]+/);
  const authUrl = authUrlMatch?.[0];

  // Use the first known toolkit name mentioned in the response; otherwise use a generic label.
  const toolkitNames = [
    "Google Drive", "Google Calendar", "Google Sheets", "Google Docs",
    "GitHub", "Gmail", "Google", "Slack", "Notion", "Dropbox",
    "Microsoft Outlook", "Outlook", "Microsoft Teams", "Teams",
    "Linear", "Jira", "Trello", "Discord", "Salesforce", "HubSpot",
    "Airtable", "Asana", "Zoom", "LinkedIn", "X (Twitter)", "Twitter",
  ];
  const normalizedContent = content.toLowerCase();
  const toolkitName = toolkitNames.find((name) =>
    normalizedContent.includes(name.toLowerCase())
  ) || "your account";

  // Remove the raw authorization URL and Markdown link markup from visible message text.
  const visibleMessage = content
    .replace(/\\?\[([^\]]+)\]\(\s*\\?\[?(https:\/\/connect\.composio\.dev\/link\/[a-zA-Z0-9_-]+)\]?\s*\)/g, "$1")
    .replace(/https:\/\/connect\.composio\.dev\/link\/[a-zA-Z0-9_-]+/g, "")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, "$1")
    .replace(/\\([()[\]])/g, "$1")
    .trim();

  return (
    <div className="assistant-message">
      {visibleMessage && <div className="message-text">{visibleMessage}</div>}
      {authUrl && (
        <div className="connection-card">
          <div className="connection-card-title">
            <Plug size={18} aria-hidden="true" />
            Connect {toolkitName}
          </div>
          <div className="connection-card-description">
            Authorize {toolkitName === "your account" ? "this integration" : toolkitName} to let your assistant access the connected service.
          </div>
          <a
            className="connect-button"
            href={authUrl}
            target="_blank"
            rel="noopener noreferrer"
          >
            <Plug size={17} aria-hidden="true" />
            Connect {toolkitName === "your account" ? "account" : toolkitName}
            <ExternalLink size={14} aria-hidden="true" />
          </a>
          <div className="connection-card-description">
            Complete authorization in the opened page. This link may expire.
          </div>
        </div>
      )}
    </div>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [history, setHistory] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [activeTitle, setActiveTitle] = useState("New conversation");
  const textareaRef = useRef(null);
  const bottomRef = useRef(null);
  const abortRef = useRef(null);

  const checkAuth = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/me`, { credentials: "include" });
      if (!response.ok) throw new Error("Not signed in");
      const data = await response.json();
      setUser(data.user);
    } catch { setUser(null); }
    finally { setAuthLoading(false); }
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/conversations`, { credentials: "include" });
      if (response.status === 401) { setUser(null); return; }
      if (!response.ok) throw new Error(await readError(response));
      const data = await response.json();
      setHistory(data.conversations || []);
    } catch (e) { setError(e.message || "Could not load conversation history."); }
  }, []);

  useEffect(() => { checkAuth(); }, [checkAuth]);
  useEffect(() => { if (user) loadHistory(); }, [user, loadHistory]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);
  // Grow the composer as the user types, up to a comfortable limit.
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    const maxHeight = 220;
    textarea.style.height = `${Math.min(textarea.scrollHeight, maxHeight)}px`;
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? "auto" : "hidden";
  }, [input]);
  useEffect(() => () => abortRef.current?.abort(), []);

  const login = () => { window.location.assign(`${API_BASE}/google/login`); };
  const logout = async () => {
    abortRef.current?.abort();
    try { await fetch(`${API_BASE}/google/logout`, { method: "POST", credentials: "include" }); }
    finally { setUser(null); setMessages([]); setHistory([]); setConversationId(null); setInput(""); }
  };
  const newChat = () => {
    if (sending) abortRef.current?.abort();
    setMessages([]); setConversationId(null); setInput(""); setError(""); setActiveTitle("New conversation"); setSending(false);
    textareaRef.current?.focus();
  };

  const openConversation = async (item) => {
    if (sending) abortRef.current?.abort();
    setSending(false); setError("");
    try {
      const response = await fetch(`${API_BASE}/conversations/${item.id}`, { credentials: "include" });
      if (!response.ok) throw new Error(await readError(response));
      const data = await response.json();
      setConversationId(data.id); setActiveTitle(data.title); setMessages(data.messages.map(({role, content, id}) => ({id, role, content, streaming: false})));
    } catch (e) { setError(e.message || "Could not open conversation."); }
  };

  const deleteConversation = async (event, item) => {
    event.stopPropagation();
    try {
      const response = await fetch(`${API_BASE}/conversations/${item.id}`, { method: "DELETE", credentials: "include" });
      if (!response.ok) throw new Error(await readError(response));
      setHistory(old => old.filter(row => row.id !== item.id));
      if (conversationId === item.id) newChat();
    } catch (e) { setError(e.message || "Could not delete conversation."); }
  };

  const sendMessage = async (text = input) => {
    const question = text.trim();
    if (!question || sending) return;
    setError(""); setInput(""); setSending(true); setActiveTitle(question.slice(0, 60));
    setMessages(old => [...old, { role: "user", content: question }, { role: "assistant", content: "", streaming: true }]);
    const controller = new AbortController(); abortRef.current = controller;
    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST", credentials: "include", signal: controller.signal,
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify({ question, conversation_id: conversationId }),
      });
      if (!response.ok) {
        const detail = await readError(response);
        if (response.status === 401) { setUser(null); throw new Error("Your session expired. Please sign in again."); }
        throw new Error(detail);
      }
      if (!response.body) throw new Error("Streaming is not supported by this browser.");
      const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = "";
      const handleEvent = (rawEvent) => {
        const lines = rawEvent.split("\n");
        const eventName = lines.find(line => line.startsWith("event:"))?.slice(6).trim();
        const dataLine = lines.find(line => line.startsWith("data:"))?.slice(5).trim();
        if (!eventName || !dataLine) return;
        let data; try { data = JSON.parse(dataLine); } catch { return; }
        if (eventName === "token") setMessages(old => old.map((m, i) => i === old.length - 1 ? { ...m, content: m.content + (data.delta || "") } : m));
        if (eventName === "done") { setConversationId(data.conversation_id); }
        if (eventName === "error") setError(data.message || "The assistant could not complete this request.");
      };
      while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
        const events = buffer.split("\n\n"); buffer = events.pop() || ""; events.forEach(handleEvent);
        if (done) break;
      }
      if (buffer.trim()) handleEvent(buffer);
      setMessages(old => old.map((m, i) => i === old.length - 1 ? { ...m, streaming: false } : m));
      await loadHistory();
    } catch (e) {
      if (e.name !== "AbortError") setError(e.message || "Something went wrong. Please try again.");
      setMessages(old => old.map((m, i) => i === old.length - 1 ? { ...m, streaming: false } : m));
    } finally { setSending(false); abortRef.current = null; textareaRef.current?.focus(); }
  };

  const handleSubmit = e => { e.preventDefault(); sendMessage(); };
  const handleKeyDown = e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSubmit(e); } };
  const copyMessage = async content => { try { await navigator.clipboard.writeText(content); } catch { setError("Clipboard access was blocked by the browser."); } };

  if (authLoading) return <main className="loading-screen"><div className="loading-mark"><Sparkles size={23}/></div><div className="loading-spinner"/><p>Preparing your workspace...</p></main>;
  if (!user) return <Login onLogin={login}/>;
  const displayName = user.name || user.email?.split("@")[0] || "User";
  const initials = displayName.split(/\s+/).map(x => x[0]).join("").slice(0, 2).toUpperCase();

  return <div className="app-shell">
    {sidebarOpen && <aside className="sidebar"><div className="sidebar-top"><a className="brand" href="#" onClick={e => e.preventDefault()}><div className="brand-icon"><Sparkles size={18}/></div><span>authspace<span className="brand-dot">.</span></span></a><button className="icon-button sidebar-close" aria-label="Close sidebar" onClick={() => setSidebarOpen(false)}><X size={18}/></button></div>
      <button className="new-chat-button" onClick={newChat}><Plus size={17}/><span>New conversation</span><kbd>⌘ K</kbd></button>
      <div className="sidebar-section"><span className="sidebar-label">WORKSPACE</span><button className="nav-item active"><MessageSquare size={17}/><span>AI Assistant</span><span className="nav-live"/></button><button className="nav-item" onClick={() => setError("Settings will be available here soon.")}><Settings size={17}/><span>Settings</span></button></div>
      <div className="history-section"><span className="sidebar-label">RECENT CONVERSATIONS</span>{history.length ? history.map(item => <div className={`history-row ${conversationId === item.id ? "selected" : ""}`} key={item.id}><button className="history-item" onClick={() => openConversation(item)} title={item.title}><MessageSquare size={15}/><span>{item.title}</span></button><button className="history-delete" aria-label={`Delete ${item.title}`} title="Delete conversation" onClick={e => deleteConversation(e, item)}><Trash2 size={14}/></button></div>) : <div className="empty-history"><div className="history-art"><MessageSquare size={20}/></div><p>Your conversations<br/>will show up here.</p></div>}</div>
      <div className="sidebar-bottom"><div className="upgrade-card"><div className="upgrade-icon"><Sparkles size={16}/></div><b>A little more magic</b><p>Connect your tools and let your assistant do more.</p><span className="coming-soon">YOUR AI WORKSPACE</span></div><button className="user-menu" onClick={logout}><div className="user-avatar">{initials}</div><div className="user-details"><b>{displayName}</b><small>{user.email}</small></div><LogOut size={16}/></button></div>
    </aside>}
    <main className="main-panel"><header className="topbar"><div className="topbar-left">{!sidebarOpen && <button className="icon-button" aria-label="Open sidebar" onClick={() => setSidebarOpen(true)}><Menu size={18}/></button>}<div className="breadcrumb"><span>Workspace</span><span className="breadcrumb-sep">/</span><b>{activeTitle}</b></div></div><div className="topbar-right"><span className="secure-label"><ShieldCheck size={14}/> Secure workspace</span><div className="top-avatar">{initials}</div></div></header>
      <div className="chat-area">{messages.length === 0 ? <section className="welcome-screen"><div className="welcome-icon"><Sparkles size={24}/></div><div className="eyebrow"><span className="status-dot"/> YOUR AI WORKSPACE</div><h1>What can I help you<br/><span>get done today?</span></h1><p className="welcome-subtitle">Your tools, ideas, and workflows — all in one place.</p><div className="suggestion-grid">{suggestions.map(s => <button className="suggestion-card" key={s.title} onClick={() => sendMessage(s.text)}><span className="suggestion-icon">{s.icon}</span><b>{s.title}</b><span>{s.text}</span><span className="suggestion-arrow">↗</span></button>)}</div></section> : <section className="messages-list" aria-live="polite">{messages.map((m, i) => <article className={`message-row ${m.role}`} key={m.id || `${i}-${m.role}`}><div className={`message-avatar ${m.role}`}>{m.role === "assistant" ? <Sparkles size={16}/> : initials}</div><div className="message-content"><div className="message-author">{m.role === "assistant" ? "AuthSpace AI" : "You"}</div>{m.role === "assistant" && m.content ? (
              <>
                <AssistantMessage content={m.content} />
                {m.streaming && <span className="stream-cursor" />}
              </>
            ) : (
              <div className="message-text">
                {m.content || (m.streaming ? <span className="typing"><i/><i/><i/></span> : "")}
              </div>
            )}{m.role === "assistant" && m.content && !m.streaming && <button className="copy-response" onClick={() => copyMessage(m.content)} aria-label="Copy response"><Copy size={14}/> Copy</button>}</div></article>)}<div ref={bottomRef}/></section>}{error && <div className="error-banner" role="alert"><span>{error}</span><button onClick={() => setError("")} aria-label="Dismiss error"><X size={15}/></button></div>}</div>
      <div className="composer-wrap"><form className="composer" onSubmit={handleSubmit}><textarea ref={textareaRef} value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown} placeholder="Message your assistant..." rows={1} aria-label="Message your assistant" disabled={sending}/><div className="composer-footer"><div className="composer-hint"><span className="hint-sparkle">✦</span> AI assistant <span className="hint-divider">·</span><span>Enter to send</span></div><div className="composer-actions">{sending && <button type="button" className="stop-button" aria-label="Stop generating" onClick={() => abortRef.current?.abort()}><Square size={14}/></button>}<button type="submit" className="send-button" disabled={!input.trim() || sending} aria-label="Send message">{sending ? <span className="send-loader"/> : <Send size={16}/>}</button></div></div></form><p className="disclaimer">AI can make mistakes. Check important information before you act.</p></div>
    </main>
  </div>;
}

export default App;
