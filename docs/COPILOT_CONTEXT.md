# COPILOT PROJECT CONTEXT

## Project
Dating Platform MVP
Repository: Yumis84/dating-platform-mvp

## Current state

The project passed the documentation/migration audit phase and moved into MVP implementation.

Last completed stages:
- Migration documentation repaired and merged
- Canonical migration strategy fixed
- WF_01 architecture decision documented
- audit_events reconciliation migration created
- WF_01 documentation and smoke tests created

## Database architecture

Canonical migrations:

001_users_and_telegram_accounts_schema.sql
- CANONICAL
- creates users and telegram_accounts

002_profiles_schema.sql
003_moderation_schema.sql
004_catalog_schema.sql
005_chat_schema.sql
006_chat_reliability_schema.sql
007_chat_message_moderation_schema.sql

008_audit_events_schema.sql
- reconciliation migration
- creates audit_events
- required by WF_01

Legacy:
- 001_initial_users_schema.sql
- do not use
- contains conflicting old schema

Important:
Never claim audit_events is created by 001-007. It exists only through migration 008.

## WF_01 status

Goal:
Telegram user registration MVP.

Canonical workflow:

n8n/workflows/auth/WF_01_USER_REGISTRATION.json

Do NOT use:

n8n/workflows/registration/WF_01

WF_01 scope:
- receive Telegram data
- create users row
- create telegram_accounts row
- create audit_events row
- return success response

Out of scope:
- roles
- profiles
- AI agent
- moderation
- chats

## Known WF_01 limitations

MVP limitations accepted:
- no idempotency check
- no duplicate registration handling
- no advanced error handling
- no role selection

These are future improvements, not blockers.

## Created documentation

Important files:

- docs/architecture/WF_01_ARCHITECTURE_DECISION.md
- docs/WF_01_IMPLEMENTATION_GUIDE.md
- docs/WF_01_SMOKE_TEST.md
- scripts/dry_run_migrations.sh

## Next technical step

Continue from:

WF_01 IMPLEMENTATION

Tasks:
1. Verify n8n import readiness
2. Configure PostgreSQL credentials in n8n
3. Configure Telegram webhook
4. Run dry-run migrations
5. Execute first real smoke test
6. Verify database rows:
   - users
   - telegram_accounts
   - audit_events

After successful WF_01:
Proceed to WF_02_ROLE_SELECTION.

## Rules for future Copilot agents

Before changing anything:
- read this file
- read PROJECT_STATUS.md
- read MIGRATION_MANIFEST.md
- read MIGRATION_POLICY.md

Do not:
- modify canonical migrations without explicit decision
- use legacy workflow paths
- change Docker/infrastructure during WF tasks
- mix documentation cleanup with implementation work

Always return structured reports:

[COPILOT TASK RESULT]

HEAD:
Changed files:
SQL:
n8n:
Docker:
Code:
Problems:
Next step:
