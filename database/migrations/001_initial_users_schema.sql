-- 001_initial_users_schema.sql
-- Initial migration for user registration module

-- NOTE: Do NOT run against production without review. This migration creates only user-related tables for the registration module.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  telegram_id BIGINT UNIQUE NOT NULL,
  username TEXT,
  first_name TEXT,
  last_name TEXT,
  role VARCHAR(16) DEFAULT 'man' CHECK (role IN ('man','woman','admin')),
  status VARCHAR(16) DEFAULT 'pending' CHECK (status IN ('active','blocked','pending')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Telegram accounts (separate to allow multiple linked Telegram accounts in future)
CREATE TABLE IF NOT EXISTS telegram_accounts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  telegram_id BIGINT,
  init_data_hash TEXT,
  last_login_at TIMESTAMP WITH TIME ZONE
);

-- Audit events for user actions
CREATE TABLE IF NOT EXISTS audit_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID,
  event_type TEXT,
  event_data JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
