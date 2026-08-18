export default function PulseLoader({ stage }: { stage: string }) {
  return (
    <div className="flex items-center gap-3 py-1">
      <svg width="64" height="24" viewBox="0 0 120 24" fill="none">
        <path
          className="ecg-line"
          d="M0 12 H30 L36 4 L42 20 L48 12 H60 L66 2 L72 22 L78 12 H120"
          stroke="var(--accent)"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span
        className="text-[11px] uppercase tracking-[0.12em]"
        style={{ fontFamily: "var(--font-mono)", color: "var(--ink-muted)" }}
      >
        {stage}
      </span>
    </div>
  );
}