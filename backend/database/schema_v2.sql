-- EngageSphere Schema v2 — run this in Supabase SQL Editor
-- Safe to run multiple times (IF NOT EXISTS / IF NOT EXISTS guards)

-- Add user_id and email to businesses
ALTER TABLE businesses
  ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  ADD COLUMN IF NOT EXISTS email TEXT;

-- Index for fast user_id lookup
CREATE UNIQUE INDEX IF NOT EXISTS idx_businesses_user_id ON businesses(user_id);

-- Add token columns to platform_connections
ALTER TABLE platform_connections
  ADD COLUMN IF NOT EXISTS access_token TEXT,
  ADD COLUMN IF NOT EXISTS token_expires_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS page_id TEXT,
  ADD COLUMN IF NOT EXISTS ig_user_id TEXT;
