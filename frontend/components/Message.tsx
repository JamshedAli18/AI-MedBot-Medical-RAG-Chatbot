import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import PulseLoader from "./PulseLoader";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
  stage?: string;
  isError?: boolean;
}

function parseAnswer(text: string) {
  const sourcesMatch = text.split(/\n\n\*\*Sources:\*\*\n/);
  const main = sourcesMatch[0];
  let citations: string[] = [];
  let disclaimer = "";

  if (sourcesMatch[1]) {
    const discMatch = sourcesMatch[1].split(/\n\n_/);
    citations = discMatch[0]
      .split("\n")
      .map((l) => l.replace(/^- /, "").trim())
      .filter(Boolean);
    if (discMatch[1]) disclaimer = "_" + discMatch[1];
  }

  return { main, citations, disclaimer };
}

export default function Message({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="pop-in flex justify-end">
        <div
          className="max-w-[85%] rounded-2xl rounded-tr-sm px-4 py-2.5 text-[15px] leading-relaxed sm:max-w-[75%]"
          style={{ background: "var(--accent)", color: "#fff", boxShadow: "0 1px 2px rgba(20,36,32,0.12)" }}
        >
          {message.content}
        </div>
      </div>
    );
  }

  if (message.streaming && !message.content) {
    return (
      <div className="pop-in flex justify-start">
        <div
          className="max-w-[85%] rounded-2xl rounded-tl-sm px-4 py-3 sm:max-w-[80%]"
          style={{ background: "var(--surface)", border: "1px solid var(--hairline)", boxShadow: "0 1px 2px rgba(20,36,32,0.04)" }}
        >
          <PulseLoader stage={message.stage || "Thinking"} />
        </div>
      </div>
    );
  }

  const { main, citations, disclaimer } = parseAnswer(message.content);

  return (
    <div className="pop-in flex justify-start">
      <div
        className="max-w-[85%] rounded-2xl rounded-tl-sm px-4 py-3 sm:max-w-[80%]"
        style={{
          background: message.isError ? "var(--alert-soft)" : "var(--surface)",
          border: `1px solid ${message.isError ? "var(--alert)" : "var(--hairline)"}`,
          boxShadow: message.isError ? "none" : "0 1px 2px rgba(20,36,32,0.04)",
        }}
      >
        <div className="md-content text-[15px]" style={{ color: "var(--ink)" }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{main}</ReactMarkdown>
        </div>

        {citations.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {citations.map((c, i) => (
              <span
                key={i}
                className="rounded px-2 py-1 text-[11px] leading-none"
                style={{
                  background: "var(--tag-soft)",
                  color: "var(--tag)",
                  fontFamily: "var(--font-mono)",
                  border: "1px solid rgba(169,120,46,0.25)",
                }}
              >
                {c}
              </span>
            ))}
          </div>
        )}

        {disclaimer && (
          <p
            className="mt-3 text-[12px] italic"
            style={{ color: "var(--ink-muted)" }}
          >
            {disclaimer.replace(/^_|_$/g, "")}
          </p>
        )}

        {message.streaming && message.content && (
          <span className="inline-block w-1.5 h-4 ml-0.5 align-middle animate-pulse" style={{ background: "var(--accent)" }} />
        )}
      </div>
    </div>
  );
}