# WF_01 corrected DEV workflow — static verification

Date: 2026-08-11

Status: **STATIC + SERVER DRAFT + SAFE SMOKE PASS. Imported only as a separate inactive DEV workflow. Not approved for activation or production publish.**

## Artifact

- Corrected file: `n8n/workflows/registration/WF_01_USER_REGISTRATION_DEV_CORRECTED_56NODE.json`
- Derived from the immutable 54-node DEV snapshot
- Nodes: 56
- Connection sources: 43
- Edges: 56
- SHA-256: `69e4c9d948f562754bfe5c6a21529ebc56f709a01984fdaa46f1f5f6a8e84792`
- Target `meta.instanceId`: `7715b9e43263936ef7d5ead15b70c021d76e29a9bc1abb07d28243b86cc28821`

Two nodes were added to the 54-node source:

- `Is text?`
- `Send fallback (unsupported message)`

This prevents stickers, voice messages, contacts, locations, and documents from being processed as empty onboarding text answers.

## Confirmed decisions implemented

### Registration and role

- New users are created with `users.role = NULL`.
- `man` or `woman` is written only after the validated role callback.
- Registration of the user and Telegram account now happens in one SQL statement under a Telegram-ID advisory transaction lock.
- A conflict cleanup removes a newly-created orphan user if an external concurrent registration wins the Telegram-account conflict.
- Registration audit no longer stores Telegram ID, username, first name, or last name.
- Registration audit is idempotent per user/event type within this workflow.

### Credentials and Telegram nodes

- All Telegram nodes use the server baseline credential ID `iq6xvKahi25BYuys` / `@vstrechi18bot`.
- All Postgres nodes use the server baseline credential ID `caq2JyQzouyoC7gv`.
- Callback nodes explicitly specify `operation = answerQuery`.
- Telegram message nodes explicitly specify `resource = message` and `operation = sendMessage`.
- Unknown callbacks remain isolated from role updates.

Credential IDs are instance-local identifiers, not secrets. No bot token, database password, or credential payload is stored in the JSON.

### SQL safety

- Dynamic values on the main registration, session, answer, photo, finalization, and verification paths use `$1...$N` PostgreSQL parameters.
- Because these nodes remain `n8n-nodes-base.postgres` typeVersion 1 for server compatibility, parameters are supplied through `additionalFields.queryParams` as input-item property names.
- `Insert role audit` retains two direct n8n expressions, but the query is explicitly marked as an n8n expression (`=` prefix) and both values are constrained upstream: the UUID comes from PostgreSQL and role is limited to `man|woman` by callback routing and the update query.
- Profile answer JSON is passed as a PostgreSQL parameter and cast to JSONB; manual quote construction was removed.

The typeVersion 1 parameter format was checked against the official n8n Postgres V1 implementation:

- https://github.com/n8n-io/n8n/blob/master/packages/nodes-base/nodes/Postgres/v1/PostgresV1.node.ts
- https://github.com/n8n-io/n8n/blob/master/packages/nodes-base/nodes/Postgres/v1/genericFunctions.ts

### Session and answer concurrency

- Session find-or-create is serialized by a per-user advisory transaction lock.
- A role callback does not reset an existing `IN_PROGRESS` session.
- If a profile already exists and there is no active session, a repeated role callback does not create a new onboarding session.
- `/start` resumes an active session; for an already-existing profile it returns `Анкета уже заполнена.` instead of starting an implicit overwrite flow.
- `Save answer` locks the current session and updates only when `current_step` matches the validated expected step.
- A stale concurrent answer is not written; the workflow reloads/returns the current step and asks the current question.

### Finalization and field storage

- Finalization revalidates all mandatory context: name, age 18..100, city, description, non-empty interests array, and purpose.
- `purpose`, `hobbies`, `job`, `education`, and `communication_style` are materialized as named keys in `profiles.preferences` JSONB.
- No nonexistent profile columns were introduced.
- Profile upsert, pending-photo materialization, session completion, profile audit, and moderation queue creation now execute inside one PostgreSQL statement/transaction.
- On success:
  - `profiles.status = PENDING_MODERATION`;
  - `profile_ai_sessions.status = COMPLETED`;
  - session `profile_id` is set;
  - `pending_photos` is removed from completed session context;
  - profile audit exists;
  - a pending AI moderation record exists.
