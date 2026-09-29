"use client";

import { useEffect, useState } from "react";
import { getFeedback, getReplies } from "@/lib/api";
import type { FeedbackItem, Platform, Reply, Sentiment } from "@/lib/types";
import ReplyCard from "./ReplyCard";

interface Props {
  platform: Platform | "all";
  sentiment: Sentiment | "all";
}

const PLATFORM_STYLES: Record<string, { badge: string; label: string }> = {
  google_maps: { badge: "bg-blue-500/15 text-blue-300 border-blue-500/25",  label: "Google Maps"  },
  facebook:    { badge: "bg-blue-600/15 text-blue-400 border-blue-600/25",  label: "Facebook"     },
  instagram:   { badge: "bg-pink-500/15 text-pink-300 border-pink-500/25",  label: "Instagram"    },
  twitter:     { badge: "bg-slate-500/15 text-slate-300 border-slate-500/25",label: "Twitter / X" },
};

const INTENT_STYLES: Record<string, string> = {
  complaint: "bg-red-500/10 text-red-400 border-red-500/20",
  praise:    "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  question:  "bg-sky-500/10 text-sky-400 border-sky-500/20",
  spam:      "bg-gray-500/10 text-gray-500 border-gray-500/15",
};

const SENTIMENT_STYLES: Record<string, string> = {
  positive: "bg-emerald-500/15 text-emerald-400 border-emerald-500/25",
  negative: "bg-red-500/15 text-red-400 border-red-500/25",
  neutral:  "bg-amber-500/15 text-amber-400 border-amber-500/25",
};

export default function FeedbackFeed({ platform, sentiment }: Props) {
  const [items, setItems] = useState<FeedbackItem[]>([]);
  const [replyMap, setReplyMap] = useState<Record<string, Reply>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    Promise.all([
      getFeedback({
        platform: platform === "all" ? undefined : platform,
        sentiment: sentiment === "all" ? undefined : sentiment,
        limit: 100,
      }),
      getReplies({ limit: 500 }),
    ])
      .then(([feedbackRes, repliesRes]) => {
        setItems(feedbackRes.items);
        const map: Record<string, Reply> = {};
        for (const r of repliesRes.items) map[r.feedback_item_id] = r;
        setReplyMap(map);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [platform, sentiment]);

  const handleReplyUpdate = (updated: Reply) => {
    setReplyMap(prev => ({ ...prev, [updated.feedback_item_id]: updated }));
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="rounded-xl h-40 bg-white/[0.02] border border-white/5 animate-pulse" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-5 text-red-400 text-sm">
        <span className="font-medium">Failed to load feedback</span>
        <span className="text-red-500/60 ml-2">— {error}</span>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-12 text-center space-y-2">
        <div className="text-3xl">📭</div>
        <p className="text-gray-400 text-sm font-medium">No feedback yet</p>
        <p className="text-gray-600 text-xs">
          {platform !== "all" || sentiment !== "all"
            ? "Try removing filters to see all items."
            : "Click \"Ingest + Generate Replies\" to pull data."}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Count bar */}
      <div className="flex items-center justify-between px-1">
        <span className="text-xs text-gray-500 font-medium">{items.length} items</span>
      </div>

      {items.map((item) => {
        const reply = replyMap[item.id];
        const ps = PLATFORM_STYLES[item.platform];

        return (
          <div
            key={item.id}
            className="group rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/8 transition-all duration-150 p-5 space-y-3"
          >
            {/* Header */}
            <div className="flex items-start justify-between gap-3 flex-wrap">
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`px-2.5 py-1 rounded-lg text-xs font-medium border ${ps?.badge ?? ""}`}>
                  {ps?.label ?? item.platform}
                </span>
                {item.author_name && (
                  <span className="text-sm text-gray-300 font-medium">{item.author_name}</span>
                )}
                {item.rating != null && (
                  <div className="flex items-center gap-0.5">
                    {[1,2,3,4,5].map(s => (
                      <svg key={s} className={`w-3.5 h-3.5 ${s <= item.rating! ? "text-amber-400" : "text-white/10"}`} fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-1.5 flex-wrap">
                {item.intent_category && (
                  <span className={`px-2 py-0.5 rounded-md text-xs font-medium border ${INTENT_STYLES[item.intent_category] ?? ""}`}>
                    {item.intent_category}
                  </span>
                )}
                {item.sentiment && (
                  <span className={`px-2 py-0.5 rounded-md text-xs font-medium border ${SENTIMENT_STYLES[item.sentiment] ?? ""}`}>
                    {item.sentiment}
                  </span>
                )}
              </div>
            </div>

            {/* Review text — never truncated */}
            <p className="text-gray-200 text-sm leading-relaxed">{item.content_text}</p>

            {/* Timestamp */}
            {item.timestamp && (
              <p className="text-xs text-gray-600">
                {new Date(item.timestamp).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
              </p>
            )}

            {/* Reply card */}
            {reply && (
              <ReplyCard reply={reply} feedbackItemId={item.id} onUpdate={handleReplyUpdate} />
            )}
          </div>
        );
      })}
    </div>
  );
}
