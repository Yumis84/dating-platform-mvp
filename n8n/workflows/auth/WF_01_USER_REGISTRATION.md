# WF_01: User Registration

Trigger: Telegram webhook when a user starts or sends /start

Purpose
-------
Create a new user record (UUID primary key) and link Telegram account to that user. Insert an audit_event recording registration. Return a welcome message to the user.

Flow summary
------------
1. Receive Telegram webhook payload with telegram_id and optional username.
2. Extract telegram_id and username; map to internal user creation.
3. Create users row (id UUID DEFAULT uuid_generate_v4(), role NULL initially).
4. Insert telegram_accounts row linking telegram_id to user_id.
5. Insert audit_event with minimal metadata (user_id and event_type).
6. Respond to Telegram via platform relay with a welcome message (the actual Telegram send should be performed by platform delivery flow — here we return payload to the webhook caller).

Privacy rules
-------------
- Telegram ID is stored only in telegram_accounts table. Do not duplicate Telegram ID into other tables.
- Store minimal metadata in audit_event; do not include raw Telegram update payloads.

Credentials and placeholders
----------------------------
- Postgres credential uses placeholder POSTGRES_PLACEHOLDER in exported n8n JSON. Bind correct credentials in n8n UI before importing.
- Do not commit real tokens or secrets.
