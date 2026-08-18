"use client";

import { useState } from "react";
import { Plus, Trash2, MessageSquare, X } from "lucide-react";
import { SessionSummary, deleteSession } from "@/lib/sessions";

export default function SessionSidebar({
  sessions,
  activeSessionId,
  onSelect,
  onNewChat,
  onDeleted,
  open,
  onClose,
}: {
  sessions: SessionSummary[];
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDeleted: (id: string) => void;
  open: boolean;
  onClose: () => void;
}) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setDeletingId(id);
    try {
      await deleteSession(id);
      onDeleted(id);
    } catch {
      // silently ignore — sidebar just won't update if it failed
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <>
      <div
        onClick={onClose}
        aria-hidden="true"
        className={`fixed inset-0 z-40 bg-black/40 transition-opacity duration-300 sm:hidden ${
          open ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
      />
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex h-screen w-72 shrink-0 flex-col transition-transform duration-300 ease-out sm:static sm:z-auto sm:w-64 sm:translate-x-0 sm:transition-none ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
        style={{ background: "var(--surface)", borderRight: "1px solid var(--hairline)" }}
      >
        <div className="flex items-center gap-2 p-3">
          <button
            onClick={onNewChat}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg py-2.5 text-[13.5px] font-medium text-white transition-all duration-200 hover:opacity-90 active:scale-[0.98] focus-ring"
            style={{ background: "var(--accent)" }}
          >
            <Plus size={15} /> New chat
          </button>
          <button
            onClick={onClose}
            aria-label="Close sidebar"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-colors duration-200 hover:bg-black/5 sm:hidden focus-ring"
          >
            <X size={17} color="var(--ink-muted)" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto scroll-thin px-2 pb-3">
          {sessions.length === 0 && (
            <p className="text-[12.5px] px-2.5 py-2" style={{ color: "var(--ink-muted)" }}>
              No chats yet — start one above.
            </p>
          )}
          {sessions.map((s) => (
            <div
              key={s.id}
              onClick={() => onSelect(s.id)}
              className="group flex items-center gap-2 rounded-lg px-2.5 py-2.5 mb-1 cursor-pointer transition-colors duration-150 hover:bg-black/[0.03]"
              style={{
                background: s.id === activeSessionId ? "var(--accent-soft)" : "transparent",
              }}
            >
              <MessageSquare
                size={14}
                color={s.id === activeSessionId ? "var(--accent)" : "var(--ink-muted)"}
                className="shrink-0"
              />
              <span
                className="flex-1 text-[13px] truncate"
                style={{ color: s.id === activeSessionId ? "var(--ink)" : "var(--ink-muted)" }}
              >
                {s.title}
              </span>
              <button
                onClick={(e) => handleDelete(e, s.id)}
                disabled={deletingId === s.id}
                aria-label="Delete chat"
                className="shrink-0 rounded p-1 opacity-0 transition-opacity duration-150 group-hover:opacity-100 hover:bg-black/5 focus-ring focus-visible:opacity-100"
              >
                <Trash2 size={13} color="var(--ink-muted)" />
              </button>
            </div>
          ))}
        </div>
      </aside>
    </>
  );
}
