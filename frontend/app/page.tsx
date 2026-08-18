import Link from "next/link";
import {
  ArrowRight,
  ShieldCheck,
  Search,
  Globe,
  BookOpen,
  Sparkles,
  MessagesSquare,
  History,
  ListChecks,
  Code2,
  Workflow,
  Database,
  Lock,
} from "lucide-react";
import SiteNav from "@/components/SiteNav";
import Reveal from "@/components/Reveal";

const STEPS = [
  {
    letter: "S",
    title: "Site",
    desc: "Where in the body the problem originates — organ, system, or structure.",
  },
  {
    letter: "E",
    title: "Etiology",
    desc: "The underlying cause — infectious, congenital, metabolic, or otherwise.",
  },
  {
    letter: "P",
    title: "Pathophysiology",
    desc: "How the disease disrupts normal function once it takes hold.",
  },
  {
    letter: "D",
    title: "Dysfunction",
    desc: "The measurable impact on the patient's day-to-day capacity.",
  },
];

const ARCHITECTURE = [
  {
    icon: MessagesSquare,
    title: "Ask",
    desc: "Your question arrives and is checked for urgency and general intent before anything else happens.",
  },
  {
    icon: History,
    title: "Contextualize",
    desc: "Chat history folds into a single, standalone question — the one that actually gets searched for.",
  },
  {
    icon: Search,
    title: "Retrieve & rerank",
    desc: "A vector search across the book's full text, then reranked so only the most relevant passages move forward.",
  },
  {
    icon: ListChecks,
    title: "Grade the evidence",
    desc: "Every retrieved passage is scored on its own — the answer can't lean on evidence that fails the check.",
  },
  {
    icon: Globe,
    title: "Search the web",
    desc: "Only when the book's evidence comes up thin. Pulled in and clearly labeled as a separate, non-book source.",
    fallback: true,
  },
  {
    icon: ShieldCheck,
    title: "Generate & verify",
    desc: "An answer is drafted from the graded material, then independently checked for claims it can't support.",
  },
  {
    icon: BookOpen,
    title: "Answer, cited",
    desc: "Page and section attached to every claim it makes, so you can go check the source yourself.",
  },
];

const STACK = [
  {
    icon: Code2,
    title: "Frontend",
    items: ["Next.js", "React", "TypeScript", "Tailwind CSS"],
  },
  {
    icon: Workflow,
    title: "Orchestration & reasoning",
    items: ["LangGraph", "LangChain", "Groq", "OpenAI"],
  },
  {
    icon: Database,
    title: "Retrieval & ranking",
    items: ["Pinecone", "Cohere Rerank"],
  },
  {
    icon: Lock,
    title: "Safety & data",
    items: ["MongoDB", "JWT auth", "Tavily search"],
  },
];

const FEATURES = [
  {
    icon: BookOpen,
    title: "Grounded in a real reference",
    desc: "Every answer traces back to a specific page and section of the source book — not invented from memory.",
  },
  {
    icon: ShieldCheck,
    title: "Verified before you see it",
    desc: "A second, independent check audits every answer for unsupported claims before it's shown to you.",
  },
  {
    icon: Globe,
    title: "Honest when it doesn't know",
    desc: "If the book doesn't cover something, it says so — or looks to the web, clearly labeled as a separate source.",
  },
  {
    icon: Sparkles,
    title: "Adapts to how you ask",
    desc: "Ask for detail, a simple explanation, or bullet points — the same grounded facts, restyled on request.",
  },
];

