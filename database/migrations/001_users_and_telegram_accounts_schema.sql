-- 001_users_and_telegram_accounts_schema.sql
-- Creates users and telegram_accounts tables with UUID primary keys

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  role VARCHAR(16), -- 'MAN' or 'WOMAN'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS telegram_accounts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  telegram_id BIGINT NOT NULL UNIQUE,
  username TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

COMMENT ON TABLE users IS 'Application users. Minimal fields; personal contact is stored in telegram_accounts only.';
COMMENT ON TABLE telegram_accounts IS 'Links users to Telegram accounts; Telegram ID stored here only.';
