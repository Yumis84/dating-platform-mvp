-- 008_audit_events_schema.sql
-- Reconciliation migration: creates audit_events table required by WF_01, WF_02, WF_03

-- CONTEXT:
-- Canonical migrations 001-007 do not create audit_events table.
-- audit_events is required by WF_01 (user registration), WF_02 (role selection),
-- WF_03 (AI profile agent) and other workflows for audit logging.
-- This migration resolves the blocker by creating the table separately.

-- REFERENCE:
-- docs/MIGRATION_MANIFEST.md — canonical migration order
-- database/MIGRATION_POLICY.md — audit_events structure guidelines
-- docs/architecture/WF_01_ARCHITECTURE_DECISION.md — WF_01 MVP scope

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: audit_events
-- Stores audit trail of user actions and workflow events
-- Used by: WF_01 (registration), WF_02 (role selection), WF_03 (profile creation),
-- WF_04+ (moderation, chat events)
CREATE TABLE IF NOT EXISTS audit_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  event_type TEXT NOT NULL,
  event_data JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Indexes for common queries
-- user_id: fast lookup of events by user (audit trail per user)
CREATE INDEX IF NOT EXISTS idx_audit_events_user_id ON audit_events(user_id);

-- event_type: fast lookup of events by type (admin reporting, analytics)
CREATE INDEX IF NOT EXISTS idx_audit_events_event_type ON audit_events(event_type);

-- event_type + created_at: combined index for reporting filtered by type and time
CREATE INDEX IF NOT EXISTS idx_audit_events_event_type_created ON audit_events(event_type, created_at DESC);

-- created_at: fast lookup of recent events (timeline)
CREATE INDEX IF NOT EXISTS idx_audit_events_created_at ON audit_events(created_at DESC);

-- Comments for documentation
COMMENT ON TABLE audit_events IS 'Audit trail for user actions and workflow events. Required by WF_01-WF_03 and beyond. Stores minimal data; does not include raw Telegram payloads or PII beyond user_id.';
COMMENT ON COLUMN audit_events.user_id IS 'Reference to users table. NULL for system-generated events. ON DELETE SET NULL to preserve audit history even if user is deleted.';
COMMENT ON COLUMN audit_events.event_type IS 'Type of event: user_registration, role_selection, profile_created, message_sent, etc. Used for filtering and reporting.';
COMMENT ON COLUMN audit_events.event_data IS 'Optional JSONB payload with event-specific metadata (e.g., {source: "telegram", role: "WOMAN"}). Should not contain raw Telegram updates or PII.';
COMMENT ON COLUMN audit_events.created_at IS 'Timestamp when event was recorded. Immutable; used for sorting and time-based queries.';
