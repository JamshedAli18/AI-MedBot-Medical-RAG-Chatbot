"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { saveToken } from "@/lib/auth";
import { Activity, ArrowLeft, Loader2 } from "lucide-react";
import AuthPanel from "@/components/AuthPanel";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const endpoint = mode === "login" ? "/auth/login" : "/auth/signup";
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Something went wrong. Please try again.");
        setLoading(false);
        return;
      }

      saveToken(data.access_token, data.identity_type);
      router.push("/chat");
    } catch {
      setError("Couldn't reach the server. Check your connection.");
      setLoading(false);
    }
  };

  const handleGuest = async () => {
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/guest`, { method: "POST" });
      const data = await res.json();

      if (!res.ok) {
        setError("Couldn't start a guest session. Please try again.");
        setLoading(false);
        return;
      }

      saveToken(data.access_token, data.identity_type);
      router.push("/chat");
    } catch {
      setError("Couldn't reach the server. Check your connection.");
      setLoading(false);
    }
  };

  return (
    <main className="relative isolate min-h-screen overflow-hidden" style={{ background: "var(--bg)" }}>
      <div className="hero-grid pointer-events-none absolute inset-0 -z-10 opacity-60 lg:hidden" aria-hidden="true" />
      <div className="mx-auto grid min-h-screen max-w-5xl lg:grid-cols-2">
        <AuthPanel variant="user" />

        <div className="flex flex-col justify-center px-4 py-10 sm:px-8 sm:py-12">
          <Link
            href="/"
            className="focus-ring mb-6 inline-flex w-fit items-center gap-1.5 rounded-md text-[12.5px] font-medium lg:hidden"
            style={{ color: "var(--ink-muted)" }}
          >
            <ArrowLeft size={14} /> Back to home
          </Link>

          <div
            className="pop-in mx-auto w-full max-w-sm rounded-2xl p-8"
            style={{
              background: "var(--surface)",
              border: "1px solid var(--hairline)",
              boxShadow: "0 20px 40px -24px rgba(20,36,32,0.18)",
            }}
          >
            <div className="mb-6 flex flex-col items-center lg:hidden">
              <div
                className="mb-3 flex h-11 w-11 items-center justify-center rounded-full"
                style={{ background: "var(--accent-soft)" }}
              >
                <Activity size={20} color="var(--accent)" strokeWidth={2.25} />
              </div>
              <h1 className="text-[17px] font-semibold">MedBot</h1>
            </div>

            <div className="mb-6 hidden lg:block">
              <h1 className="text-[20px] font-semibold tracking-tight">
                {mode === "login" ? "Welcome back" : "Create your account"}
              </h1>
              <p className="mt-1 text-[13px]" style={{ color: "var(--ink-muted)" }}>
                {mode === "login" ? "Log in to pick up where you left off." : "Unlimited chats, grounded in the reference."}
              </p>
            </div>

            <div
              className="relative flex rounded-lg p-1 mb-5"
              style={{ background: "var(--bg)" }}
            >
              <div
                className="absolute inset-y-1 w-[calc(50%-4px)] rounded-md transition-transform duration-250 ease-out"
                style={{
                  background: "var(--surface)",
                  boxShadow: "0 1px 2px rgba(20,36,32,0.08)",
                  transform: mode === "login" ? "translateX(0)" : "translateX(calc(100% + 8px))",
                }}
                aria-hidden="true"
              />
              <button
                type="button"
                onClick={() => setMode("login")}
                className="relative z-10 flex-1 py-1.5 rounded-md text-[13px] font-medium transition-colors duration-200 focus-ring"
                style={{ color: mode === "login" ? "var(--ink)" : "var(--ink-muted)" }}
              >
                Log in
              </button>
              <button
                type="button"
                onClick={() => setMode("signup")}
                className="relative z-10 flex-1 py-1.5 rounded-md text-[13px] font-medium transition-colors duration-200 focus-ring"
                style={{ color: mode === "signup" ? "var(--ink)" : "var(--ink-muted)" }}
              >
                Sign up
              </button>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                aria-label="Email"
                className="w-full rounded-lg border border-[var(--hairline)] px-3 py-2.5 text-[14px] outline-none transition-[border-color,box-shadow] duration-200 focus:border-[var(--accent)] focus:shadow-[0_0_0_3px_var(--accent-soft)]"
                style={{ background: "var(--bg)", color: "var(--ink)" }}
              />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                aria-label="Password"
                className="w-full rounded-lg border border-[var(--hairline)] px-3 py-2.5 text-[14px] outline-none transition-[border-color,box-shadow] duration-200 focus:border-[var(--accent)] focus:shadow-[0_0_0_3px_var(--accent-soft)]"
                style={{ background: "var(--bg)", color: "var(--ink)" }}
              />

              {error && (
                <p className="pop-in text-[12.5px]" style={{ color: "var(--alert)" }}>
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={loading}
                className="flex items-center justify-center gap-2 w-full rounded-lg py-2.5 text-[14px] font-medium text-white transition-all duration-200 hover:opacity-90 hover:shadow-lg active:scale-[0.98] disabled:opacity-60 disabled:active:scale-100 focus-ring"
                style={{ background: "var(--accent)", boxShadow: "0 8px 20px -12px rgba(47,111,98,0.6)" }}
              >
                {loading && <Loader2 size={15} className="animate-spin" />}
                {mode === "login" ? "Log in" : "Create account"}
              </button>
            </form>

            <div className="flex items-center gap-3 my-5">
              <div className="flex-1 h-px" style={{ background: "var(--hairline)" }} />
              <span
                className="text-[11px] uppercase tracking-wide"
                style={{ color: "var(--ink-muted)", fontFamily: "var(--font-mono)" }}
              >
                or
              </span>
              <div className="flex-1 h-px" style={{ background: "var(--hairline)" }} />
            </div>

            <button
              onClick={handleGuest}
              disabled={loading}
              className="w-full rounded-lg border border-[var(--hairline)] py-2.5 text-[14px] font-medium transition-all duration-200 hover:border-[var(--accent)] active:scale-[0.98] disabled:opacity-60 disabled:active:scale-100 focus-ring"
              style={{ background: "var(--bg)", color: "var(--ink)" }}
            >
              Try as guest (10 questions)
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
