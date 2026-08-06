--
-- SQL schema placeholder for Dating Platform MVP v1.0
-- This file is intentionally a template and MUST NOT be executed against production DB.
-- TODO: Спроектировать таблицы пользователей, профилей, сообщений, соответствий (matches), сессий и т.п.

-- Пример структуры (заготовка):
-- CREATE TABLE users (
--   id UUID PRIMARY KEY,
--   telegram_id BIGINT UNIQUE,
--   created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
-- );

-- CREATE TABLE profiles (
--   id UUID PRIMARY KEY,
--   user_id UUID REFERENCES users(id),
--   display_name TEXT,
--   bio TEXT
-- );

-- Migrations будут храниться в папке database/migrations
