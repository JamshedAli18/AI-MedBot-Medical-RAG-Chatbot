"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Message, { ChatMessage } from "./Message";
import MessageInput from "./MessageInput";
import SessionSidebar from "./SessionSidebar";
import { streamChat } from "@/lib/api";
import { isLoggedIn, getIdentityType, clearToken } from "@/lib/auth";
import { createSession, listSessions, getSessionMessages, SessionSummary } from "@/lib/sessions";
import { Activity, LogOut, Menu } from "lucide-react";

function uid() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

const GUEST_LIMIT_PHRASE = "reached the 10-question limit";
const SESSION_LIMIT_PHRASE = "reached its 20-question limit";

const WELCOME: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "Hello — I'm MedBot, a diagnostic reference assistant grounded in *A System of Diagnosis in Outline*. Ask me about symptom analysis, site localization, or diagnostic reasoning for a given system.",
};

export default function ChatWindow() {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [identityType, setIdentityType] = useState<string | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME]);
  const [ephemeralSessionId] = useState<string>(() => uid()); // guests only
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [limitReached, setLimitReached] = useState<"guest" | "session" | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const isRegisteredUser = identityType === "user";

  const loadSessions = useCallback(async () => {
    const list = await listSessions();
    setSessions(list);
    return list;
  }, []);

  const switchToSession = useCallback(async (sessionId: string) => {
    setLimitReached(null);
    const data = await getSessionMessages(sessionId);
    setActiveSessionId(sessionId);
    if (data.messages.length === 0) {
      setMessages([WELCOME]);
    } else {
      setMessages(
        data.messages.map((m) => ({
          id: uid(),
          role: m.role,
          content: m.content,
        }))
      );
    }
  }, []);

  const handleNewChat = useCallback(async () => {
    const created = await createSession();
    await loadSessions();
    setActiveSessionId(created.id);
    setMessages([WELCOME]);
    setLimitReached(null);
  }, [loadSessions]);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/login");
      return;
    }
    const type = getIdentityType();
    setIdentityType(type);

    (async () => {
      if (type === "user") {
        const list = await loadSessions();
        if (list.length === 0) {
          await handleNewChat();
        } else {
          await switchToSession(list[0].id);
        }
      }
      setReady(true);
    })();
  }, [router, loadSessions, handleNewChat, switchToSession]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleLogout = () => {
    clearToken();
    router.replace("/login");
  };

  const handleDeletedSession = async (deletedId: string) => {
    const list = await loadSessions();
    if (deletedId === activeSessionId) {
      if (list.length > 0) {
        await switchToSession(list[0].id);
      } else {
        await handleNewChat();
      }
    }
  };

  const handleSend = async (text: string) => {
    if (isStreaming || limitReached) return;
    const sessionId = isRegisteredUser ? activeSessionId : ephemeralSessionId;
    if (!sessionId) return;

    const userMsg: ChatMessage = { id: uid(), role: "user", content: text };
    const assistantId = uid();
    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      streaming: true,
      stage: "Thinking",
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsStreaming(true);

    let accumulated = "";
    const updateAssistant = (patch: Partial<ChatMessage>) => {
      setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, ...patch } : m)));
    };

    await streamChat(text, sessionId, {
      onStage: (stage) => updateAssistant({ stage }),
      onToken: (chunk) => {
        accumulated += chunk;
        updateAssistant({ content: accumulated });
      },
      onDone: (finalAnswer) => {
        updateAssistant({ content: finalAnswer, streaming: false, stage: undefined });
        if (finalAnswer.includes(GUEST_LIMIT_PHRASE)) setLimitReached("guest");
        else if (finalAnswer.includes(SESSION_LIMIT_PHRASE)) setLimitReached("session");
        else if (isRegisteredUser) loadSessions(); // refresh sidebar (title/order may have changed)
      },
      onError: (message) => {
        updateAssistant({ content: message, streaming: false, isError: true, stage: undefined });
      },
      onUnauthorized: () => {
        clearToken();
        router.replace("/login");
      },
    });

    setIsStreaming(false);
  };

  if (!ready) {
    return (
      <div className="flex h-screen w-full items-center justify-center" style={{ background: "var(--bg)" }}>
        <div className="pop-in flex flex-col items-center gap-3">
          <div
            className="flex items-center justify-center w-11 h-11 rounded-full animate-pulse"
            style={{ background: "var(--accent-soft)" }}
          >
            <Activity size={20} color="var(--accent)" strokeWidth={2.25} />
          </div>
          <p
            className="text-[11px] uppercase tracking-[0.1em]"
            style={{ fontFamily: "var(--font-mono)", color: "var(--ink-muted)" }}
          >
            Loading MedBot&hellip;
          </p>
        </div>
      </div>
    );
  }

  const chatArea = (
    <div className="flex flex-col h-screen flex-1 min-w-0">
      <header
        className="flex items-center justify-between gap-3 px-4 py-4 shrink-0 sm:px-5"
        style={{ borderBottom: "1px solid var(--hairline)" }}
      >
        <div className="flex items-center gap-2 min-w-0 sm:gap-3">
          {isRegisteredUser && (
            <button
              onClick={() => setSidebarOpen(true)}
              aria-label="Open chat list"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-colors duration-200 hover:bg-black/5 sm:hidden focus-ring"
            >
              <Menu size={18} color="var(--ink)" />
            </button>
          )}
          <div
            className="flex items-center justify-center w-9 h-9 rounded-full shrink-0"
            style={{ background: "var(--accent-soft)" }}
          >
            <Activity size={18} color="var(--accent)" strokeWidth={2.25} />
          </div>
          <div className="min-w-0">
            <h1 className="text-[15px] font-semibold leading-none truncate">MedBot</h1>
            <p
              className="text-[11px] mt-1 uppercase tracking-[0.08em] truncate"
              style={{ fontFamily: "var(--font-mono)", color: "var(--ink-muted)" }}
            >
              {identityType === "guest" ? "Guest session" : "Diagnostic reference assistant"}
            </p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex shrink-0 items-center gap-1.5 text-[12.5px] px-2.5 py-1.5 rounded-lg transition-colors duration-200 hover:bg-black/5 focus-ring"
          style={{ color: "var(--ink-muted)" }}
        >
          <LogOut size={14} />
          <span className="hidden sm:inline">{identityType === "guest" ? "Exit" : "Log out"}</span>
        </button>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto scroll-thin px-4 py-6 space-y-4 max-w-190 w-full mx-auto sm:px-5">
        {messages.map((m) => (
          <Message key={m.id} message={m} />
        ))}

        {limitReached === "guest" && (
          <div
            className="pop-in rounded-2xl px-4 py-3.5 flex flex-col items-center text-center gap-2.5"
            style={{ background: "var(--accent-soft)", border: "1px solid rgba(47,111,98,0.2)" }}
          >
            <p className="text-[13.5px]" style={{ color: "var(--ink)" }}>
              You&rsquo;ve used all 10 guest questions. Sign up for free to keep chatting with no limit.
            </p>
            <button
              onClick={() => { clearToken(); router.push("/login"); }}
              className="rounded-lg px-4 py-2 text-[13px] font-medium text-white transition-all duration-200 hover:opacity-90 active:scale-[0.98] focus-ring"
              style={{ background: "var(--accent)" }}
            >
              Sign up now
            </button>
          </div>
        )}

        {limitReached === "session" && (
          <div
            className="pop-in rounded-2xl px-4 py-3.5 flex flex-col items-center text-center gap-2.5"
            style={{ background: "var(--tag-soft)", border: "1px solid rgba(169,120,46,0.2)" }}
          >
            <p className="text-[13.5px]" style={{ color: "var(--ink)" }}>
              This chat has reached its 20-question limit.
            </p>
            <button
              onClick={handleNewChat}
              className="rounded-lg px-4 py-2 text-[13px] font-medium text-white transition-all duration-200 hover:opacity-90 active:scale-[0.98] focus-ring"
              style={{ background: "var(--tag)" }}
            >
              Start a new chat
            </button>
          </div>
        )}
      </div>

      <div className="px-4 pb-5 pt-2 shrink-0 max-w-190 w-full mx-auto sm:px-5">
        <MessageInput onSend={handleSend} disabled={isStreaming || !!limitReached} />
        <p className="text-center text-[10.5px] mt-2.5" style={{ color: "var(--ink-muted)" }}>
          Reference information only — not a substitute for professional medical care.
        </p>
      </div>
    </div>
  );

  if (!isRegisteredUser) {
    return <div className="flex" style={{ background: "var(--bg)" }}>{chatArea}</div>;
  }

  return (
    <div className="flex" style={{ background: "var(--bg)" }}>
      <SessionSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelect={(id) => { switchToSession(id); setSidebarOpen(false); }}
        onNewChat={() => { handleNewChat(); setSidebarOpen(false); }}
        onDeleted={handleDeletedSession}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      {chatArea}
    </div>
  );
}
