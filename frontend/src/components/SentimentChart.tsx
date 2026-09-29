"use client";

import { useEffect, useState } from "react";
import { getSentimentStats } from "@/lib/api";
import type { SentimentStats } from "@/lib/types";

const BARS = [
  { key: "positive" as const, label: "Positive", color: "#22C55E" },
  { key: "negative" as const, label: "Negative", color: "#EF4444" },
  { key: "neutral"  as const, label: "Neutral",  color: "#F59E0B" },
];

export default function SentimentChart() {
  const [stats, setStats] = useState<SentimentStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getSentimentStats()
      .then(setStats).catch(console.error).finally(() => setLoading(false));
  }, []);

  const pct = (n: number) => stats && stats.total > 0 ? Math.round((n / stats.total) * 100) : 0;

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-200">Sentiment Breakdown</h2>
        {stats && stats.total > 0 && (
          <span className="text-xs text-gray-500 bg-white/5 px-2 py-0.5 rounded-md">
            {stats.total} reviews
          </span>
        )}
      </div>

      <div className="space-y-3">
        {BARS.map((b) => {
          const value = loading ? 0 : pct(stats?.[b.key] ?? 0);
          const count = stats?.[b.key] ?? 0;
          return (
            <div key={b.key} className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400 font-medium">{b.label}</span>
                <div className="flex items-center gap-2">
                  {!loading && stats && (
                    <span className="text-xs text-gray-600">{count}</span>
                  )}
                  <span className="text-xs font-semibold w-8 text-right" style={{ color: b.color }}>
                    {loading ? "—" : `${value}%`}
                  </span>
                </div>
              </div>
              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                <div
                  className="h-1.5 rounded-full transition-all duration-700 ease-out"
                  style={{
                    width: loading ? "0%" : `${value}%`,
                    backgroundColor: b.color,
                    boxShadow: value > 0 ? `0 0 8px ${b.color}60` : "none",
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {!loading && stats && stats.total === 0 && (
        <p className="text-xs text-gray-600 text-center pt-1">
          Run Ingest to populate sentiment data
        </p>
      )}
    </div>
  );
}
