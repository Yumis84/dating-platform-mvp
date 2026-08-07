# WF_01 Runtime Test Checklist

## Purpose

Checklist for the first real MVP registration test using Telegram + n8n + PostgreSQL.

Scope is limited to:

- `n8n/workflows/auth/WF_01_USER_REGISTRATION.json`
- canonical migrations:
  - `database/migrations/001_users_and_telegram_accounts_schema.sql`
  - `database/migrations/008_audit_events_schema.sql`

Legacy workflow path is not used:

- `n8n/workflows/registration/WF_01_USER_REGISTRATION.json`

## Pre-flight

- [ ] PostgreSQL is running
- [ ] Canonical migrations 001-008 applied
- [ ] n8n PostgreSQL credential created
- [ ] Workflow imported from `auth/` path
- [ ] Credential placeholders replaced with real n8n credential binding
- [ ] Telegram bot webhook configured

## WF_01 validation

Webhook endpoint:

```
POST /webhook/user-registration
```

Expected flow:

1. Receive Telegram payload
2. Extract:
   - telegram_id
   - telegram_username
3. Create `users` row
4. Create `telegram_accounts` row
5. Create `audit_events` row
6. Return HTTP 200 response

## Database verification

After successful webhook call:

```sql
SELECT * FROM users ORDER BY created_at DESC LIMIT 5;

SELECT * FROM telegram_accounts ORDER BY created_at DESC LIMIT 5;

SELECT * FROM audit_events
WHERE event_type = 'user_registration'
ORDER BY created_at DESC
LIMIT 5;
```

Expected:

- one new user UUID
- linked telegram account
- audit event with `event_type='user_registration'`

## Known MVP limitations

Current WF_01 intentionally does not implement:

- duplicate user idempotency
- role selection
- profile creation
- retry/error branches
- moderation

These belong to later workflow stages.

## Security checks

Before production:

- [ ] No Telegram token stored in workflow JSON
- [ ] No database password stored in repository
- [ ] n8n credentials managed through credential store
- [ ] Webhook endpoint protected according to deployment policy

## Ready criteria

WF_01 is accepted when:

- database rows are created correctly
- audit trail is written
- webhook returns success
- no SQL or migration modifications are required
