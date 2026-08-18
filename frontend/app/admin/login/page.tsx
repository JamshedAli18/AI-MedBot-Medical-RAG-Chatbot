"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { saveToken } from "@/lib/auth";
import { ShieldCheck, ArrowLeft, Loader2 } from "lucide-react";
import AuthPanel from "@/components/AuthPanel";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function AdminLoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/auth/admin-login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Incorrect password.");
        setLoading(false);
        return;
      }

      saveToken(data.access_token, data.identity_type);
      router.push("/admin/dashboard");
    } catch {
      setError("Couldn't reach the server.");
      setLoading(false);
    }
  };

  return (
    <main className="relative isolate min-h-screen overflow-hidden" style={{ background: "var(--bg)" }}>
      <div className="hero-grid pointer-events-none absolute inset-0 -z-10 opacity-60 lg:hidden" aria-hidden="true" />
      <div className="mx-auto grid min-h-screen max-w-5xl lg:grid-cols-2">
        <AuthPanel variant="admin" />

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
            <div className="flex flex-col items-center mb-6 lg:items-start">
              <div
                className="flex items-center justify-center w-11 h-11 rounded-full mb-3"
                style={{ background: "var(--tag-soft)" }}
              >
                <ShieldCheck size={20} color="var(--tag)" strokeWidth={2.25} />
              </div>
              <h1 className="text-[17px] font-semibold">Admin access</h1>
              <p className="mt-1 text-[13px]" style={{ color: "var(--ink-muted)" }}>
                Enter the admin password to continue.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
              <input
                type="password"
                placeholder="Admin password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoFocus
                aria-label="Admin password"
                className="w-full rounded-lg border border-[var(--hairline)] px-3 py-2.5 text-[14px] outline-none transition-[border-color,box-shadow] duration-200 focus:border-[var(--tag)] focus:shadow-[0_0_0_3px_var(--tag-soft)]"
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
                style={{ background: "var(--ink)" }}
              >
                {loading && <Loader2 size={15} className="animate-spin" />}
                Enter
              </button>
            </form>
          </div>
        </div>
      </div>
    </main>
  );
}
