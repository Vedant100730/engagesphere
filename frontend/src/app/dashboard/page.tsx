"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import FeedbackFeed from "@/components/FeedbackFeed";
import SentimentChart from "@/components/SentimentChart";
import SuggestionsPanel from "@/components/SuggestionsPanel";
import PlatformFilterTabs from "@/components/PlatformFilterTabs";
import { useAuth } from "@/lib/auth-context";
import { getFeedback, getReplies, ingestFeedback, generateReplies, getConnections, classifyFeedback } from "@/lib/api";
import type { Platform, Sentiment } from "@/lib/types";

type PipelineStatus = "idle" | "ingesting" | "generating" | "done" | "error";

export default function DashboardPage() {
  const { user, loading: authLoading, logout } = useAuth();
  const router = useRouter();
  const [activePlatform, setActivePlatform] = useState<Platform | "all">("all");
  const [activeSentiment, setActiveSentiment] = useState<Sentiment | "all">("all");
  const [totalFeedback, setTotalFeedback] = useState<number | null>(null);
  const [pendingReplies, setPendingReplies] = useState<number | null>(null);
  const [connections, setConnections] = useState<{ platform: string; connected: boolean }[]>([]);
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus>("idle");
  const [pipelineMsg, setPipelineMsg] = useState("");
  const [feedKey, setFeedKey] = useState(0);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [user, authLoading, router]);

  const refreshMetrics = useCallback(async () => {
    try {
      const [f, r] = await Promise.all([
        getFeedback({ limit: 1 }),
        getReplies({ status: "pending", limit: 1 }),
      ]);
      setTotalFeedback(f.total);
      setPendingReplies(r.total);
    } catch { /* non-fatal */ }
  }, []);

  const loadConnections = useCallback(async () => {
    try {
      const res = await getConnections();
      setConnections(res.platforms);
    } catch { /* non-fatal */ }
  }, []);

  useEffect(() => {
    if (user) {
      refreshMetrics();
      loadConnections();
    }
  }, [user, refreshMetrics, loadConnections, feedKey]);

  const handleFetch = async () => {
    setPipelineStatus("ingesting");
    setPipelineMsg("Fetching comments from connected platforms…");
    try {
      const ingestRes = await ingestFeedback();
      setPipelineMsg(`Classifying ${ingestRes.total_inserted + 30} items…`);
      // Force reclassify all — ensures correct sentiment after model fix
      const classifyRes = await classifyFeedback(true);
      setPipelineStatus("done");
      setPipelineMsg(`✓ ${ingestRes.total_inserted} new items · ${classifyRes.updated} classified`);
      setFeedKey(k => k + 1);
      refreshMetrics();
    } catch (e: unknown) {
      setPipelineStatus("error");
      setPipelineMsg(e instanceof Error ? e.message : "Fetch failed");
    }
  };

  const handleGenerate = async () => {
    setPipelineStatus("generating");
    setPipelineMsg("Generating AI replies…");
    try {
      const replyRes = await generateReplies();
      if (replyRes.failed > 0) {
        setPipelineStatus("error");
        setPipelineMsg(`${replyRes.generated} replies generated · ${replyRes.failed} failed — check LLM keys`);
      } else {
        setPipelineStatus("done");
        setPipelineMsg(`✓ ${replyRes.generated} replies generated · ${replyRes.skipped} skipped (spam)`);
      }
      setFeedKey(k => k + 1);
      refreshMetrics();
    } catch (e: unknown) {
      setPipelineStatus("error");
      setPipelineMsg(e instanceof Error ? e.message : "Generation failed");
    }
  };

  const handlePipeline = async () => {
    await handleFetch();
    await handleGenerate();
  };

  const busy = pipelineStatus === "ingesting" || pipelineStatus === "generating";
  const connectedCount = connections.filter(c => c.connected).length;

  if (authLoading || !user) return null;

  return (
    <div className="min-h-screen bg-[#080B12] text-gray-100 flex flex-col">

      {/* Header */}
      <header className="relative bg-[#0C1018] border-b border-white/5 px-6 py-4 flex-shrink-0">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-indigo-500/40 to-transparent" />

        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Brand + business name */}
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <span className="text-white text-xs font-bold">E</span>
            </div>
            <div>
              <h1 className="text-base font-bold bg-gradient-to-r from-indigo-300 to-violet-300 bg-clip-text text-transparent leading-none">
                EngageSphere
              </h1>
              <p className="text-xs text-gray-500 mt-0.5">{user.business_name}</p>
            </div>
          </div>

          {/* Right side */}
          <div className="flex items-center gap-3">
            {/* Metrics */}
            <div className="hidden sm:flex items-center gap-2">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/8">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                <span className="text-xs text-gray-400">
                  Feedback <span className="text-white font-semibold ml-1">{totalFeedback ?? "—"}</span>
                </span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/8">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                <span className="text-xs text-gray-400">
                  Pending <span className="text-white font-semibold ml-1">{pendingReplies ?? "—"}</span>
                </span>
              </div>
            </div>

            {/* Connect platforms */}
            <button
              onClick={() => router.push("/settings")}
              className="text-xs px-3 py-1.5 rounded-lg bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10 transition-all"
            >
              ⚙ Manage platforms
            </button>

            {/* Two separate action buttons */}
            <button
              onClick={handleFetch}
              disabled={busy}
              className="relative px-4 py-2 text-xs rounded-lg font-semibold text-white disabled:opacity-50 transition-all bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 shadow-lg shadow-indigo-500/20"
            >
              {busy && pipelineStatus === "ingesting" && (
                <span className="absolute inset-0 bg-white/5 animate-pulse rounded-lg" />
              )}
              <span className="relative flex items-center gap-1.5">
                📥 Fetch Comments
              </span>
            </button>

            <button
              onClick={handleGenerate}
              disabled={busy}
              className="relative px-4 py-2 text-xs rounded-lg font-semibold text-white disabled:opacity-50 transition-all bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 shadow-lg shadow-violet-500/20"
            >
              {busy && pipelineStatus === "generating" && (
                <span className="absolute inset-0 bg-white/5 animate-pulse rounded-lg" />
              )}
              <span className="relative flex items-center gap-1.5">
                ✍️ Generate Replies
              </span>
            </button>

            {/* User menu */}
            <button
              onClick={logout}
              className="text-xs text-gray-500 hover:text-gray-300 transition-colors px-2 py-1.5 rounded-lg hover:bg-white/5"
            >
              Sign out
            </button>
          </div>
        </div>

        {/* Pipeline status */}
        {pipelineMsg && (
          <div className={`mt-2 text-xs px-3 py-1.5 rounded-lg border inline-block ${
            pipelineStatus === "done" ? "bg-green-500/10 border-green-500/20 text-green-400" :
            pipelineStatus === "error" ? "bg-red-500/10 border-red-500/20 text-red-400" :
            "bg-indigo-500/10 border-indigo-500/20 text-indigo-300"
          }`}>
            {pipelineMsg}
          </div>
        )}

        {/* No platforms warning */}
        {connectedCount === 0 && (
          <div className="mt-2 text-xs text-amber-400/80">
            No platforms connected yet — click &quot;Connect platforms&quot; to link Facebook or Instagram.
          </div>
        )}
      </header>

      {/* Filter bar */}
      <div className="bg-[#0C1018] border-b border-white/5 px-6 py-2.5 flex-shrink-0">
        <PlatformFilterTabs
          activePlatform={activePlatform}
          onPlatformChange={setActivePlatform}
          activeSentiment={activeSentiment}
          onSentimentChange={setActiveSentiment}
        />
      </div>

      {/* Body */}
      <div className="flex-1 px-6 py-5 grid grid-cols-1 xl:grid-cols-3 gap-5">
        <div className="xl:col-span-2">
          <FeedbackFeed key={`feed-${feedKey}`} platform={activePlatform} sentiment={activeSentiment} />
        </div>
        <div className="space-y-5">
          <SentimentChart key={`sentiment-${feedKey}`} />
          <SuggestionsPanel key={`suggestions-${feedKey}`} />
        </div>
      </div>
    </div>
  );
}
