"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken, getIdentityType, clearToken } from "@/lib/auth";
import { Users, UserRound, LogOut, RefreshCw } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

interface UserSummary {
  email: string;
  auth_provider: string;
  created_at: string;
}

interface GuestSummary {
  guest_id: string;
  question_count: number;
  created_at: string;
  last_used_at: string;
}

interface Stats {
  total_users: number;
  total_guests: number;
  users: UserSummary[];
  guests: GuestSummary[];
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function AdminDashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    const token = getToken();
    if (!token || getIdentityType() !== "admin") {
      router.replace("/admin/login");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401 || res.status === 403) {
        clearToken();
        router.replace("/admin/login");
        return;
      }
      const data = await res.json();
      setStats(data);
    } catch {
      setError("Couldn't load stats. Check the server connection.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleLogout = () => {
    clearToken();
    router.replace("/admin/login");
  };

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6" style={{ background: "var(--bg)" }}>
      <div className="max-w-3xl mx-auto">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-8">
          <h1 className="text-[19px] font-semibold">Admin dashboard</h1>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchStats}
              disabled={loading}
              className="flex items-center gap-1.5 text-[12.5px] px-3 py-1.5 rounded-lg transition-colors duration-200 hover:bg-black/[0.03] disabled:opacity-60 focus-ring"
              style={{ background: "var(--surface)", border: "1px solid var(--hairline)", color: "var(--ink)" }}
            >
              <RefreshCw size={13} className={loading ? "animate-spin" : ""} /> Refresh
            </button>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 text-[12.5px] px-3 py-1.5 rounded-lg transition-colors duration-200 hover:bg-black/5 focus-ring"
              style={{ color: "var(--ink-muted)" }}
            >
              <LogOut size={13} /> Log out
            </button>
          </div>
        </div>

        {error && <p className="pop-in mb-6 text-[13.5px]" style={{ color: "var(--alert)" }}>{error}</p>}

        {loading && !stats && (
          <div className="pop-in">
            <div className="grid grid-cols-2 gap-3 mb-8 sm:gap-4">
              {[0, 1].map((i) => (
                <div
                  key={i}
                  className="h-[74px] animate-pulse rounded-2xl"
                  style={{ background: "var(--surface)", border: "1px solid var(--hairline)" }}
                />
              ))}
            </div>
            <div className="h-4 w-20 mb-3 animate-pulse rounded" style={{ background: "var(--hairline)" }} />
            <div
              className="h-32 animate-pulse rounded-2xl mb-8"
              style={{ background: "var(--surface)", border: "1px solid var(--hairline)" }}
            />
            <div className="h-4 w-20 mb-3 animate-pulse rounded" style={{ background: "var(--hairline)" }} />
            <div
              className="h-32 animate-pulse rounded-2xl"
              style={{ background: "var(--surface)", border: "1px solid var(--hairline)" }}
            />
          </div>
        )}

        {stats && (
          <div className="pop-in">
            <div className="grid grid-cols-2 gap-3 mb-8 sm:gap-4">
              <div
                className="rounded-2xl p-4 flex items-center gap-3 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md sm:p-5 sm:gap-3.5"
                style={{ background: "var(--surface)", border: "1px solid var(--hairline)" }}
              >
                <div
                  className="flex items-center justify-center w-10 h-10 rounded-xl shrink-0"
                  style={{ background: "var(--accent-soft)" }}
                >
                  <Users size={18} color="var(--accent)" />
                </div>
                <div className="min-w-0">
                  <p className="text-[22px] font-semibold leading-none">{stats.total_users}</p>
                  <p className="text-[12px] mt-1" style={{ color: "var(--ink-muted)" }}>Registered users</p>
                </div>
              </div>
              <div
                className="rounded-2xl p-4 flex items-center gap-3 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md sm:p-5 sm:gap-3.5"
                style={{ background: "var(--surface)", border: "1px solid var(--hairline)" }}
              >
                <div
                  className="flex items-center justify-center w-10 h-10 rounded-xl shrink-0"
                  style={{ background: "var(--tag-soft)" }}
                >
                  <UserRound size={18} color="var(--tag)" />
                </div>
                <div className="min-w-0">
                  <p className="text-[22px] font-semibold leading-none">{stats.total_guests}</p>
                  <p className="text-[12px] mt-1" style={{ color: "var(--ink-muted)" }}>Guest sessions</p>
                </div>
              </div>
            </div>

            <h2 className="text-[13px] uppercase tracking-[0.08em] mb-3" style={{ color: "var(--ink-muted)", fontFamily: "var(--font-mono)" }}>
              Users
            </h2>
            <div
              className="rounded-2xl overflow-hidden mb-8"
              style={{ background: "var(--surface)", border: "1px solid var(--hairline)" }}
            >
              {stats.users.length === 0 ? (
                <p className="p-5 text-[13px] text-center" style={{ color: "var(--ink-muted)" }}>
                  No registered users yet — they&rsquo;ll show up here once someone signs up.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[480px] text-[13px]">
                    <thead>
                      <tr style={{ borderBottom: "1px solid var(--hairline)" }}>
                        <th className="text-left px-4 py-2.5 font-medium" style={{ color: "var(--ink-muted)" }}>Email</th>
                        <th className="text-left px-4 py-2.5 font-medium" style={{ color: "var(--ink-muted)" }}>Provider</th>
                        <th className="text-left px-4 py-2.5 font-medium" style={{ color: "var(--ink-muted)" }}>Joined</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.users.map((u) => (
                        <tr key={u.email} className="transition-colors duration-150 hover:bg-black/[0.02]" style={{ borderTop: "1px solid var(--hairline)" }}>
                          <td className="px-4 py-2.5">{u.email}</td>
                          <td className="px-4 py-2.5" style={{ color: "var(--ink-muted)" }}>{u.auth_provider}</td>
                          <td className="px-4 py-2.5 whitespace-nowrap" style={{ color: "var(--ink-muted)", fontFamily: "var(--font-mono)", fontSize: 12 }}>
                            {formatDate(u.created_at)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <h2 className="text-[13px] uppercase tracking-[0.08em] mb-3" style={{ color: "var(--ink-muted)", fontFamily: "var(--font-mono)" }}>
              Guests
            </h2>
            <div
              className="rounded-2xl overflow-hidden"
              style={{ background: "var(--surface)", border: "1px solid var(--hairline)" }}
            >
              {stats.guests.length === 0 ? (
                <p className="p-5 text-[13px] text-center" style={{ color: "var(--ink-muted)" }}>
                  No guest sessions yet — they&rsquo;ll show up here once someone tries MedBot.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[480px] text-[13px]">
                    <thead>
                      <tr style={{ borderBottom: "1px solid var(--hairline)" }}>
                        <th className="text-left px-4 py-2.5 font-medium" style={{ color: "var(--ink-muted)" }}>Guest ID</th>
                        <th className="text-left px-4 py-2.5 font-medium" style={{ color: "var(--ink-muted)" }}>Questions used</th>
                        <th className="text-left px-4 py-2.5 font-medium" style={{ color: "var(--ink-muted)" }}>Last active</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.guests.map((g) => (
                        <tr key={g.guest_id} className="transition-colors duration-150 hover:bg-black/[0.02]" style={{ borderTop: "1px solid var(--hairline)" }}>
                          <td className="px-4 py-2.5 whitespace-nowrap" style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}>
                            {g.guest_id.slice(0, 8)}...
                          </td>
                          <td className="px-4 py-2.5">
                            <span
                              className="px-2 py-0.5 rounded text-[12px]"
                              style={{
                                background: g.question_count >= 10 ? "var(--alert-soft)" : "var(--accent-soft)",
                                color: g.question_count >= 10 ? "var(--alert)" : "var(--accent)",
                              }}
                            >
                              {g.question_count} / 10
                            </span>
                          </td>
                          <td className="px-4 py-2.5 whitespace-nowrap" style={{ color: "var(--ink-muted)", fontFamily: "var(--font-mono)", fontSize: 12 }}>
                            {formatDate(g.last_used_at)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
