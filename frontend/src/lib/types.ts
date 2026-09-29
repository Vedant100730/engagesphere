// EngageSphere shared types — used across frontend components and API calls

export type Platform = "google_maps" | "facebook" | "instagram" | "twitter";
export type Sentiment = "positive" | "negative" | "neutral";
export type IntentCategory = "complaint" | "praise" | "question" | "spam";
export type ReplyStatus = "pending" | "approved" | "edited" | "posted";
export type ConnectionStatus = "live" | "simulated";

export interface Business {
  id: string;
  name: string;
  created_at: string;
}

export interface PlatformConnection {
  id: string;
  business_id: string;
  platform: Platform;
  status: ConnectionStatus;
  created_at: string;
}

export interface FeedbackItem {
  id: string;
  business_id: string;
  platform: Platform;
  author_name: string | null;
  content_text: string;
  rating: number | null;
  sentiment: Sentiment | null;
  intent_category: IntentCategory | null;
  external_id: string | null;
  timestamp: string | null;
  created_at: string;
  reply?: Reply;
}

export interface Reply {
  id: string;
  feedback_item_id: string;
  generated_text: string;
  status: ReplyStatus;
  toxicity_flagged: boolean;
  posted_at: string | null;
  created_at: string;
  // joined fields from feedback_items (returned by list/get reply endpoints)
  platform?: Platform;
  author_name?: string | null;
  content_text?: string;
}

export interface Suggestion {
  id: string;
  business_id: string;
  suggestion_text: string;
  evidence_quotes: EvidenceQuote[] | null;
  source_reference: string | null;
  created_at: string;
}

export interface EvidenceQuote {
  quote: string;
  platform: Platform;
  author: string | null;
}

export interface SentimentStats {
  positive: number;
  negative: number;
  neutral: number;
  total: number;
}

export interface IngestResult {
  business_id: string;
  total_inserted: number;
  total_classified: number;
  platforms: {
    platform: string;
    status: string;
    fetched: number;
    inserted: number;
    skipped: number;
    classified: number;
    error?: string;
  }[];
}

export interface GenerateRepliesResult {
  generated: number;
  skipped: number;
  failed: number;
  toxicity_flagged: number;
}

export interface GenerateSuggestionsResult {
  generated: number;
  suggestions: Suggestion[];
}

// API response wrappers
export interface ListResponse<T> {
  items: T[];
  total: number;
}
