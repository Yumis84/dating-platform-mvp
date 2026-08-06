# WF_01: User Registration (Telegram -> n8n)

Trigger: Telegram Bot Trigger (command `/start`)

Overview
--------
This document describes the registration workflow to be implemented in n8n for the Dating Platform MVP.

Flow summary
------------
1. User sends `/start` to the Telegram bot.
2. Telegram Trigger in n8n receives the update and extracts: telegram_id, username, first_name, last_name.
3. Check if telegram_id exists in `users` table.
   - If exists:
     - Update `telegram_accounts.last_login_at` (or users.updated_at as needed).
     - Create an `audit_events` entry for login.
     - Send greeting message to user.
   - If new:
     - Create `users` record (telegram_id, username, first_name, last_name, role default pending or empty).
     - Create `telegram_accounts` record linked to the created user (store init_data_hash if provided).
     - Create `audit_events` entry for registration.
     - Send welcome message asking to choose role with two buttons: "👤 Мужчина", "👩 Девушка".

Message to user (welcome):
"Добро пожаловать.\nВыберите роль."

Buttons:
- 👤 Мужчина
- 👩 Девушка

Notes and constraints
---------------------
- Do NOT store any sensitive personal data beyond the minimal fields described in the DB schema.
- Workflow should not include real credentials in the exported JSON — use placeholders for credentials and references.
- Business logic (profile creation, catalog, chat) is out of scope — only registration flow should be handled here.
- Telegram button replies should be processed by a follow-up workflow (e.g., WF_02_ROLE_SELECTION) which will set the user's role.

Operational details
-------------------
- Use PostgreSQL nodes to run parameterized queries (SELECT / INSERT / UPDATE). Ensure queries are safe and use prepared statements where possible.
- Add retries / error handling in n8n (on-failure branch) to record errors in audit_events and notify admin if necessary.

