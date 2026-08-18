import Link from "next/link";
import { Activity, ShieldCheck } from "lucide-react";

const SEPD = [
  { letter: "S", label: "Site" },
  { letter: "E", label: "Etiology" },
  { letter: "P", label: "Pathophysiology" },
  { letter: "D", label: "Dysfunction" },
];

const CITATIONS = [
  "p. 214 · Cardiovascular system · Etiology",
  "p. 87 · Respiratory disease · Site",
  "p. 332 · Renal disorders · Dysfunction",
  "p. 156 · Infectious disease · Pathophysiology",
];

const CONSOLE_LINES = [
  "> identity: administrator",
  "> session: not authenticated",
  "> access: pending verification",
];

export default function AuthPanel({ variant }: { variant: "user" | "admin" }) {
  if (variant === "admin") {
    return (
      <div
        className="relative isolate hidden h-full flex-col justify-between overflow-hidden p-10 lg:flex"
        style={{ background: "var(--ink)" }}
      >
        <div className="auth-grid auth-grid-dark pointer-events-none absolute inset-0 -z-10" aria-hidden="true" />
        <div
          className="scanlines pointer-events-none absolute inset-0 -z-10"
          aria-hidden="true"
        />
        <div
          className="aurora-blob -right-24 -top-24 -z-10"
          style={{ background: "rgba(169,120,46,0.35)" }}
          aria-hidden="true"
        />

        <Link href="/" className="focus-ring inline-flex w-fit items-center gap-2.5 rounded-md">
          <div
            className="flex h-8 w-8 items-center justify-center rounded-full"
            style={{ background: "rgba(246,239,224,0.12)" }}
          >
            <ShieldCheck size={16} color="var(--tag-soft)" strokeWidth={2.25} />
          </div>
          <span className="text-[15px] font-semibold" style={{ color: "#f6f1e6" }}>
            MedBot <span style={{ color: "rgba(246,239,224,0.55)" }}>Admin</span>
          </span>
        </Link>

        <div>
          <span
            className="mb-4 inline-block rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.12em]"
            style={{ background: "rgba(246,239,224,0.1)", color: "var(--tag-soft)", fontFamily: "var(--font-mono)" }}
          >
            Restricted console
          </span>
          <h2 className="max-w-xs text-[26px] font-semibold leading-[1.2] tracking-tight" style={{ color: "#f6f1e6" }}>
            Administrative access only.
          </h2>
          <p className="mt-3 max-w-xs text-[13.5px] leading-relaxed" style={{ color: "rgba(246,239,224,0.6)" }}>
            Manage the reference corpus, review verification logs, and monitor system health. Every session is recorded.
          </p>

          <div
            className="mt-8 max-w-xs rounded-xl px-4 py-3.5"
            style={{ background: "rgba(0,0,0,0.22)", border: "1px solid rgba(246,239,224,0.1)" }}
          >
            {CONSOLE_LINES.map((line) => (
              <p
                key={line}
                className="text-[11.5px] leading-[1.9]"
                style={{ fontFamily: "var(--font-mono)", color: "rgba(246,239,224,0.65)" }}
              >
                {line}
              </p>
            ))}
            <p className="text-[11.5px] leading-[1.9]" style={{ fontFamily: "var(--font-mono)", color: "var(--tag-soft)" }}>
              {"> "}awaiting credentials
              <span className="blink-cursor">_</span>
            </p>
          </div>
        </div>

        <p className="text-[12px]" style={{ color: "rgba(246,239,224,0.4)" }}>
          Not an administrator?{" "}
          <Link href="/login" className="focus-ring rounded-sm underline underline-offset-2" style={{ color: "var(--tag-soft)" }}>
            Go to the regular sign-in
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div
      className="relative isolate hidden h-full flex-col justify-between overflow-hidden p-10 lg:flex"
      style={{ background: "linear-gradient(160deg, var(--accent-soft), var(--bg) 78%)" }}
    >
      <div className="auth-grid pointer-events-none absolute inset-0 -z-10" aria-hidden="true" />
      <div
        className="aurora-blob drift-slow -left-20 -top-16 -z-10"
        style={{ background: "rgba(47,111,98,0.22)" }}
        aria-hidden="true"
      />
      <div
        className="aurora-blob drift-slow -right-16 bottom-0 -z-10"
        style={{ background: "rgba(169,120,46,0.16)", animationDelay: "-4s" }}
        aria-hidden="true"
      />

      <Link href="/" className="focus-ring inline-flex w-fit items-center gap-2.5 rounded-md">
        <div className="flex h-8 w-8 items-center justify-center rounded-full" style={{ background: "var(--surface)" }}>
          <Activity size={16} color="var(--accent)" strokeWidth={2.25} />
        </div>
        <span className="text-[15px] font-semibold">MedBot</span>
      </Link>

      <div>
        <span
          className="mb-4 inline-block rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.12em]"
          style={{ background: "var(--surface)", color: "var(--accent)", fontFamily: "var(--font-mono)" }}
        >
          Diagnostic reference assistant
        </span>
        <h2 className="max-w-xs text-[28px] font-semibold leading-[1.18] tracking-tight text-balance">
          Reasoning grounded in a real reference.
        </h2>
        <p className="mt-3 max-w-xs text-[13.5px] leading-relaxed" style={{ color: "var(--ink-muted)" }}>
          Every answer traces back to a page and section of{" "}
          <em>A System of Diagnosis in Outline</em> — verified before it reaches you.
        </p>

        <svg className="mt-7 opacity-70" width="220" height="40" viewBox="0 0 220 40" fill="none" aria-hidden="true">
          <path
            className="ecg-line"
            d="M0 20 H60 L68 6 L76 34 L84 20 H120 L128 4 L136 36 L144 20 H220"
            stroke="var(--accent)"
            strokeWidth="1.75"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>

        <div className="mt-6 flex flex-wrap gap-2">
          {SEPD.map((s) => (
            <span
              key={s.letter}
              className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[11.5px]"
              style={{ background: "var(--surface)", border: "1px solid var(--hairline)" }}
            >
              <span
                className="flex h-4 w-4 items-center justify-center rounded text-[10px] font-semibold"
                style={{ background: "var(--accent-soft)", color: "var(--accent)", fontFamily: "var(--font-mono)" }}
              >
                {s.letter}
              </span>
              <span style={{ color: "var(--ink-muted)" }}>{s.label}</span>
            </span>
          ))}
        </div>

        <div className="relative mt-8 h-9 max-w-xs" aria-hidden="true">
          {CITATIONS.map((c, i) => (
            <span
              key={c}
              className="citation-slide absolute inset-0 flex items-center gap-2 text-[12px]"
              style={{ color: "var(--ink-muted)", fontFamily: "var(--font-mono)", animationDelay: `${i * 2}s` }}
            >
              <span style={{ color: "var(--accent)" }}>&#10003;</span> {c}
            </span>
          ))}
        </div>
      </div>

      <p className="text-[12px]" style={{ color: "var(--ink-muted)" }}>
        Reference information only — not a substitute for professional medical care.
      </p>
    </div>
  );
}
