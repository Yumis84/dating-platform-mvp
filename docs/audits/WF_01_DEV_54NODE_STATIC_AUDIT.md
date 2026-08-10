# WF_01 DEV 54-node static audit

Date: 2026-08-11

Status: **FAIL — do not import, activate, or publish this 54-node graph on the server until the critical findings are resolved.**

This report is static and read-only with respect to n8n and PostgreSQL. No live workflow, production version, database, or migration was changed.

## Scope and provenance

### DEV 54-node snapshot

- File: `n8n/workflows/registration/WF_01_USER_REGISTRATION_DEV_54NODE_SNAPSHOT.json`
- Source: first user attachment
- Source SHA-256: `0927230d8f01c12ff3fdd6298ebf3ae65d803d56a818ff6bd4d2d7a8b2b0592b`
- Nodes: 54
- Connection sources: 42
- Edges: 54
- `meta.instanceId`: `5ed5e149a3fe25d96fa35441656f0e3fc5e15ed200ec8fd1874574d9faceb783`

### Server 23-node baseline

- File: `n8n/workflows/registration/WF_01_USER_REGISTRATION_SERVER_23NODE_BASELINE.json`
- Source: second user attachment, described by the user as the server version that was worked on
- Source SHA-256: `c3ea0281fc35326e091eec2cef7204b95ca433ce69dff666b6c73990a1700836`
- Nodes: 23
- Connection sources: 20
- `meta.instanceId`: `7715b9e43263936ef7d5ead15b70c021d76e29a9bc1abb07d28243b86cc28821`

Both attachments are canvas snapshots containing only `nodes`, `connections`, `pinData`, and `meta`. They are not complete workflow exports: workflow name, workflow ID, active state, settings, and version IDs are absent.

Canonical schema sources used for the audit:

- `database/migrations/001_users_and_telegram_accounts_schema.sql`
- `database/migrations/002_profiles_schema.sql`
- `database/migrations/003_moderation_schema.sql`
- `database/migrations/008_audit_events_schema.sql`

## Static checks that passed

- JSON parses successfully and contains exactly 54 nodes.
- All 54 node names and all 54 node IDs are unique.
- Every connection source and target names an existing node.
- All 54 nodes are reachable from `Telegram Trigger`.
- The graph is acyclic.
- Every named `$('Node name')` reference resolves to an existing node.
- `Validate answer` JavaScript passes a syntax parse check.
- Callback routing distinguishes role callbacks from unknown callbacks.
- `/start`, photo, and ordinary-message routes are separated.
- Onboarding state uses `profile_ai_sessions.current_step`; `profiles.status` is not used as a step counter.
- Steps 0..9 match the canonical field order.
- Finalization uses only columns that exist in `profiles` migration 002.
- `pending_photos` is stored as a JSON key inside `profile_ai_sessions.ai_context`; no nonexistent `pending_photos` table or column is referenced.
- `profile_photos.position` is the real migration 002 column.
- `profiles.status = 'PENDING_MODERATION'` and session `status = 'COMPLETED'` match the required lifecycle.
- `profile_moderation(profile_id, moderator_type, status)` matches migration 003.
- No destructive SQL was found.

## Critical findings

### C-01 — DEV credentials belong to a different n8n instance

The 54-node snapshot uses:

- Telegram: ID `IavKZ32AamAnJ72b`, name `Telegram account`
- PostgreSQL: ID `LUwCplWn74xgKcxq`, name `Postgres account`

The server baseline uses:

- Telegram: ID `iq6xvKahi25BYuys`, name `@vstrechi18bot`
- PostgreSQL: ID `caq2JyQzouyoC7gv`, name `Postgres account`

The `meta.instanceId` values also differ. The 54-node graph is therefore not credential-portable to the attached server baseline. Import/paste may leave every Telegram/Postgres node unbound or bound to the wrong credential. Rebind all affected nodes to the exact server credentials and verify in n8n UI before any activation.

### C-02 — Server baseline routes callbacks through a hard-coded test identity

In the 23-node baseline, `Is callback?` connects to `Extract role vars1`, not to the real `Extract role vars`. `Extract role vars1` hard-codes:

- `telegram_id = 7558747925`
- `chat_id = 7558747925`
- `callback_query_id = test-stage1`
- `role = woman`

The real `Extract role vars` node is unreachable. If this graph were active, callbacks from other users could act on the hard-coded account and send messages to the hard-coded chat. The 54-node graph removes this test route, but the baseline must never be restored or published as-is.

### C-03 — Existing profiles accept new photos without moderation

`Save photo metadata` immediately inserts a photo into any existing profile selected by `user_id`, regardless of:

- whether an onboarding session is active;
- whether the profile is `ACTIVE`, `BLOCKED`, or `PENDING_MODERATION`;
- whether the photo is audited or queued for moderation.

A registered user with an existing active profile can send a Telegram photo and append it directly to the public profile without changing profile status or creating a moderation task. This is a moderation bypass. Photo updates must either be limited to an active onboarding/edit session or force the profile/photo through a pending moderation lifecycle.

### C-04 — Finalization is not atomic and can become permanently incomplete

Finalization is split across sequential nodes:

`Finalize profile -> Complete session -> Create profile audit -> Trigger moderation -> Send finalize message`

If audit or moderation insertion fails after `Complete session`, the session is already `COMPLETED`. Ordinary messages then cannot resume it, so retry logic does not repair the missing audit/moderation task. A failure between profile update and session completion also leaves a `PENDING_MODERATION` profile with an `IN_PROGRESS` session.

Profile upsert, pending-photo materialization, session completion, audit creation, and moderation task creation should be committed atomically in one database transaction or supported by an explicit retry/reconciliation path.

## High findings

### H-01 — New users are temporarily assigned `role = 'man'`

Migration 001 allows `users.role` to be `NULL` and has no CHECK constraint. `Create user` nevertheless inserts `'man'` before the user chooses a role. This can permanently misclassify users who register but never press a role button. Insert the user with `role = NULL`; set `man` or `woman` only after a validated role callback.

Lowercase `man`/`woman` is technically accepted by the current schema, although the migration comment mentions uppercase `MAN`/`WOMAN`. The application needs one explicit canonical casing before any future constraint is added.

### H-02 — Active-session find-or-create has a race condition

`Ensure profile session` uses `existing -> INSERT WHERE NOT EXISTS` without a partial unique index or per-user lock. Two concurrent role callbacks can create two `IN_PROGRESS` sessions for the same user. The same risk exists anywhere this pattern is retried concurrently.

### H-03 — Registration can create orphan users

`Create user` and `Create telegram_account` are separate statements. Concurrent `/start` executions can each insert a user, while `ON CONFLICT (telegram_id) DO NOTHING` allows only one Telegram account link. The losing execution can leave an unlinked user and may write an audit event for the wrong/new user ID.

### H-04 — Concurrent answers can overwrite each other

`Save answer` updates by session ID and status only. It does not require `current_step` to equal the step validated by `Validate answer`. Two messages processed from the same loaded step can both pass validation, overwrite the same field, and set the same next step. On step 9 they can also enter finalization concurrently.

Add optimistic concurrency (`WHERE current_step = expected_step`) and handle a zero-row update by reloading the session, or serialize per-user/session execution.

### H-05 — Profile finalization can create duplicate profiles

Migration 002 has no `UNIQUE(profiles.user_id)`. `Finalize profile` uses `existing -> UPDATE/INSERT WHERE NOT EXISTS`, which is not safe against concurrent finalizations. Two executions can both insert a profile.

### H-06 — Photo positions and duplicate protection are race-prone

Both immediate photo insertion and pending-photo materialization use `MAX(position) + 1` and `NOT EXISTS` without database uniqueness. Concurrent uploads can receive the same position or duplicate the same Telegram file ID. The schema has no unique constraint for `(profile_id, position)` or `(profile_id, telegram_file_id)`.

### H-07 — Five collected fields are not materialized into the profile

`purpose`, `hobbies`, `job`, `education`, and `communication_style` remain only in the completed session's `ai_context`. `Finalize profile` persists only name, age, city, description, and interests. Consequently the public profile and a moderation workflow that reads only `profiles` cannot see steps 5..9.