- The former downstream mutation nodes are retained as read-only verification nodes:
  - `Verify completed session`;
  - `Verify profile audit`;
  - `Verify moderation queued`.

### Photos

- Pre-profile photos remain in `profile_ai_sessions.ai_context.pending_photos`; no table or column was invented.
- Pending photos are deduplicated before materialization.
- Photo insertion and position calculation are serialized by the same per-user advisory lock used by finalization.
- Adding a new photo to an existing profile now:
  - inserts the photo metadata;
  - sets the profile back to `PENDING_MODERATION`;
  - writes a minimal `profile_photo_added` audit event;
  - ensures a pending AI moderation task exists.
- Duplicate photo delivery is handled idempotently.

## Verification performed

- JSON parse: PASS
- Node count: 56
- Unique node names: 56/56
- Unique node IDs: 56/56
- Reachable from `Telegram Trigger`: 56/56
- Missing connection endpoints: 0
- Missing named node references: 0
- Graph cycles: 0
- `Validate answer` JavaScript syntax: PASS
- PostgreSQL placeholder/query-parameter count checks: PASS
- Unexpected direct SQL expression interpolation warnings: 0
- Telegram credential sets: exactly one, matching server baseline
- Postgres credential sets: exactly one, matching server baseline
- Legacy temporary `SELECT 'man'`: absent
- Legacy `field_value_sql`: absent
- Destructive SQL/migrations: absent
- n8n server node-config validation: 56/56 PASS
- n8n Workflow SDK validation: PASS, 56 nodes, no warnings
- Draft import target: `eMMEhEMrqFe35F7l` (`WF_01_USER_REGISTRATION_DEV_CORRECTED_56NODE`)
- Imported draft graph: 56 nodes, 56 edges, 56 unique names/IDs, no missing endpoints/references
- Imported draft state: `active = false`, `activeVersionId = null`, `triggerCount = 0`
- Safe pin-data smoke tests: 22/22 PASS (executions `4426`-`4447`)
- All canonical text-onboarding steps `0..9`: PASS, including validation, optional skip, stale-answer protection, and step-9 finalization routing
- Role, `/start`, unknown callback, photo, missing-user/session, and unsupported-message routes: PASS
- Every Telegram, PostgreSQL, and other external node was pinned in these smoke tests; no Telegram API call or database mutation was made
- Test-database SQL schema parsing: 18/18 PASS via `PREPARE` + `DEALLOCATE`, execution `4453`
- SQL-check workflow: `JW6qb1wq00gqlCxN` (`WF_01_DEV_SQL_SCHEMA_CHECK`), 2 nodes, `active = false`, `activeVersionId = null`
- SQL-check statement counts: 18 `PREPARE`, 18 `DEALLOCATE`, 0 `EXECUTE`; PostgreSQL node error: none
- Existing `WF_01_USER_REGISTRATION_0001` and `WF_01_USER_REGISTRATION copy` were not overwritten

## Remaining boundaries

- This is still a canvas snapshot (`nodes/connections/pinData/meta`), not a full workflow export with workflow ID, active state, settings, and draft/active version IDs.
- All 18 SQL statements were parsed and type-checked by the confirmed test PostgreSQL database through `PREPARE`; no prepared statement was executed, so no `INSERT`, `UPDATE`, or `DELETE` took effect.
- Advisory locks protect executions using this corrected workflow. Absolute cross-system guarantees still require future additive unique indexes after a duplicate-data audit; no migration was created or applied here.
- Existing duplicate profiles/sessions/photos, if already present, are not deleted or reconciled.
- The workflow queues `profile_moderation`; it does not call WF_04 directly. A separate worker/webhook contract is still required if no moderation worker polls this table.
- No photo-count policy was added because no product limit was confirmed.
- The corrected JSON was compiled through the n8n Workflow SDK and imported as a separate inactive DEV workflow. It was exercised only with pinned external nodes, and it was not activated or published.

## Safe next step

Run a deliberately isolated end-to-end test with a dedicated Telegram test account against the confirmed test database, then inspect the created rows and moderation state. Production publish still requires a separate explicit approval.

