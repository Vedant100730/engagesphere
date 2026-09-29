"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { getConnections, getOAuthUrl } from "@/lib/api";
import { Suspense } from "react";

interface Connection {
  platform: string;
  connected: boolean;
  status: string;
}

function SettingsContent() {
  const { user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [connections, setConnections] = useState<Connection[]>([]);
  const [fbLoading, setFbLoading] = useState(false);
  const [igLoading, setIgLoading] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    if (!user) { router.push("/login"); return; }

    // Handle OAuth callback results
    const success = searchParams.get("success");
    const error = searchParams.get("error");
    if (success === "facebook") setToast({ type: "success", text: "✓ Facebook connected successfully!" });
    else if (success === "instagram") setToast({ type: "success", text: "✓ Instagram connected successfully!" });
    else if (error) setToast({ type: "error", text: `Connection failed: ${error.replace(/_/g, " ")}` });

    loadConnections();
  }, [user, searchParams]);

  const loadConnections = async () => {
    try {
      const res = await getConnections();
      setConnections(res.platforms);
    } catch {}
  };

  const isConnected = (platform: string) =>
    connections.find(c => c.platform === platform)?.connected ?? false;

  const handleOAuth = async (platform: "facebook" | "instagram") => {
    const setLoading = platform === "facebook" ? setFbLoading : setIgLoading;
    setLoading(true);
    setToast(null);
    try {
      const url = await getOAuthUrl(platform);
      window.location.href = url;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Connection failed";
      setToast({
        type: "error",
        text: msg.includes("not configured")
          ? `Connection unavailable — please contact support`
          : `Failed to connect ${platform}. Please try again.`
      });
      setLoading(false);
    }
  };

  if (!user) return null;

  const livePlatforms = [
    {
      id: "facebook" as const,
      name: "Facebook",
      icon: "f",
      description: "Fetch comments from your Facebook Page posts and reply to them",
      badge: "bg-blue-500/15 text-blue-300 border-blue-500/25",
      iconBg: "bg-blue-600",
      loading: fbLoading,
    },
    {
      id: "instagram" as const,
      name: "Instagram",
      icon: "ig",
      description: "Fetch comments from your Instagram Business posts and reply to them",
      badge: "bg-pink-500/15 text-pink-300 border-pink-500/25",
      iconBg: "bg-gradient-to-br from-pink-500 to-violet-600",
      loading: igLoading,
    },
  ];

  return (
    <div className="min-h-screen bg-[#080B12] text-gray-100">
      {/* Header */}
      <header className="relative bg-[#0C1018] border-b border-white/5 px-6 py-4">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-indigo-500/40 to-transparent" />
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/dashboard")}
              className="text-gray-500 hover:text-gray-300 transition-colors text-sm flex items-center gap-1"
            >
              ← Dashboard
            </button>
            <span className="text-gray-700">|</span>
            <h1 className="text-base font-semibold text-gray-200">Platform Connections</h1>
          </div>
          <span className="text-xs text-gray-500 bg-white/5 px-2 py-1 rounded-lg">{user.business_name}</span>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-6 py-8 space-y-5">

        {/* Toast */}
        {toast && (
          <div className={`rounded-xl border px-4 py-3 text-sm font-medium ${
            toast.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/25 text-emerald-400"
              : "bg-red-500/10 border-red-500/25 text-red-400"
          }`}>
            {toast.text}
          </div>
        )}

        {/* Simulated platforms */}
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5 space-y-3">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Always Active — Simulated</p>
          <div className="flex gap-3">
            {[
              { name: "Google Maps", badge: "bg-blue-500/10 text-blue-400 border-blue-500/20", count: "15 reviews" },
              { name: "Twitter / X", badge: "bg-slate-500/10 text-slate-400 border-slate-500/20", count: "15 mentions" },
            ].map(p => (
              <div key={p.name} className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium ${p.badge}`}>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                {p.name}
                <span className="text-[10px] opacity-50">{p.count}</span>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-600">These use realistic mock datasets and are always active — no setup needed.</p>
        </div>

        {/* Live platforms */}
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mt-2">Live Platforms — Connect with one click</p>

        {livePlatforms.map(p => (
          <div key={p.id} className="rounded-xl border border-white/8 bg-white/[0.02] p-5">
            <div className="flex items-center justify-between gap-4">
              {/* Left: icon + info */}
              <div className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded-xl ${p.iconBg} flex items-center justify-center text-white text-xs font-bold shadow-lg`}>
                  {p.icon}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-gray-200">{p.name}</span>
                    {isConnected(p.id) && (
                      <span className="flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full font-medium">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                        Connected
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">{p.description}</p>
                </div>
              </div>

              {/* Right: connect button */}
              <button
                onClick={() => handleOAuth(p.id)}
                disabled={p.loading}
                className="flex-shrink-0 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 transition-all shadow-lg shadow-indigo-500/20 whitespace-nowrap"
              >
                {p.loading ? "Redirecting…" : isConnected(p.id) ? "Reconnect" : `Connect ${p.name}`}
              </button>
            </div>

            {/* Instructions — only when not connected */}
            {!isConnected(p.id) && (
              <div className="mt-4 bg-white/[0.03] border border-white/5 rounded-lg p-3">
                <p className="text-xs text-gray-500">
                  Click <span className="text-gray-300 font-medium">Connect {p.name}</span> → log in with your {p.name} account → click Allow.
                  No tokens or technical values needed.
                </p>
              </div>
            )}
          </div>
        ))}

        <button
          onClick={() => router.push("/dashboard")}
          className="w-full py-3 rounded-xl border border-white/10 text-gray-500 text-sm hover:bg-white/5 hover:text-gray-300 transition-all"
        >
          ← Back to Dashboard
        </button>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#080B12]" />}>
      <SettingsContent />
    </Suspense>
  );
}