export default function LandingPage() {
  return (
    <main style={{ background: "var(--bg)" }} className="min-h-screen overflow-x-hidden">
      <SiteNav />

      {/* Hero */}
      <section className="relative isolate">
        <div className="hero-grid pointer-events-none absolute inset-0 -z-10" aria-hidden="true" />
        <svg
          className="pointer-events-none absolute left-1/2 top-8 -z-10 -translate-x-1/2 opacity-[0.14]"
          width="900"
          height="120"
          viewBox="0 0 900 120"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M0 70 H320 L360 20 L400 105 L440 45 L470 80 L500 70 H900"
            stroke="var(--accent)"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>

        <div className="relative z-10 max-w-3xl mx-auto px-6 pt-20 pb-24 text-center sm:pt-28 sm:pb-32">
          <Reveal>
            <span
              className="inline-block text-[11px] uppercase tracking-[0.12em] px-3 py-1 rounded-full mb-6"
              style={{ background: "var(--tag-soft)", color: "var(--tag)", fontFamily: "var(--font-mono)" }}
            >
              Diagnostic reference assistant
            </span>
          </Reveal>
          <Reveal delay={80}>
            <h1 className="text-[36px] sm:text-[48px] font-semibold leading-[1.12] tracking-tight text-balance">
              A reasoning partner for clinical diagnosis —
              <br className="hidden sm:block" />
              not a guessing one.
            </h1>
          </Reveal>
          <Reveal delay={160}>
            <p className="mt-6 text-[16px] sm:text-[17px] leading-relaxed max-w-xl mx-auto" style={{ color: "var(--ink-muted)" }}>
              MedBot answers grounded in{" "}
              <em>A System of Diagnosis in Outline</em>, with every claim verified
              and cited before it reaches you. Ask about symptom analysis, site
              localization, or reasoning through a diagnosis, system by system.
            </p>
          </Reveal>
          <Reveal delay={240}>
            <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link
                href="/login"
                className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl text-[14px] font-medium text-white transition-all duration-200 hover:opacity-90 hover:-translate-y-0.5 hover:shadow-lg active:translate-y-0 focus-ring"
                style={{ background: "var(--accent)", boxShadow: "0 8px 24px -12px rgba(47,111,98,0.55)" }}
              >
                Get started <ArrowRight size={15} />
              </Link>
              <Link
                href="/login"
                className="px-5 py-2.5 rounded-xl text-[14px] font-medium transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md focus-ring"
                style={{ background: "var(--surface)", border: "1px solid var(--hairline)", color: "var(--ink)" }}
              >
                Try as guest
              </Link>
            </div>
          </Reveal>
          <Reveal delay={300}>
            <p
              className="mt-8 flex items-center justify-center gap-2 text-[12px]"
              style={{ color: "var(--ink-muted)", fontFamily: "var(--font-mono)" }}
            >
              <Search size={13} strokeWidth={2} />
              Every answer cites its source, page and all.
            </p>
          </Reveal>
        </div>
      </section>

      {/* How it works — tied to the book's own diagnostic framework */}
      <section className="max-w-4xl mx-auto px-6 pb-24 sm:pb-28">
        <Reveal>
          <h2
            className="text-[13px] uppercase tracking-[0.1em] text-center mb-2"
            style={{ color: "var(--ink-muted)", fontFamily: "var(--font-mono)" }}
          >
            The reasoning framework
          </h2>
          <p className="text-center text-[15px] mb-12" style={{ color: "var(--ink-muted)" }}>
            Every diagnosis in the source material is worked through the same four lenses.
          </p>
        </Reveal>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 sm:gap-5">
          {STEPS.map((s, i) => (
            <Reveal key={s.letter} delay={i * 90}>
              <div
                className="group h-full rounded-2xl p-5 transition-all duration-300 hover:-translate-y-1"
                style={{
                  background: "var(--surface)",
                  border: "1px solid var(--hairline)",
                  boxShadow: "0 1px 2px rgba(20,36,32,0.04)",
                }}
              >
                <span
                  className="flex items-center justify-center w-9 h-9 rounded-lg text-[14px] font-semibold mb-4 transition-colors duration-300 group-hover:bg-[var(--accent)] group-hover:text-white"
                  style={{ background: "var(--accent-soft)", color: "var(--accent)", fontFamily: "var(--font-mono)" }}
                >
                  {s.letter}
                </span>
                <h3 className="text-[14.5px] font-semibold mb-1.5">{s.title}</h3>
                <p className="text-[13px] leading-relaxed" style={{ color: "var(--ink-muted)" }}>
                  {s.desc}
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Architecture — how a question actually becomes a cited answer */}
      <section className="max-w-3xl mx-auto px-6 pb-24 sm:pb-28">
        <Reveal>
          <h2
            className="text-[13px] uppercase tracking-[0.1em] text-center mb-2"
            style={{ color: "var(--ink-muted)", fontFamily: "var(--font-mono)" }}
          >
            Under the hood
          </h2>
          <p className="text-center text-[15px] mb-12" style={{ color: "var(--ink-muted)" }}>
            How a question becomes a cited answer, one checked step at a time.
          </p>
        </Reveal>
        <div className="relative">
          <div
            className="absolute left-5 top-2 bottom-2 w-px"
            style={{ background: "var(--hairline)" }}
            aria-hidden="true"
          />
          <div className="flex flex-col">
            {ARCHITECTURE.map((step, i) => (
              <Reveal key={step.title} delay={i * 70}>
                <div className="relative flex gap-5 py-3.5">
                  <div
                    className="relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full"
                    style={{
                      background: step.fallback ? "var(--tag-soft)" : "var(--accent-soft)",
                      border: step.fallback ? "1px dashed var(--tag)" : "1px solid var(--surface)",
                    }}
                  >
                    <step.icon size={16} color={step.fallback ? "var(--tag)" : "var(--accent)"} strokeWidth={2} />
                  </div>
                  <div className="pt-1.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-[14.5px] font-semibold">{step.title}</h3>
                      {step.fallback && (
                        <span
                          className="rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wide"
                          style={{ background: "var(--tag-soft)", color: "var(--tag)", fontFamily: "var(--font-mono)" }}
                        >
                          Fallback path
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-[13px] leading-relaxed max-w-md" style={{ color: "var(--ink-muted)" }}>
                      {step.desc}
                    </p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-4xl mx-auto px-6 pb-24 sm:pb-28">
        <Reveal>
          <h2
            className="text-[13px] uppercase tracking-[0.1em] text-center mb-12"
            style={{ color: "var(--ink-muted)", fontFamily: "var(--font-mono)" }}
          >
            Built for accuracy, not just speed
          </h2>
        </Reveal>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-5">
          {FEATURES.map((f, i) => (
            <Reveal key={f.title} delay={i * 90}>
              <div
                className="group flex h-full gap-3.5 rounded-2xl p-5 transition-all duration-300 hover:-translate-y-1"
                style={{
                  background: "var(--surface)",
                  border: "1px solid var(--hairline)",
                  boxShadow: "0 1px 2px rgba(20,36,32,0.04)",
                }}
              >
                <div
                  className="flex items-center justify-center w-9 h-9 rounded-xl shrink-0 transition-colors duration-300 group-hover:bg-[var(--accent)]"
                  style={{ background: "var(--accent-soft)" }}
                >
                  <f.icon size={17} className="transition-colors duration-300 group-hover:stroke-white" color="var(--accent)" strokeWidth={2} />
                </div>
                <div>
                  <h3 className="text-[14.5px] font-semibold mb-1">{f.title}</h3>
                  <p className="text-[13.5px] leading-relaxed" style={{ color: "var(--ink-muted)" }}>
                    {f.desc}
                  </p>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Tech stack */}
      <section className="max-w-4xl mx-auto px-6 pb-24 sm:pb-28">
        <Reveal>
          <h2
            className="text-[13px] uppercase tracking-[0.1em] text-center mb-2"
            style={{ color: "var(--ink-muted)", fontFamily: "var(--font-mono)" }}
          >
            Built with
          </h2>
          <p className="text-center text-[15px] mb-12" style={{ color: "var(--ink-muted)" }}>
            A typed, modern stack end to end — no piece pretending to be simpler than it is.
          </p>
        </Reveal>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-5">
          {STACK.map((s, i) => (
            <Reveal key={s.title} delay={i * 90}>
              <div
                className="group h-full rounded-2xl p-5 transition-all duration-300 hover:-translate-y-1"
                style={{
                  background: "var(--surface)",
                  border: "1px solid var(--hairline)",
                  boxShadow: "0 1px 2px rgba(20,36,32,0.04)",
                }}
              >
                <div className="flex items-center gap-3 mb-3.5">
                  <div
                    className="flex items-center justify-center w-9 h-9 rounded-xl shrink-0 transition-colors duration-300 group-hover:bg-[var(--accent)]"
                    style={{ background: "var(--accent-soft)" }}
                  >
                    <s.icon size={17} className="transition-colors duration-300 group-hover:stroke-white" color="var(--accent)" strokeWidth={2} />
                  </div>
                  <h3 className="text-[14.5px] font-semibold">{s.title}</h3>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {s.items.map((item) => (
                    <span
                      key={item}
                      className="rounded-full px-2.5 py-1 text-[11.5px]"
                      style={{
                        background: "var(--bg)",
                        border: "1px solid var(--hairline)",
                        color: "var(--ink-muted)",
                        fontFamily: "var(--font-mono)",
                      }}
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section className="max-w-4xl mx-auto px-6 pb-20 sm:pb-24">
        <Reveal>
          <div
            className="relative isolate overflow-hidden rounded-3xl px-8 py-14 text-center sm:px-16 sm:py-16"
            style={{ background: "var(--accent-soft)", border: "1px solid var(--hairline)" }}
          >
            <div className="hero-grid pointer-events-none absolute inset-0 -z-10 opacity-40" aria-hidden="true" />
            <div className="relative z-10">
              <h2 className="text-[26px] sm:text-[30px] font-semibold tracking-tight leading-tight text-balance">
                Reason through a diagnosis with confidence.
              </h2>
              <p className="mt-3 text-[15px] max-w-md mx-auto" style={{ color: "var(--ink-muted)" }}>
                Free to try, no card required. Ten guest questions, or sign up for unlimited chats.
              </p>
              <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
                <Link
                  href="/login"
                  className="flex items-center gap-1.5 px-6 py-3 rounded-xl text-[14px] font-medium text-white transition-all duration-200 hover:opacity-90 hover:-translate-y-0.5 hover:shadow-lg active:translate-y-0 focus-ring"
                  style={{ background: "var(--accent)", boxShadow: "0 8px 24px -12px rgba(47,111,98,0.55)" }}
                >
                  Get started <ArrowRight size={15} />
                </Link>
              </div>
            </div>
          </div>
        </Reveal>
      </section>

      {/* Footer */}
      <footer className="text-center px-6 py-8" style={{ borderTop: "1px solid var(--hairline)" }}>
        <p className="text-[12px]" style={{ color: "var(--ink-muted)" }}>
          Reference information only — not a substitute for professional medical care.
        </p>
      </footer>
    </main>
  );
}
