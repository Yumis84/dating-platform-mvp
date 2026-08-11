# WF_01 corrected DEV workflow — static verification

Date: 2026-08-11

Status: **STATIC + SERVER DRAFT + SAFE SMOKE + DB INTEGRATION PASS + TELEGRAM TRANSPORT PARTIAL PASS + LIVE-TEST UX PATCH VERIFIED. Imported only as separate inactive DEV/test workflows. Not approved for production activation or publish.**

## Artifact

- Corrected file: `n8n/workflows/registration/WF_01_USER_REGISTRATION_DEV_CORRECTED_56NODE.json`
- The filename is retained for branch continuity; the current graph contains 57 nodes after the live-test UX patch
- Derived from the immutable 54-node DEV snapshot
- Nodes: 57
- Connection sources: 44
- Edges: 57
- SHA-256: `5a2adca23e0cc61b209f69d4f933aee0da4c22b346c32fc6c3de499a97a9a05b`
- Target `meta.instanceId`: `7715b9e43263936ef7d5ead15b70c021d76e29a9bc1abb07d28243b86cc28821`

Three nodes were added to the 54-node source:

- `Is text?`
- `Send fallback (unsupported message)`
- `Send start response?`

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
- Node count: 57
- Unique node names: 57/57
- Unique node IDs: 57/57
- Reachable from `Telegram Trigger`: 57/57
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
- n8n server update validation: PASS, 57 nodes, no warnings on the Telegram test clone
- n8n Workflow SDK validation: PASS, 57 nodes, no warnings
- Draft import target: `eMMEhEMrqFe35F7l` (`WF_01_USER_REGISTRATION_DEV_CORRECTED_57NODE`)
- Imported draft graph: 57 nodes, 57 edges, 57 unique names/IDs, no missing endpoints/references
- Imported draft state: `active = false`, `activeVersionId = null`, `triggerCount = 0`
- Safe pin-data smoke tests: 22/22 PASS (executions `4426`-`4447`)
- All canonical text-onboarding steps `0..9`: PASS, including validation, optional skip, stale-answer protection, and step-9 finalization routing
- Role, `/start`, unknown callback, photo, missing-user/session, and unsupported-message routes: PASS
- Every Telegram, PostgreSQL, and other external node was pinned in these smoke tests; no Telegram API call or database mutation was made
- Test-database SQL schema parsing: 18/18 PASS via `PREPARE` + `DEALLOCATE`, execution `4453`
- SQL-check workflow: `JW6qb1wq00gqlCxN` (`WF_01_DEV_SQL_SCHEMA_CHECK`), 2 nodes, `active = false`, `activeVersionId = null`
- SQL-check statement counts: 18 `PREPARE`, 18 `DEALLOCATE`, 0 `EXECUTE`; PostgreSQL node error: none
- Isolated DB integration workflow: `MfVFPQTSY2LXXPjq` (`WF_01_DEV_DB_INTEGRATION_CHECK`), 2 nodes, `active = false`, `activeVersionId = null`
- DB integration execution `4479`: PASS, 33/33 runtime invariants, `cleanup = VERIFIED`, PostgreSQL node error: none
- Runtime coverage: `users.role = NULL` registration, validated role update, registration/audit idempotency, resumable session, answers `0..9`, pending-photo deduplication, finalization, `PENDING_MODERATION`, `COMPLETED`, preferences mapping, profile-photo positions `0/1`, moderation and duplicate protections
- The DB integration harness contains no Telegram nodes. It uses one synthetic Telegram ID and exact generated identifiers; all created rows are deleted by exact ID in the same PostgreSQL `DO` transaction
- Harness execution `4478` stopped at SQL parse time before DML because the harness generator emitted JavaScript identifier quotes for text literals. The harness-only escaping was corrected and revalidated before successful execution `4479`; corrected WF_01 SQL was unchanged
- Existing `WF_01_USER_REGISTRATION_0001` and `WF_01_USER_REGISTRATION copy` were not overwritten

## Live Telegram transport test

