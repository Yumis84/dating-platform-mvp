-- 003_moderation_schema.sql
-- Migration: moderation-related tables for profile moderation and rules

-- NOTE: Review before applying to any environment. This migration adds moderation tables only.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: profile_moderation
-- Stores moderation tasks/records for profiles: AI or ADMIN initiated checks
CREATE TABLE IF NOT EXISTS profile_moderation (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  moderator_type VARCHAR(16) NOT NULL CHECK (moderator_type IN ('AI','ADMIN')),
  status VARCHAR(16) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','APPROVED','REJECTED')),
  reason TEXT,
  moderation_data JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_profile_moderation_profile_id ON profile_moderation(profile_id);
CREATE INDEX IF NOT EXISTS idx_profile_moderation_status ON profile_moderation(status);

COMMENT ON TABLE profile_moderation IS 'Moderation tasks/records for profiles. Can be created by AI or ADMIN and store results and metadata.';
COMMENT ON COLUMN profile_moderation.moderation_data IS 'JSONB blob with moderation details (e.g., detected issues, scores, model metadata).';

-- Table: moderation_rules
-- Stores configurable moderation rules used by AI or admin to evaluate profiles
CREATE TABLE IF NOT EXISTS moderation_rules (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  rule_name TEXT NOT NULL,
  description TEXT,
  severity VARCHAR(16) NOT NULL DEFAULT 'MEDIUM' CHECK (severity IN ('LOW','MEDIUM','HIGH','CRITICAL')),
  enabled BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_moderation_rules_name ON moderation_rules(rule_name);

COMMENT ON TABLE moderation_rules IS 'Configurable rules used by the moderation system (AI and Admin) to evaluate profile content.';

-- Table: moderation_history
-- Audit of actions taken on profile moderation tasks and profile status transitions
CREATE TABLE IF NOT EXISTS moderation_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  action TEXT NOT NULL,
  old_status VARCHAR(32),
  new_status VARCHAR(32),
  actor_type VARCHAR(16) NOT NULL CHECK (actor_type IN ('AI','ADMIN','SYSTEM')), -- who performed the action
  actor_id UUID, -- optional reference to admin user or AI run id
  comment TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_moderation_history_profile_id ON moderation_history(profile_id);
CREATE INDEX IF NOT EXISTS idx_moderation_history_actor_id ON moderation_history(actor_id);

COMMENT ON TABLE moderation_history IS 'History of moderation actions and profile status changes for auditing and rollback.';

-- Helper notes:
-- - Consider adding triggers to update profile.updated_at when moderation decisions affect profile rows.
-- - Consider implementing materialized views or queues for admin moderation UI to fetch PENDING items efficiently.
-- - Plan retention/archival for moderation_history and profile_moderation if volumes grow large.
