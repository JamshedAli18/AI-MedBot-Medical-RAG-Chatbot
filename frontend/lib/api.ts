import { getToken } from "./auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface StreamHandlers {
  onStage: (stage: string) => void;
  onToken: (text: string) => void;
  onDone: (finalAnswer: string) => void;
  onError: (message: string) => void;
  onUnauthorized?: () => void;
}

export async function streamChat(message: string, sessionId: string, handlers: StreamHandlers): Promise<void> {
  const token = getToken();

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
  } catch {
    handlers.onError("Couldn't reach the server. Check your connection and try again.");
    return;
  }

  if (res.status === 401) {
    handlers.onUnauthorized?.();
    return;
  }

  if (!res.ok || !res.body) {
    handlers.onError("The server returned an unexpected response.");
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const events = buffer.split("\n\n");
    buffer = events.pop() || "";

    for (const raw of events) {
      if (!raw.trim()) continue;
      let eventType = "message";
      let data = "";
      for (const line of raw.split("\n")) {
        if (line.startsWith("event:")) eventType = line.slice(6).trim();
        else if (line.startsWith("data:")) data = line.slice(5).trim();
      }
      if (!data) continue;

      try {
        const parsed = JSON.parse(data);
        if (eventType === "stage") handlers.onStage(parsed.stage);
        else if (eventType === "token") handlers.onToken(parsed.text);
        else if (eventType === "done") handlers.onDone(parsed.final_answer);
        else if (eventType === "error") handlers.onError(parsed.message);
      } catch {
        // ignore malformed SSE fragment
      }
    }
  }
}
