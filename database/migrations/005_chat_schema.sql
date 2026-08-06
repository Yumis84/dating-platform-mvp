-- 005_chat_schema.sql
-- Migration: anonymous chat module schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- chat_sessions: session between two users (initiator and respondent), linked to a profile
CREATE TABLE IF NOT EXISTS chat_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  initiator_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  respondent_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN','CLOSED','BLOCKED','ARCHIVED')),
  started_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  last_message_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_profile_id ON chat_sessions(profile_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_initiator ON chat_sessions(initiator_user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_respondent ON chat_sessions(respondent_user_id);

COMMENT ON TABLE chat_sessions IS 'Anonymous chat sessions between a user and a profile owner; profile_id references the female profile in the catalog.';

-- messages: messages sent within a chat session
CREATE TABLE IF NOT EXISTS messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  chat_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  sender_id UUID REFERENCES users(id) ON DELETE SET NULL,
  content TEXT,
  content_type VARCHAR(32) NOT NULL DEFAULT 'text' CHECK (content_type IN ('text','photo','sticker','other')),
  telegram_message_id TEXT, -- optional metadata for delivery tracking (do not expose to counterpart)
  metadata JSONB, -- additional message metadata (e.g., media file_id reference stored securely)
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

COMMENT ON TABLE messages IS 'Stores chat messages. Message metadata may contain non-PII (e.g., telegram_file_id) and should be treated as sensitive.';

-- chat_blocks: who blocked whom within a session
CREATE TABLE IF NOT EXISTS chat_blocks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  chat_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
  blocker_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  blocked_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  reason TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_blocks_chat_id ON chat_blocks(chat_id);
CREATE INDEX IF NOT EXISTS idx_chat_blocks_blocker ON chat_blocks(blocker_user_id);

COMMENT ON TABLE chat_blocks IS 'Records of blocking actions in chats. Blocking should immediately prevent further messages from the blocked party.';

-- chat_reports: reports/complaints filed for a chat or user
CREATE TABLE IF NOT EXISTS chat_reports (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  chat_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,
  reporter_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  reported_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  report_type VARCHAR(64), -- e.g., 'abuse','spam','fraud','harassment'
  comment TEXT,
  report_data JSONB, -- optional structured data for moderators
  status VARCHAR(32) NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN','IN_REVIEW','RESOLVED','REJECTED')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_reports_chat_id ON chat_reports(chat_id);
CREATE INDEX IF NOT EXISTS idx_chat_reports_reporter ON chat_reports(reporter_user_id);

COMMENT ON TABLE chat_reports IS 'User-submitted reports related to chats for moderator review.';

-- Helper notes:
-- - Consider enforcing that messages cannot be inserted into chat_sessions with status = 'BLOCKED' or 'CLOSED' via application logic or DB trigger.
-- - Implement TTL / archival for messages and sessions according to privacy policy.
