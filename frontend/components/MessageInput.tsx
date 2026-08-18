"use client";

import { useState, useRef, KeyboardEvent } from "react";
import { ArrowUp } from "lucide-react";

export default function MessageInput({
  onSend,
  disabled,
}: {
  onSend: (text: string) => void;
  disabled: boolean;
}) {
  const [value, setValue] = useState("");
  const [focused, setFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const autoGrow = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 140) + "px";
  };

  return (
    <div
      className="flex items-end gap-2 rounded-2xl px-3 py-2 transition-[border-color,box-shadow] duration-200 focus-within:shadow-sm"
      style={{
        background: "var(--surface)",
        border: `1px solid ${focused ? "var(--accent)" : "var(--hairline)"}`,
        boxShadow: focused ? "0 0 0 3px var(--accent-soft)" : "none",
      }}
    >
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => {
          setValue(e.target.value);
          autoGrow();
        }}
        onKeyDown={handleKeyDown}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        placeholder="Ask a diagnostic reference question..."
        rows={1}
        disabled={disabled}
        aria-label="Message"
        className="flex-1 resize-none bg-transparent outline-none text-[15px] py-1.5 leading-relaxed disabled:opacity-60"
        style={{ color: "var(--ink)", maxHeight: 140 }}
      />
      <button
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        className="flex items-center justify-center w-9 h-9 rounded-full shrink-0 transition-all duration-200 enabled:hover:opacity-90 enabled:hover:scale-105 enabled:active:scale-95 disabled:opacity-30 focus-ring"
        style={{ background: "var(--accent)" }}
        aria-label="Send message"
      >
        <ArrowUp size={17} color="#fff" strokeWidth={2.25} />
      </button>
    </div>
  );
}