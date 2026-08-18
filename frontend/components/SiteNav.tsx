"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Activity } from "lucide-react";

export default function SiteNav() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className="sticky top-0 z-50 transition-[background-color,box-shadow,border-color] duration-300"
      style={{
        background: scrolled ? "color-mix(in srgb, var(--bg) 82%, transparent)" : "transparent",
        borderBottom: `1px solid ${scrolled ? "var(--hairline)" : "transparent"}`,
        backdropFilter: scrolled ? "blur(10px)" : "none",
        WebkitBackdropFilter: scrolled ? "blur(10px)" : "none",
      }}
    >
      <div className="flex items-center justify-between max-w-5xl mx-auto px-6 py-5">
        <Link href="/" className="flex items-center gap-2.5 group focus-ring rounded-md">
          <div
            className="flex items-center justify-center w-8 h-8 rounded-full transition-transform duration-300 group-hover:scale-105"
            style={{ background: "var(--accent-soft)" }}
          >
            <Activity size={16} color="var(--accent)" strokeWidth={2.25} />
          </div>
          <span className="text-[15px] font-semibold">MedBot</span>
        </Link>
        <Link
          href="/login"
          className="text-[13.5px] font-medium px-4 py-2 rounded-lg transition-all duration-200 hover:opacity-90 hover:shadow-md active:scale-[0.97] focus-ring"
          style={{ background: "var(--accent)", color: "#fff" }}
        >
          Log in
        </Link>
      </div>
    </header>
  );
}
