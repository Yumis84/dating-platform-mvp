-- 007_chat_message_moderation_schema.sql
-- Migration: message moderation queue for chat messages (AI + admin review)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS message_moderation_queue (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
  chat_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
  status VARCHAR(16) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','APPROVED','BLOCKED','REVIEW')),
  ai_score NUMERIC(5,4),
  flags JSONB,
  reason TEXT,
  processed_by VARCHAR(128), -- NULL for AI, 'admin:<user>' for human
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mmq_status_created ON message_moderation_queue(status, created_at);
CREATE INDEX IF NOT EXISTS idx_mmq_message_id ON message_moderation_queue(message_id);
CREATE INDEX IF NOT EXISTS idx_mmq_chat_id ON message_moderation_queue(chat_id);

COMMENT ON TABLE message_moderation_queue IS 'Queue of messages to be evaluated by AI or human moderators. Stores minimal metadata and verdicts; avoids storing Telegram IDs or extra PII.';
