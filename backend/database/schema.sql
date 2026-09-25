-- EngageSphere Database Schema

-- Businesses
CREATE TABLE IF NOT EXISTS businesses (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Platform connections (one row per platform per business)
CREATE TABLE IF NOT EXISTS platform_connections (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id     UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    platform        TEXT NOT NULL CHECK (platform IN ('google_maps', 'facebook', 'instagram', 'twitter')),
    status          TEXT NOT NULL CHECK (status IN ('live', 'simulated')),
    credentials_ref TEXT,          -- reference key / vault path; never store raw tokens here
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (business_id, platform)
);

-- Feedback items ingested from all platforms
CREATE TABLE IF NOT EXISTS feedback_items (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id      UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    platform         TEXT NOT NULL CHECK (platform IN ('google_maps', 'facebook', 'instagram', 'twitter')),
    author_name      TEXT,
    content_text     TEXT NOT NULL,
    rating           SMALLINT CHECK (rating BETWEEN 1 AND 5),  -- nullable; not all platforms have ratings
    sentiment        TEXT CHECK (sentiment IN ('positive', 'negative', 'neutral')),
    intent_category  TEXT CHECK (intent_category IN ('complaint', 'praise', 'question', 'spam')),
    external_id      TEXT,         -- platform-native comment/review ID for dedup
    timestamp        TIMESTAMPTZ,  -- when the original item was posted on the platform
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_business ON feedback_items(business_id);
CREATE INDEX IF NOT EXISTS idx_feedback_platform ON feedback_items(platform);
CREATE INDEX IF NOT EXISTS idx_feedback_sentiment ON feedback_items(sentiment);

-- AI-generated replies
CREATE TABLE IF NOT EXISTS replies (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feedback_item_id UUID NOT NULL REFERENCES feedback_items(id) ON DELETE CASCADE,
    generated_text   TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'edited', 'posted')),
    toxicity_flagged BOOLEAN NOT NULL DEFAULT FALSE,
    posted_at        TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_replies_status ON replies(status);
CREATE INDEX IF NOT EXISTS idx_replies_feedback ON replies(feedback_item_id);

-- Suggestion Agent output
CREATE TABLE IF NOT EXISTS suggestions (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id      UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    suggestion_text  TEXT NOT NULL,
    evidence_quotes  JSONB,        -- array of {quote, platform, author} objects
    source_reference TEXT,         -- cited best-practice source / URL
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_suggestions_business ON suggestions(business_id);
