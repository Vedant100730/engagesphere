"use client";

import { useState } from "react";
import { updateReply, postReply } from "@/lib/api";
import type { Reply } from "@/lib/types";

interface Props {
  reply: Reply;
  feedbackItemId: string;
  onUpdate?: (updated: Reply) => void;
}

const STATUS_CONFIG = {
  pending:  { color: "text-amber-400",  bg: "bg-amber-500/10 border-amber-500/20",  label: "Pending review" },
  approved: { color: "text-indigo-400", bg: "bg-indigo-500/10 border-indigo-500/20", label: "Approved" },
  edited:   { color: "text-violet-400", bg: "bg-violet-500/10 border-violet-500/20", label: "Edited" },
  posted:   { color: "text-emerald-400",bg: "bg-emerald-500/10 border-emerald-500/20",label: "Posted" },
};

export default function ReplyCard({ reply: initialReply, onUpdate }: Props) {
  const [reply, setReply] = useState<Reply>(initialReply);
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState(initialReply.generated_text);
  const [loading, setLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const applyUpdate = (updated: Reply) => { setReply(updated); onUpdate?.(updated); };

  const handleApprove = async () => {
    setLoading(true); setActionError(null);
    try { applyUpdate(await updateReply(reply.id, { status: "approved" })); }
    catch (e: unknown) { setActionError(e instanceof Error ? e.message : "Failed"); }
    finally { setLoading(false); }
  };

  const handleSaveEdit = async () => {
    if (!editText.trim()) return;
    setLoading(true); setActionError(null);
    try {
      applyUpdate(await updateReply(reply.id, { generated_text: editText, status: "edited" }));
      setEditing(false);
    }
    catch (e: unknown) { setActionError(e instanceof Error ? e.message : "Failed"); }
    finally { setLoading(false); }
  };

  const handlePost = async () => {
    setLoading(true); setActionError(null);
    try { applyUpdate(await postReply(reply.id)); }
    catch (e: unknown) { setActionError(e instanceof Error ? e.message : "Failed to post"); }
    finally { setLoading(false); }
  };

  const sc = STATUS_CONFIG[reply.status] ?? STATUS_CONFIG.pending;

  return (
    <div className="rounded-xl border border-white/5 bg-[#080B12] p-4 space-y-3">

      {/* Status bar */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-lg border ${sc.bg} ${sc.color}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${reply.status === "posted" ? "bg-emerald-400" : reply.status === "pending" ? "bg-amber-400 animate-pulse" : "bg-current"}`} />
            AI Reply · {sc.label}
          </span>
          {reply.toxicity_flagged && (
            <span className="text-xs px-2 py-1 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20 font-medium">
              ⚠ Manual review required
            </span>
          )}
        </div>
        {reply.status === "posted" && reply.posted_at && (
          <span className="text-xs text-gray-600">
            {new Date(reply.posted_at).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}
          </span>
        )}
      </div>

      {/* Reply text or editor */}
      {editing ? (
        <textarea
          value={editText}
          onChange={e => setEditText(e.target.value)}
          rows={4}
          className="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-sm text-gray-200 resize-none focus:outline-none focus:border-indigo-500/40 leading-relaxed transition-colors"
        />
      ) : (
        <p className="text-gray-300 text-sm leading-relaxed">{reply.generated_text}</p>
      )}

      {actionError && (
        <p className="text-xs text-red-400 bg-red-500/5 rounded-lg px-3 py-2 border border-red-500/15">{actionError}</p>
      )}

      {/* Actions */}
      {reply.status !== "posted" && (
        <div className="flex gap-2 flex-wrap">
          {editing ? (
            <>
              <button onClick={handleSaveEdit} disabled={loading || !editText.trim()}
                className="px-3 py-1.5 text-xs rounded-lg font-medium bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/30 disabled:opacity-50 transition-all">
                {loading ? "Saving…" : "Save changes"}
              </button>
              <button onClick={() => { setEditing(false); setEditText(reply.generated_text); setActionError(null); }}
                className="px-3 py-1.5 text-xs rounded-lg text-gray-500 hover:text-gray-300 border border-white/5 hover:bg-white/5 transition-all">
                Cancel
              </button>
            </>
          ) : (
            <>
              {reply.status === "pending" && (
                <button onClick={handleApprove} disabled={loading}
                  className="px-3 py-1.5 text-xs rounded-lg font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 hover:bg-emerald-500/25 disabled:opacity-50 transition-all">
                  {loading ? "…" : "✓ Approve"}
                </button>
              )}
              <button onClick={() => setEditing(true)} disabled={loading}
                className="px-3 py-1.5 text-xs rounded-lg text-gray-400 border border-white/8 hover:bg-white/5 hover:text-gray-200 disabled:opacity-50 transition-all">
                Edit
              </button>
              {(reply.status === "approved" || reply.status === "edited") && (
                <button onClick={handlePost} disabled={loading}
                  className="px-3 py-1.5 text-xs rounded-lg font-medium bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/30 disabled:opacity-50 transition-all">
                  {loading ? "Posting…" : "↗ Post"}
                </button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
