-- 002_profiles_schema.sql
-- Migration: profiles and related tables for AI-assisted profile creation (female profiles focus)

-- NOTE: Review before applying to any environment. This migration is for schema design only.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Profiles: main user profile (public-facing)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  display_name TEXT,
  age INTEGER CHECK (age >= 14 AND age <= 120),
  city TEXT,
  description TEXT,
  avatar_file_id TEXT,
  status VARCHAR(32) NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT','PENDING_MODERATION','ACTIVE','BLOCKED','ARCHIVED')),
  moderation_status VARCHAR(32) NOT NULL DEFAULT 'NOT_REQUIRED' CHECK (moderation_status IN ('NOT_REQUIRED','PENDING','APPROVED','REJECTED')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Indexes for profiles
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_profiles_status ON profiles(status);
CREATE INDEX IF NOT EXISTS idx_profiles_moderation_status ON profiles(moderation_status);

COMMENT ON TABLE profiles IS 'User profiles created via AI assistant (female profile flow is primary in MVP step).';
COMMENT ON COLUMN profiles.avatar_file_id IS 'Telegram file_id reference for avatar image.';

-- Profile photos: store Telegram file_ids and ordering
CREATE TABLE IF NOT EXISTS profile_photos (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  telegram_file_id TEXT NOT NULL,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_profile_photos_profile_id ON profile_photos(profile_id);
CREATE INDEX IF NOT EXISTS idx_profile_photos_telegram_file_id ON profile_photos(telegram_file_id);

COMMENT ON TABLE profile_photos IS 'Photos attached to profiles. Stores Telegram file_id so media can be re-used without re-upload.';

-- Profile AI sessions: history of AI-assisted profile creation conversations
CREATE TABLE IF NOT EXISTS profile_ai_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  session_status VARCHAR(32) NOT NULL DEFAULT 'IN_PROGRESS' CHECK (session_status IN ('IN_PROGRESS','COMPLETED','CANCELLED','FAILED')),
  current_step INTEGER DEFAULT 0,
  ai_context JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_profile_ai_sessions_user_id ON profile_ai_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_profile_ai_sessions_status ON profile_ai_sessions(session_status);

COMMENT ON TABLE profile_ai_sessions IS 'Conversation sessions with AI agent for building or editing a profile. Stores context for resuming sessions.';

-- Profile fields history: audit of profile field changes
CREATE TABLE IF NOT EXISTS profile_fields_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  field_name TEXT NOT NULL,
  old_value JSONB,
  new_value JSONB,
  changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_profile_fields_history_profile_id ON profile_fields_history(profile_id);
CREATE INDEX IF NOT EXISTS idx_profile_fields_history_changed_by ON profile_fields_history(changed_by);

COMMENT ON TABLE profile_fields_history IS 'History of changes to profile fields (values stored as JSONB to allow structured fields).';

-- Trigger / helper notes:
-- - Consider adding trigger to update profiles.updated_at on row modification.
-- - Consider adding retention policy for profile_ai_sessions and profile_fields_history to limit storage growth.
