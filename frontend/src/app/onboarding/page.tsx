"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { connectFacebook, connectInstagram } from "@/lib/api";

type Step = "welcome" | "facebook" | "instagram" | "done";

export default function OnboardingPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState<Step>("welcome");
  const [fbToken, setFbToken] = useState("");
  const [igToken, setIgToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fbConnected, setFbConnected] = useState(false);
  const [igConnected, setIgConnected] = useState(false);

  useEffect(() => {
    if (!user) router.push("/login");
  }, [user, router]);

  const handleConnectFacebook = async () => {
    if (!fbToken.trim()) return;
    setLoading(true); setError("");
    try {
      await connectFacebook(fbToken.trim());
      setFbConnected(true);
      setStep("instagram");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to connect Facebook");
    } finally {
      setLoading(false);
    }
  };

  const handleConnectInstagram = async () => {
    if (!igToken.trim()) return;
    setLoading(true); setError("");
    try {
      await connectInstagram(igToken.trim());
      setIgConnected(true);
      setStep("done");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to connect Instagram");
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <main className="min-h-screen bg-[#080B12] flex items-center justify-center px-4">
      <div className="relative w-full max-w-lg">
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 bg-indigo-600/10 rounded-full blur-[100px]" />
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-8 space-y-6 shadow-2xl">
          {/* Progress */}
          <div className="flex items-center gap-2">
            {(["welcome", "facebook", "instagram", "done"] as Step[]).map((s, i) => (
              <div key={s} className="flex items-center gap-2 flex-1">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                  step === s ? "bg-indigo-500 text-white" :
                  (["welcome", "facebook", "instagram", "done"].indexOf(step) > i) ? "bg-indigo-500/30 text-indigo-400" :
                  "bg-white/5 text-gray-600"
                }`}>{i + 1}</div>
                {i < 3 && <div className={`flex-1 h-px ${(["welcome","facebook","instagram","done"].indexOf(step) > i) ? "bg-indigo-500/40" : "bg-white/5"}`} />}
              </div>
            ))}
          </div>

          {/* Welcome step */}
          {step === "welcome" && (
            <div className="space-y-4">
              <div>
                <h2 className="text-xl font-bold text-white">Welcome, {user.business_name}! 👋</h2>
                <p className="text-gray-400 text-sm mt-1">Let&apos;s connect your social media accounts so EngageSphere can fetch real comments and generate replies.</p>
              </div>
              <div className="bg-white/5 rounded-xl p-4 space-y-2 border border-white/5">
                <p className="text-xs text-gray-400 font-medium">You&apos;ll need:</p>
                <ul className="text-xs text-gray-500 space-y-1">
                  <li>• Facebook Page Access Token (from Meta Graph API Explorer)</li>
                  <li>• Instagram User Access Token (same or separate)</li>
                </ul>
              </div>
              <button
                onClick={() => setStep("facebook")}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 text-white font-semibold text-sm hover:opacity-90 transition-all"
              >
                Get Started →
              </button>
              <button onClick={() => router.push("/dashboard")} className="w-full text-xs text-gray-600 hover:text-gray-400 transition-colors py-1">
                Skip for now — connect later from dashboard
              </button>
            </div>
          )}

          {/* Facebook step */}
          {step === "facebook" && (
            <div className="space-y-4">
              <div>
                <h2 className="text-lg font-bold text-white">Connect Facebook Page</h2>
                <p className="text-gray-400 text-sm mt-1">Paste your Facebook Page Access Token below.</p>
              </div>
              <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-3 text-xs text-blue-300 space-y-1">
                <p className="font-medium">How to get your token:</p>
                <p>1. Go to developers.facebook.com/tools/explorer</p>
                <p>2. Select your app → Select your Page → Generate Access Token</p>
                <p>3. Add permissions: pages_read_engagement, pages_manage_posts</p>
              </div>
              <textarea
                value={fbToken}
                onChange={e => setFbToken(e.target.value)}
                placeholder="Paste your Facebook Page Access Token here…"
                rows={3}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-indigo-500/50 resize-none"
              />
              {error && <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{error}</p>}
              <div className="flex gap-2">
                <button
                  onClick={handleConnectFacebook}
                  disabled={loading || !fbToken.trim()}
                  className="flex-1 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 text-white font-semibold text-sm disabled:opacity-50 hover:opacity-90 transition-all"
                >
                  {loading ? "Connecting…" : "Connect Facebook"}
                </button>
                <button
                  onClick={() => { setError(""); setStep("instagram"); }}
                  className="px-4 py-3 rounded-xl border border-white/10 text-gray-500 text-sm hover:bg-white/5 transition-all"
                >
                  Skip
                </button>
              </div>
            </div>
          )}

          {/* Instagram step */}
          {step === "instagram" && (
            <div className="space-y-4">
              <div>
                <h2 className="text-lg font-bold text-white">Connect Instagram</h2>
                <p className="text-gray-400 text-sm mt-1">Paste your Instagram User Access Token below.</p>
              </div>
              <div className="bg-pink-500/5 border border-pink-500/20 rounded-xl p-3 text-xs text-pink-300 space-y-1">
                <p className="font-medium">How to get your token:</p>
                <p>1. Go to developers.facebook.com/tools/explorer</p>
                <p>2. Select your app → Generate User Token</p>
                <p>3. Add permissions: instagram_basic, instagram_manage_comments</p>
              </div>
              <textarea
                value={igToken}
                onChange={e => setIgToken(e.target.value)}
                placeholder="Paste your Instagram Access Token here…"
                rows={3}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-indigo-500/50 resize-none"
              />
              {error && <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{error}</p>}
              <div className="flex gap-2">
                <button
                  onClick={handleConnectInstagram}
                  disabled={loading || !igToken.trim()}
                  className="flex-1 py-3 rounded-xl bg-gradient-to-r from-pink-500 to-violet-500 text-white font-semibold text-sm disabled:opacity-50 hover:opacity-90 transition-all"
                >
                  {loading ? "Connecting…" : "Connect Instagram"}
                </button>
                <button
                  onClick={() => { setError(""); setStep("done"); }}
                  className="px-4 py-3 rounded-xl border border-white/10 text-gray-500 text-sm hover:bg-white/5 transition-all"
                >
                  Skip
                </button>
              </div>
            </div>
          )}

          {/* Done */}
          {step === "done" && (
            <div className="space-y-5 text-center">
              <div className="text-5xl">🎉</div>
              <div>
                <h2 className="text-xl font-bold text-white">You&apos;re all set!</h2>
                <p className="text-gray-400 text-sm mt-1">
                  {fbConnected && igConnected ? "Facebook and Instagram connected." :
                   fbConnected ? "Facebook connected." :
                   igConnected ? "Instagram connected." :
                   "You can connect platforms later from the dashboard."}
                </p>
              </div>
              <div className="flex gap-2">
                {fbConnected && <span className="flex-1 py-2 rounded-lg bg-blue-500/15 text-blue-400 border border-blue-500/25 text-xs font-medium">✓ Facebook</span>}
                {igConnected && <span className="flex-1 py-2 rounded-lg bg-pink-500/15 text-pink-400 border border-pink-500/25 text-xs font-medium">✓ Instagram</span>}
              </div>
              <button
                onClick={() => router.push("/dashboard")}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 text-white font-semibold text-sm hover:opacity-90 transition-all"
              >
                Open Dashboard →
              </button>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
