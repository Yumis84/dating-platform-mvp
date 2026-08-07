# WF_01 n8n Setup Guide

## Purpose

This document describes runtime setup for the canonical MVP workflow:

`n8n/workflows/auth/WF_01_USER_REGISTRATION.json`

Scope:
- Telegram user registration
- users creation
- telegram_accounts linking
- audit_events logging

Out of scope:
- role selection (WF_02)
- profile creation (WF_03)
- AI agent logic

## Requirements

Before import:

- PostgreSQL with canonical migrations:
  - `database/migrations/001_users_and_telegram_accounts_schema.sql`
  - `database/migrations/008_audit_events_schema.sql`
- n8n instance running
- Telegram bot configured

## PostgreSQL credential setup

In n8n:

1. Open Credentials.
2. Create PostgreSQL credential.
3. Fill:
   - Host
   - Database
   - User
   - Password
   - Port
   - SSL settings if required
4. Save credential.

The workflow JSON contains `POSTGRES_PLACEHOLDER`. Replace it with the real n8n credential during import/setup.

## Workflow import

Import only:

`n8n/workflows/auth/WF_01_USER_REGISTRATION.json`

Do not import:

`n8n/workflows/registration/WF_01_USER_REGISTRATION.json`

The registration folder version is legacy and not part of MVP runtime.

## Webhook configuration

Workflow webhook:

```
POST /user-registration
```

After activation n8n provides a production webhook URL.

Example:

```
https://your-n8n-domain/webhook/user-registration
```

## Telegram webhook payload example

WF_01 expects Telegram-style payload:

```json
{
  "body": {
    "message": {
      "from": {
        "id": 123456789,
        "username": "example_user"
      }
    }
  }
}
```

Extracted values:

- telegram_id
- telegram_username

## Smoke test

Example:

```bash
curl -X POST https://your-n8n-domain/webhook/user-registration \
-H "Content-Type: application/json" \
-d '{"body":{"message":{"from":{"id":123456789,"username":"test_user"}}}}'
```

Expected:

- HTTP 200 response
- users row created
- telegram_accounts row created
- audit_events row created

## Verification SQL

```sql
SELECT * FROM users ORDER BY created_at DESC LIMIT 5;
```

```sql
SELECT * FROM telegram_accounts ORDER BY created_at DESC LIMIT 5;
```

```sql
SELECT * FROM audit_events ORDER BY created_at DESC LIMIT 5;
```

## Security checklist

Required:

- no Telegram bot tokens inside workflow JSON
- no database passwords inside workflow JSON
- use n8n credentials
- do not store raw Telegram updates

## Known MVP limitations

Current WF_01 intentionally does not include:

- duplicate registration handling
- retry/error branches
- role selection
- profile creation

These are planned for later workflow iterations.
