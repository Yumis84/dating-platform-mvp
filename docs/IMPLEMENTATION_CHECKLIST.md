# Implementation checklist — first dev run (Dating Platform MVP)

Before the first full developer run of the system, ensure the following steps are completed in order. This checklist covers environment prep, migrations, workflows and basic smoke tests.

1) Prepare clean PostgreSQL
- Provision a fresh Postgres instance (local container / VM / managed instance).
- Create an empty database for the MVP (e.g., `clone_db` or `dating_mvp_dev`).
- Ensure the DB user has permissions for schema creation.

2) Ensure uuid-ossp extension
- Verify or install extension:
  - As a superuser: `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`
- Confirm `uuid_generate_v4()` is available.

3) Apply canonical migrations
- Use `database/MIGRATION_MANIFEST.md` to get the canonical order.
- Prefer copying canonical migrations to a temporary directory (e.g., `migrations_apply/`) and run migrator on that directory to avoid accidental application of conflicting files.
- Apply migrations in order 001..007. Confirm no errors.
- If reconciliation is required (legacy data present), prepare and run `008_reconcile_users_and_audit.sql` (planned).

4) Configure n8n and credentials
- Deploy n8n (local container or service).
- In n8n UI, create Postgres credential with the name used by workflow exports (or update workflow JSONs to match the credential id you created).
- Add Telegram credentials (Bot token) to n8n credentials area.
- Configure any AI provider credentials (if workflows expect them).

5) Import n8n workflows
- Import WF_01_USER_REGISTRATION, WF_02_ROLE_SELECTION, WF_03_AI_PROFILE_AGENT into n8n.
- Keep workflows inactive until testing credentials and DB are verified (optional).
- Update any placeholders in workflow nodes to use actual credentials.

6) Smoke tests (basic end-to-end)
- Test 1: Registration (WF_01)
  - Simulate Telegram webhook with minimal payload (telegram_id, username).
  - Verify: users row created, telegram_accounts row created, audit_events row written.
- Test 2: Role selection (WF_02)
  - Simulate role selection trigger for created user.
  - Verify: users.role updated correctly (value matches canonical constraint), audit_event created.
- Test 3: AI Profile (WF_03)
  - Trigger profile agent start for a WOMAN user; run through a few steps (ai_context updates).
  - Verify: profile_ai_sessions rows created and updated, profile_photos metadata stored, profile created with status PENDING_MODERATION.

7) Post-validation
- Verify indexes exist (e.g., idx_audit_events_user_id, ux_telegram_accounts_telegram_id).
- Verify no orphan audit_events.user_id (if FK applied).
- Check n8n workflow logs for errors and handle template SQL issues (missing variables causing malformed SQL).

8) Notes
- Do NOT run migrations against production.
- If legacy `users.telegram_id` exists, do not drop it until reconciliation has been validated.
- Keep db dumps before any destructive migration.

End of checklist.
