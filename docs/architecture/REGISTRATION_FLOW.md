# Registration flow (architecture)

Sequence diagram (high level):

Telegram Client (user)
        ↓
Telegram Bot (receives /start) —> n8n Telegram Trigger
        ↓
n8n workflow:
  - Extract user info (telegram_id, username, first_name, last_name)
  - Query PostgreSQL (users) to check existing user
  - If exists: update last_login_at, create audit event
  - If new: insert into users, telegram_accounts, audit_events
        ↓
PostgreSQL (users, telegram_accounts, audit_events)
        ↓
n8n -> Telegram Bot: send welcome message with role selection buttons

Notes:
- Telegram is the primary entrypoint (Telegram-first architecture).
- n8n acts as the backend/orchestrator for the registration flow in the MVP.
- PostgreSQL stores minimal user info and audit trail; no sensitive PII is collected at this stage.