- Isolated workflow: `cXeonlxpKEG9FBzt` (`WF_01_USER_REGISTRATION_TELEGRAM_TEST_56NODE`)
- Test credential: `@test39n8n_bot`; no production Telegram credential was used
- Temporary active version: `c2b34d03-c4f7-4ada-a0c2-6202e33bae21`
- The workflow was activated only for the test window and then deactivated; final state is `active = false`, `activeVersionId = null`
- Webhook executions `4480`-`4503`: 24/24 completed with status `success`
- Registration, role selection, steps `0..9`, finalization, completed-profile `/start`, and no-active-session fallback routes executed without node errors
- Final database state before cleanup: one `PENDING_MODERATION` profile, one `COMPLETED` session at `current_step = 10`, one pending AI moderation row, one `profile_created` audit row, and no photos
- Field mapping was correct for name, age, city, description, interests, purpose, and optional values; `job`, `education`, and `communication_style` were stored as null after the accepted skip command
- `пропуск` is not recognized as an optional-step skip command and was stored literally as `preferences.hobbies = "пропуск"`; `пропустить` is recognized
- An extra `пропустить` advanced step 9 and finalized the profile before the later `ок` message. The `ок` execution correctly followed the no-active-session fallback, but the chat transcript made the responses appear attached to different user messages
- Five rapid `/start` updates each produced a welcome response. Database duplicate protections held, but the transport currently has no per-chat debounce or duplicate `/start` response suppression
- After completion, `/start` consistently followed `Send resume question` (`Анкета уже заполнена.`), while arbitrary text consistently followed `Send fallback (no session)`. The apparently inconsistent chat order was response interleaving, not incorrect branch routing
- Commands such as `посмотреть анкеты` / `покажи анкеты` are outside WF_01 and currently fall through to the no-active-session message
- The photo route was not exercised in this live test
- Cleanup execution `4506`: PASS. It deleted only the current run profile, session, moderation row, and two current audit events; the pre-existing user, Telegram account, and eight earlier audit events were preserved

## Live-test UX patch verification

- `пропуск` is now accepted together with `пропустить`, `skip`, `-`, and `нет` for optional steps 6-9; it is normalized to JSON `null` instead of being stored literally
- `Create audit_event` now always returns the canonical `user_id`, including the idempotent no-insert path, so new and existing users share the same `/start` response gate
- `Load start session` uses `pg_try_advisory_xact_lock` plus a minimal `start_prompt_sent` row in the existing `audit_events` table; a 3-second per-user window suppresses rapid duplicate responses without adding schema
- `Send start response?` has an empty false branch, so a suppressed update makes no Telegram API call
- Completed profiles are represented explicitly by `Load active session` as `status = COMPLETED`, `current_step = 10`, `profile_exists = true`; arbitrary text then replies `Анкета уже заполнена. Просмотр анкет пока не реализован.`
- Local graph validation: 57 nodes, 57 edges, 57 reachable nodes, 57 unique names and IDs, no missing references, no cycles, no expression/placeholder warnings
- n8n Workflow SDK validation: PASS, 57 nodes, no warnings
- Corrected inactive DEV draft: `eMMEhEMrqFe35F7l` (`WF_01_USER_REGISTRATION_DEV_CORRECTED_57NODE`), `active = false`, `activeVersionId = null`
- Inactive Telegram test clone: `cXeonlxpKEG9FBzt` (`WF_01_USER_REGISTRATION_TELEGRAM_TEST_57NODE`), `active = false`, `activeVersionId = null`
- Both saved graphs contain the response gate and exact connections `Create audit_event -> Load start session -> Send start response? -> Has start session?`; the gate's false output is intentionally unconnected
- Updated isolated DB integration execution `4507`: PASS, 35/35 runtime invariants, `cleanup = VERIFIED`, PostgreSQL node error: none
- New DB coverage verifies registration-audit return semantics, completed-profile text routing, the first allowed `/start`, and an immediately repeated suppressed `/start`
- No production workflow was edited, activated, unpublished, or published; no migration was created or applied

## Remaining boundaries

- This is still a canvas snapshot (`nodes/connections/pinData/meta`), not a full workflow export with workflow ID, active state, settings, and draft/active version IDs.
- All 18 SQL statements were parsed and type-checked by the confirmed test PostgreSQL database through `PREPARE`; no prepared statement was executed, so no `INSERT`, `UPDATE`, or `DELETE` took effect.
- A separate isolated integration harness then executed the corrected registration/onboarding/finalization SQL against the confirmed test database. Its latest 35 assertions passed and its final cleanup assertion verified that no synthetic user, Telegram account, profile, session, audit, photo, or moderation rows remained.
- Advisory locks protect executions using this corrected workflow. Absolute cross-system guarantees still require future additive unique indexes after a duplicate-data audit; no migration was created or applied here.
- Existing duplicate profiles/sessions/photos, if already present, are not deleted or reconciled.
- The workflow queues `profile_moderation`; it does not call WF_04 directly. A separate worker/webhook contract is still required if no moderation worker polls this table.
- No photo-count policy was added because no product limit was confirmed.
- The corrected JSON was compiled through the n8n Workflow SDK and saved as separate inactive 57-node DEV/test workflows. The UX patch was verified by isolated database execution; neither workflow was activated or published after the patch.

## Safe next step

With separate approval, temporarily activate only `WF_01_USER_REGISTRATION_TELEGRAM_TEST_57NODE` and repeat the live test with rapid `/start`, the `пропуск` alias, one pending photo, and one post-profile photo. Production publish still requires a separate explicit approval.
