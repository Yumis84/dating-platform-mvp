-- 004_catalog_schema.sql
-- Migration: catalog-related tables: profile_views, favorites, profile_search_events

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Profile views: history of profile views
CREATE TABLE IF NOT EXISTS profile_views (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  viewer_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_profile_views_profile_id ON profile_views(profile_id);
CREATE INDEX IF NOT EXISTS idx_profile_views_viewer_user_id ON profile_views(viewer_user_id);

COMMENT ON TABLE profile_views IS 'History of profile views for analytics and rate limiting.';

-- Favorites: user favorites / likes
CREATE TABLE IF NOT EXISTS favorites (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  CONSTRAINT uniq_user_profile_favorite UNIQUE (user_id, profile_id)
);
CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_profile_id ON favorites(profile_id);

COMMENT ON TABLE favorites IS 'User favorites (bookmarks) for profiles. Unique per (user_id, profile_id).';

-- Profile search events: analytics of searches performed by users
CREATE TABLE IF NOT EXISTS profile_search_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  filters JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_profile_search_events_user_id ON profile_search_events(user_id);
CREATE INDEX IF NOT EXISTS idx_profile_search_events_created_at ON profile_search_events(created_at);

COMMENT ON TABLE profile_search_events IS 'Stores search queries/filters used by users for analytics and tuning search ranking.';
