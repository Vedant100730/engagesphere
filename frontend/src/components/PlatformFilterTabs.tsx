"use client";

import type { Platform, Sentiment } from "@/lib/types";

const PLATFORMS: { value: Platform | "all"; label: string; dot?: string }[] = [
  { value: "all",        label: "All Platforms" },
  { value: "google_maps",label: "Google Maps",  dot: "bg-blue-400" },
  { value: "facebook",   label: "Facebook",     dot: "bg-blue-500" },
  { value: "instagram",  label: "Instagram",    dot: "bg-pink-400" },
  { value: "twitter",    label: "Twitter / X",  dot: "bg-slate-400" },
];

const SENTIMENTS: { value: Sentiment | "all"; label: string; color: string }[] = [
  { value: "all",      label: "All",      color: "bg-indigo-500/20 text-indigo-300 border-indigo-500/40" },
  { value: "positive", label: "Positive", color: "bg-green-500/20 text-green-400 border-green-500/40" },
  { value: "negative", label: "Negative", color: "bg-red-500/20 text-red-400 border-red-500/40" },
  { value: "neutral",  label: "Neutral",  color: "bg-amber-500/20 text-amber-400 border-amber-500/40" },
];

interface Props {
  activePlatform: Platform | "all";
  onPlatformChange: (p: Platform | "all") => void;
  activeSentiment: Sentiment | "all";
  onSentimentChange: (s: Sentiment | "all") => void;
}

export default function PlatformFilterTabs({
  activePlatform, onPlatformChange,
  activeSentiment, onSentimentChange,
}: Props) {
  return (
    <div className="flex flex-wrap items-center gap-4">

      {/* Platform pills */}
      <div className="flex items-center gap-1 overflow-x-auto">
        {PLATFORMS.map((p) => (
          <button
            key={p.value}
            onClick={() => onPlatformChange(p.value)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
              activePlatform === p.value
                ? "bg-indigo-500/20 text-indigo-200 border border-indigo-500/40 shadow-sm shadow-indigo-500/10"
                : "text-gray-500 hover:text-gray-300 hover:bg-white/5 border border-transparent"
            }`}
          >
            {p.dot && (
              <span className={`w-1.5 h-1.5 rounded-full ${p.dot} opacity-80`} />
            )}
            {p.label}
          </button>
        ))}
      </div>

      {/* Divider */}
      <div className="w-px h-4 bg-white/10 hidden sm:block" />

      {/* Sentiment pills */}
      <div className="flex items-center gap-1">
        {SENTIMENTS.map((s) => (
          <button
            key={s.value}
            onClick={() => onSentimentChange(s.value)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
              activeSentiment === s.value
                ? s.color
                : "text-gray-500 hover:text-gray-300 hover:bg-white/5 border-transparent"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

    </div>
  );
}
