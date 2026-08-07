# COPILOT / CODING AGENT PROJECT CONTEXT

## Project
Dating Platform MVP
Repository: `Yumis84/dating-platform-mvp`
Local project: `/root/project-mvp`

## Current handoff

Read `docs/AGENT_HANDOFF.md` first. It contains the current context after the latest WF_01 dry-run and replaces stale assumptions from earlier Copilot sessions.

## Current state

The project is in **MVP implementation**, not documentation-only mode.

Latest verified dry-run result from the user's latest log:

- PASS: **47**
- FAIL: **0**
- EXIT CODE: **0**
- temporary container `dating-mvp-dryrun-1786138482` was stopped and removed

This was an isolated test database. It does **not** prove that the real n8n workflow or real development/production database is working yet.

## Database architecture

Canonical migration chain:

001_users_and_telegram_accounts_schema.sql
002_profiles_schema.sql
003_moderation_schema.sql
004_catalog_schema.sql
005_chat_schema.sql
006_chat_reliability_schema.sql
007_chat_message_moderation_schema.sql
008_audit_events_schema.sql

`008_audit_events_schema.sql` is the reconciliation migration that creates/reconciles `audit_events` and is required by WF_01.

Legacy:
- `001_initial_users_schema.sql` — conflicting legacy schema; do not use.

Never claim that 001–007 create `audit_events`.

## WF_01

Canonical workflow:

`n8n/workflows/auth/WF_01_USER_REGISTRATION.json`

Scope:
- receive Telegram data;
- create `users` row;
- create `telegram_accounts` row;
- create `audit_events` row;
- return success response.

Do not use the duplicate/legacy path `n8n/workflows/registration/`.

Accepted current MVP limitations:
- no idempotency;
- no duplicate-registration handling;
- no advanced error handling;
- no role selection inside WF_01.

These are not blockers unless the tests/TZ explicitly require them.

## Latest dry-run checks

Verified in the temporary database:

- expected chat/reliability/moderation tables exist;
- 31 foreign keys exist;
- `audit_events` exists;
- `audit_events` has 5 columns;
- `audit_events` has 5 indexes;
- `audit_events.user_id` FK exists;
- `users` schema is present;
- `telegram_accounts` schema is present;
- UNIQUE constraint/index for `telegram_accounts.telegram_id` exists;
- sample insertion `users -> telegram_accounts -> audit_events` succeeds;
- all 47 checks pass.

The old result `PASS=26 / FAIL=21` is stale and must not be treated as current.

## Next technical step

Continue **WF_01 IMPLEMENTATION**:

1. inspect current repo and git diff;
2. verify migration files and dry-run script;
3. inspect `infrastructure/docker-compose.yml` and env example;
4. determine actual dev Postgres connection from local environment/config, never invent credentials;
5. import canonical WF_01 into n8n;
6. configure Postgres credential;
7. configure/test Telegram webhook;
8. run real WF_01 smoke test;
9. verify rows in `users`, `telegram_accounts`, `audit_events`;
10. only then move to WF_02.

Do not apply production DB changes merely because dry-run passed.

## Related documentation

Start with:

- `docs/AGENT_HANDOFF.md`
- `PROJECT_STATUS.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/MIGRATION_MANIFEST.md`
- `database/MIGRATION_POLICY.md`
- `docs/WF_01_IMPLEMENTATION_GUIDE.md`
- `docs/WF_01_SMOKE_TEST.md`
- `n8n/workflows/auth/WF_01_USER_REGISTRATION.json`
- `n8n/workflows/auth/WF_01_USER_REGISTRATION.md`
- `infrastructure/docker-compose.yml`
- `scripts/dry_run_migrations.sh`

## Rules for future coding agents

Before changing anything:
- read `docs/AGENT_HANDOFF.md`;
- inspect current git HEAD/diff;
- identify canonical files before editing;
- do not use legacy workflow paths;
- do not modify canonical migrations without an explicit technical reason;
- do not change Docker/infrastructure unnecessarily during WF work;
- do not mix documentation cleanup with implementation work;
- do not invent secrets/credentials/IDs/URLs.

Working MVP is the priority.

## Report format

After each significant step:

[AGENT TASK RESULT]

HEAD:
Changed files:
SQL:
n8n:
Docker:
Code:
Tests:
Problems:
Next step:
