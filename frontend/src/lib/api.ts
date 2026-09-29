import type {
  FeedbackItem, GenerateRepliesResult, GenerateSuggestionsResult,
  IngestResult, ListResponse, Reply, SentimentStats, Suggestion,
} from "./types";

const BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

// Get token from localStorage
function getToken(): string {
  if (typeof window === "undefined") return "";
  try {
    const u = localStorage.getItem("engagesphere_user");
    return u ? JSON.parse(u).access_token : "";
  } catch {
    return "";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();

  // Render free tier spins down after inactivity — first request can take 30s+.
  // Retry once with a longer timeout so "Failed to fetch" doesn't surface to the user.
  const attemptFetch = () =>
    fetch(`${BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...init?.headers,
      },
      ...init,
    });

  let res: Response;
  try {
    res = await attemptFetch();
  } catch {
    // First attempt failed (likely Render cold start) — wait 3s and retry once
    await new Promise((r) => setTimeout(r, 3000));
    try {
      res = await attemptFetch();
    } catch (err) {
      throw new Error("Server is waking up — please try again in a moment.");
    }
  }
  if (res.status === 401) {
    localStorage.removeItem("engagesphere_user");
    window.location.href = "/login";
    throw new Error("Session expired");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== "");
  if (!entries.length) return "";
  return "?" + new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString();
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export async function apiSignup(email: string, password: string, business_name: string) {
  return request<{ access_token: string; refresh_token: string; user: { id: string; email: string; business_name: string; business_id: string } }>(
    "/api/auth/signup",
    { method: "POST", body: JSON.stringify({ email, password, business_name }) }
  );
}

export async function apiLogin(email: string, password: string) {
  return request<{ access_token: string; refresh_token: string; user: { id: string; email: string; business_name: string; business_id: string } }>(
    "/api/auth/login",
    { method: "POST", body: JSON.stringify({ email, password }) }
  );
}

// ── Feedback ──────────────────────────────────────────────────────────────────

export async function getFeedback(params?: { platform?: string; sentiment?: string; limit?: number; offset?: number }) {
  return request<ListResponse<FeedbackItem>>(`/api/feedback/${buildQuery(params ?? {})}`);
}

export async function getSentimentStats(): Promise<SentimentStats> {
  const res = await getFeedback({ limit: 500 });
  const stats: SentimentStats = { positive: 0, negative: 0, neutral: 0, total: 0 };
  for (const item of res.items) {
    if (item.sentiment === "positive") stats.positive++;
    else if (item.sentiment === "negative") stats.negative++;
    else if (item.sentiment === "neutral") stats.neutral++;
  }
  stats.total = stats.positive + stats.negative + stats.neutral;
  return stats;
}

// ── Replies ───────────────────────────────────────────────────────────────────

export async function getReplies(params?: { status?: string; limit?: number }) {
  return request<ListResponse<Reply>>(`/api/replies/${buildQuery(params ?? {})}`);
}

export async function updateReply(replyId: string, update: { generated_text?: string; status?: string }) {
  return request<Reply>(`/api/replies/${replyId}`, { method: "PATCH", body: JSON.stringify(update) });
}

export async function postReply(replyId: string) {
  return request<Reply>(`/api/replies/${replyId}/post`, { method: "POST" });
}

export async function generateReplies(): Promise<GenerateRepliesResult> {
  return request<GenerateRepliesResult>("/api/replies/generate", { method: "POST" });
}

// ── Suggestions ───────────────────────────────────────────────────────────────

export async function getSuggestions() {
  return request<ListResponse<Suggestion>>("/api/suggestions/");
}

export async function generateSuggestions(): Promise<GenerateSuggestionsResult> {
  return request<GenerateSuggestionsResult>("/api/suggestions/generate", { method: "POST" });
}

// ── Ingest ────────────────────────────────────────────────────────────────────

export async function ingestFeedback(): Promise<IngestResult> {
  return request<IngestResult>("/api/ingest/", { method: "POST" });
}

export async function classifyFeedback(force = false) {
  return request<{ processed: number; updated: number; failed: number }>(
    `/api/classify/${force ? "?force=true" : ""}`,
    { method: "POST" }
  );
}

// ── Business ──────────────────────────────────────────────────────────────────

export async function getConnections() {
  return request<{ platforms: { platform: string; connected: boolean; status: string }[] }>("/api/business/connections");
}

export async function connectFacebook(access_token: string) {
  return request<{ platform: string; connected: boolean; page_name: string }>(
    "/api/business/connect/facebook",
    { method: "POST", body: JSON.stringify({ access_token }) }
  );
}

export async function connectInstagram(access_token: string) {
  return request<{ platform: string; connected: boolean; username: string }>(
    "/api/business/connect/instagram",
    { method: "POST", body: JSON.stringify({ access_token }) }
  );
}

export async function getOAuthUrl(platform: "facebook" | "instagram"): Promise<string> {
  const res = await request<{ auth_url: string }>(`/api/oauth/${platform}/start`);
  return res.auth_url;
}
