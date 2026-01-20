-- Enable UUID generation (Railway Postgres usually supports pgcrypto)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS listings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source text NOT NULL DEFAULT 'olx',
  url text NOT NULL UNIQUE,
  title text NOT NULL,
  price_value numeric NULL,
  location text NULL,
  scraped_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_listings_scraped_at ON listings (scraped_at DESC);

CREATE TABLE IF NOT EXISTS user_listing_state (
  user_id bigint NOT NULL,
  listing_id uuid NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  state text NOT NULL CHECK (state IN ('seen','liked','skipped')),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(user_id, listing_id)
);

CREATE INDEX IF NOT EXISTS idx_user_listing_state_user_state ON user_listing_state (user_id, state, updated_at DESC);
