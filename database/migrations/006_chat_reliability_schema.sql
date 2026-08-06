-- 006_chat_reliability_schema.sql
-- Migration: reliability and moderation support for chat delivery (outbox, rate limits, moderation events)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- message_delivery_queue: outbox table for reliable delivery to external APIs (Telegram)
CREATE TABLE IF NOT EXISTS message_delivery_queue (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
  status VARCHAR(16) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','SENT','FAILED')),
  attempts INT NOT NULL DEFAULT 0,
  last_error TEXT,
  scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  sent_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mdq_status_scheduled ON message_delivery_queue(status, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_mdq_message_id ON message_delivery_queue(message_id);

COMMENT ON TABLE message_delivery_queue IS 'Outbox queue for delivering messages to external services (Telegram). Ensures retry and visibility of failed deliveries.';

-- message_rate_limits: counters for simple rate limiting windows
CREATE TABLE IF NOT EXISTS message_rate_limits (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  action_type VARCHAR(64) NOT NULL, -- e.g., 'send_message'
  counter INT NOT NULL DEFAULT 0,
  window_start TIMESTAMP WITH TIME ZONE NOT NULL,
  window_end TIMESTAMP WITH TIME ZONE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mrl_user_action_window ON message_rate_limits(user_id, action_type, window_start, window_end);

COMMENT ON TABLE message_rate_limits IS 'Sliding or fixed window counters to implement rate limits per user and action type.';

-- chat_moderation_events: records of moderation actions / AI verdicts related to chat messages
CREATE TABLE IF NOT EXISTS chat_moderation_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  chat_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
  message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
  event_type VARCHAR(64) NOT NULL, -- e.g., 'ai_flag','admin_review'
  ai_verdict JSONB, -- model response or flags (if applicable)
  action_taken VARCHAR(64), -- e.g., 'none','hide_message','block_user'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cme_chat_id ON chat_moderation_events(chat_id);
CREATE INDEX IF NOT EXISTS idx_cme_message_id ON chat_moderation_events(message_id);

COMMENT ON TABLE chat_moderation_events IS 'Holds moderation results and actions for chat messages to allow auditing and followup.';

-- Helper notes:
-- - The delivery worker (n8n or background worker) should select PENDING rows with scheduled_at <= now() and attempt delivery.
-- - After N failed attempts the worker should mark the row as FAILED and surface to admins for manual intervention.
-- - message_rate_limits can be implemented as upserts/refreshes per window period; consider using Redis for high throughput counters if needed.
