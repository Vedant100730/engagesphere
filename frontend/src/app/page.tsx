"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

const FEATURES = [
  { icon: "⚡", title: "Multi-platform ingestion", desc: "Facebook & Instagram — one unified pipeline." },
  { icon: "🧠", title: "Local NLP classification", desc: "Sentiment, intent & spam — fully offline, no API costs." },
  { icon: "✍️", title: "AI reply generation", desc: "RAG-grounded replies via Groq → Gemini → OpenRouter." },
  { icon: "🛡️", title: "Toxicity gate", desc: "Every reply passes toxic-bert before the approval queue." },
  { icon: "💡", title: "Suggestion Agent", desc: "Evidence-backed improvement recommendations." },
  { icon: "✅", title: "Human-in-the-loop", desc: "Approve, edit, or post — no blind auto-publish." },
];

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();

  // If already logged in, go straight to dashboard
  useEffect(() => {
    if (!loading && user) router.push("/dashboard");
  }, [user, loading, router]);

  if (loading) return null;

  return (
    <main className="min-h-screen bg-[#080B12] flex flex-col items-center justify-center px-6 py-20 relative overflow-hidden">
      {/* Background glows */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-64 -left-64 w-[600px] h-[600px] rounded-full bg-indigo-600/10 blur-[120px]" />
        <div className="absolute -bottom-64 -right-32 w-[500px] h-[500px] rounded-full bg-violet-600/10 blur-[100px]" />
      </div>

      <div className="relative z-10 max-w-4xl w-full space-y-14">
        {/* Hero */}
        <div className="text-center space-y-5">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-xs font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
            AI-Powered Customer Engagement
          </div>
          <h1 className="text-6xl sm:text-7xl font-bold tracking-tight">
            <span className="bg-gradient-to-br from-white via-gray-100 to-gray-400 bg-clip-text text-transparent">Engage</span>
            <span className="bg-gradient-to-br from-indigo-400 via-violet-400 to-purple-500 bg-clip-text text-transparent">Sphere</span>
          </h1>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto leading-relaxed">
            Every customer comment across Facebook and Instagram — classified, replied to,
            and turned into actionable insights. Automatically.
          </p>
        </div>

        {/* CTA buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            href="/signup"
            className="px-8 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 text-white font-semibold text-sm hover:from-indigo-400 hover:to-violet-400 transition-all shadow-lg shadow-indigo-500/25 w-full sm:w-auto text-center"
          >
            Get Started Free →
          </Link>
          <Link
            href="/login"
            className="px-8 py-3 rounded-xl border border-white/10 text-gray-300 font-medium text-sm hover:bg-white/5 hover:border-white/20 transition-all w-full sm:w-auto text-center"
          >
            Sign In
          </Link>
        </div>

        {/* Feature grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/10 p-5 space-y-2 transition-all duration-200"
            >
              <div className="text-2xl">{f.icon}</div>
              <p className="text-sm font-semibold text-gray-200">{f.title}</p>
              <p className="text-xs text-gray-500 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
