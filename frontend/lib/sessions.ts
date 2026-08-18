import { getToken } from "./auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface SessionSummary {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface SessionMessage {
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

function authHeaders() {
  const token = getToken();
  return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
}

export async function createSession(): Promise<{ id: string; title: string }> {
  const res = await fetch(`${API_BASE}/sessions`, { method: "POST", headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function listSessions(): Promise<SessionSummary[]> {
  const res = await fetch(`${API_BASE}/sessions`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to list sessions");
  return res.json();
}

export async function getSessionMessages(sessionId: string): Promise<{ id: string; title: string; messages: SessionMessage[] }> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/messages`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load session");
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, { method: "DELETE", headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to delete session");
}