No separate columns exist, so inserting invented columns is forbidden. With the current schema, the least invasive durable mapping is to store these named values in `profiles.preferences` JSONB. That product mapping should be explicitly confirmed before a corrected workflow is produced.

### H-08 — Finalization does not revalidate required context

Finalization trusts `current_step >= 10` and does not verify that name, valid age, city, description, interests, and purpose are present. A damaged, legacy, or manually edited session can create a `PENDING_MODERATION` profile with missing required data.

### H-09 — Audit events contain identifiers and personal names contrary to migration guidance

Migration 008 says audit payloads should not contain raw Telegram payloads or PII beyond `user_id`. The registration audit stores Telegram ID, username, first name, and last name. Role audit also stores Telegram ID and callback query ID. This is a privacy/data-retention mismatch with the canonical migration comments.

### H-10 — A new onboarding silently overwrites an existing profile

When an existing user has no active session, `/start` offers role selection. A repeated role callback creates a new session, and finalization updates the first existing profile and resets it to `PENDING_MODERATION`. There is no explicit create-vs-edit decision, confirmation, or deterministic profile selection if duplicate profiles already exist.

## Medium findings

### M-01 — SQL uses direct expression interpolation instead of query parameters

The workflow manually escapes some strings, but still interpolates IDs, callback IDs, file IDs, UUIDs, JSON text, and field paths directly into SQL. Current validation reduces several attack paths, but the approach is brittle and dependent on every upstream assumption. Use Postgres query parameters/query replacements supported by the actual node version.

### M-02 — Audit and moderation idempotency is not concurrency-safe

`Create profile audit` and `Trigger moderation` use `WHERE NOT EXISTS`, but there is no matching unique constraint. Concurrent finalization can still create duplicate audit or pending moderation rows.

### M-03 — Non-text Telegram messages enter text validation

After callback/photo/start checks, all remaining messages go to `Extract message vars`. Stickers, voice messages, contacts, locations, and documents have no `message.text`; they are treated as empty answers and produce misleading validation errors. Add an explicit text-message guard and a suitable fallback.

### M-04 — Snapshot metadata is incomplete

The 54-node attachment is sufficient for canvas-level static analysis but cannot prove workflow identity, draft version, active version, activation state, settings, or exact server provenance. A future full export or read-only workflow-details snapshot should include these values.

### M-05 — `Trigger moderation` creates a DB record but does not invoke WF_04

The node inserts a `profile_moderation` row only. It does not call the documented WF_04 webhook. This is acceptable only if another worker polls pending moderation rows; otherwise moderation never starts. Confirm the intended dispatch contract.

### M-06 — Telegram callback operation should be verified after import

Callback nodes contain `resource = callback` and `queryId`, but omit an explicit `operation`. This may rely on the n8n node's default for typeVersion 1. The server baseline has the same omission, so static evidence does not prove failure, but imported nodes must be opened/validated to confirm `answerQuery` is selected.

### M-07 — Photo flow has no count/size policy or audit trail

Users can append an unlimited number of Telegram file IDs. The flow records neither upload audit events nor moderation state per photo. This can grow session JSON/profile rows and weakens moderation traceability.

## Required correction order

1. Rebind all 54-node Telegram/Postgres nodes to the exact server credentials; do not guess credential IDs.
2. Ensure the hard-coded 23-node test route is never active or restored.
3. Remove the temporary `role = 'man'` assignment.
4. Close registration/session/answer/profile/photo races using per-user serialization and/or additive unique indexes after a duplicate-data audit.
5. Make finalization atomic or explicitly retryable and reconcilable.
6. Prevent photo moderation bypass; define an edit/photo moderation lifecycle.
7. Confirm the mapping of steps 5..9, preferably to named keys in `profiles.preferences` under the current schema.
8. Parameterize SQL and add finalization-level required-field validation.
9. Remove unnecessary PII from audit payloads.
10. Add a text-message guard and confirm how WF_04 is dispatched.
11. Re-export the full draft with workflow/version metadata and rerun static verification.

## Change boundary

This branch contains evidence and analysis only. The received snapshots were not normalized or corrected. No migration, production workflow, existing architecture document, or `main` branch was modified. A corrected workflow JSON should be produced only after the findings and storage/moderation decisions are approved.
