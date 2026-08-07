-- 002_profiles_schema.sql
-- Profiles, photos and ai session tables

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status VARCHAR(32) NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT','PENDING_MODERATION','ACTIVE','BLOCKED')),
  name TEXT,
  age INT,
  city TEXT,
  description TEXT,
  interests JSONB,
  preferences JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS profile_photos (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
  telegram_file_id TEXT,
  position INT DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS profile_ai_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
  current_step INT DEFAULT 0,
  ai_context JSONB,
  status VARCHAR(32) DEFAULT 'IN_PROGRESS',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS profile_fields_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  field_name TEXT NOT NULL,
  old_value JSONB,
  new_value JSONB,
  changed_by TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

COMMENT ON TABLE profiles IS 'User profiles persisted after AI assisted creation; minimal PII stored.';
COMMENT ON TABLE profile_ai_sessions IS 'Temporary AI driven sessions for creating or editing profiles.';
COMMENT ON TABLE profile_photos IS 'Metadata references to Telegram file ids; binary data is not stored.';
