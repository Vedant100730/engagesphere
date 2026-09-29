"use client";

import { useEffect, useState } from "react";
import { getSuggestions, generateSuggestions } from "@/lib/api";
import type { Suggestion } from "@/lib/types";

export default function SuggestionsPanel() {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const load = () => {
    setLoading(true); setError(null);
    getSuggestions()
      .then(res => setSuggestions(res.items))
      .catch((e: Error) => {
        // Session expired — don't show error on initial load, just show empty state
        if (e.message.includes("401") || e.message.includes("Session expired")) {
          setSuggestions([]);
        } else {
          setError(e.message);
        }
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleGenerate = async () => {
    setGenerating(true); setError(null); setToast(null);
    try {
      const res = await generateSuggestions();
      setToast(`${res.generated} new suggestion${res.generated !== 1 ? "s" : ""} generated`);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="rounded-xl border border-indigo-500/15 bg-white/[0.02] p-5 space-y-4">

      {/* Header */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-md bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center">
            <span className="text-xs">💡</span>
          </div>
          <h2 className="text-sm font-semibold text-gray-200">Suggestions</h2>
          {suggestions.length > 0 && (
            <span className="text-xs bg-indigo-500/15 text-indigo-400 border border-indigo-500/25 px-1.5 py-0.5 rounded-md font-medium">
              {suggestions.length}
            </span>
          )}
        </div>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-medium bg-indigo-500/15 text-indigo-300 border border-indigo-500/25 hover:bg-indigo-500/25 disabled:opacity-50 transition-all"
          >
            {generating ? (
              <>
                <span className="w-3 h-3 border border-indigo-400/40 border-t-indigo-400 rounded-full animate-spin" />
                Analysing…
              </>
            ) : "Re-generate"}
          </button>
      </div>

      {/* Toast */}
      {toast && (
        <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-3 py-2">
          <span>✓</span> {toast}
        </div>
      )}
      {error && (
        <p className="text-xs text-red-400 bg-red-500/5 border border-red-500/15 rounded-lg px-3 py-2">{error}</p>
      )}

      {/* Content */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="h-16 bg-white/[0.03] rounded-lg animate-pulse" />
          ))}
        </div>
      ) : suggestions.length === 0 ? (
        <div className="text-center py-6">
          <p className="text-gray-500 text-xs">
            Click Re-generate to analyse feedback and get suggestions
          </p>
        </div>
      ) : (
        <ul className="space-y-4 max-h-[440px] overflow-y-auto pr-0.5">
          {suggestions.map((s, idx) => (
            <li key={s.id} className="space-y-2.5 pb-4 border-b border-white/5 last:border-0 last:pb-0">
              {/* Suggestion number */}
              <div className="flex items-start gap-2">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-indigo-500/15 border border-indigo-500/25 text-indigo-400 text-[10px] font-bold flex items-center justify-center mt-0.5">
                  {idx + 1}
                </span>
                <p className="text-sm text-gray-200 leading-relaxed">{s.suggestion_text}</p>
              </div>

              {/* Evidence quotes */}
              {s.evidence_quotes && s.evidence_quotes.length > 0 && (
                <div className="ml-7 space-y-1.5">
                  {s.evidence_quotes.slice(0, 2).map((q, i) => (
                    <blockquote key={i} className="flex items-start gap-2">
                      <span className="text-indigo-500/60 text-sm mt-0.5 flex-shrink-0">"</span>
                      <p className="text-xs text-gray-500 italic leading-relaxed">
                        {q.quote.length > 110 ? q.quote.slice(0, 110) + "…" : q.quote}
                        {q.author && (
                          <span className="not-italic text-gray-600 ml-1">— {q.author}</span>
                        )}
                      </p>
                    </blockquote>
                  ))}
                </div>
              )}

              {/* Source */}
              {s.source_reference && (
                <p className="ml-7 text-[10px] text-indigo-400/60 leading-relaxed">
                  📚 {s.source_reference}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
