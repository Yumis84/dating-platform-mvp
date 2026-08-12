# WF_03: WOMAN AI profile agent (inactive DEV)

This JSON is a repository-only, inactive DEV draft. It has not been imported into n8n.

Input: `telegram_id`, `chat_id`, `update_type`, `user_id`, `session_id`,
`profile_id`, optional `message_text`, optional Telegram `photo_file_id`, and
optional `message_id`.

The caller must already have created an IN_PROGRESS WOMAN session linked to a
DRAFT profile. WF_03 verifies WOMAN role and the exact user/session/profile
ownership tuple. Missing, stale, malformed, or mismatched identifiers produce
one controlled `WOMAN_SESSION_NOT_AVAILABLE` response and cannot reach photo,
AI, persistence, cursor, or finalization nodes.

The inactive DEV webhook uses n8n Header Auth. WF_01 must bind the same
DEV-only `httpHeaderAuth` credential through Generic Credential Type. The JSON
contains only a credential placeholder, never a secret. This is a repository
contract, not proof that a particular n8n runtime has imported or accepted it.

Text and the existing structured profile state are sent to DeepSeek with a strict JSON contract. `Validate AI Extraction` permits only TZ #2 scalar fields and explicit collection operations:

- `APPEND` with a complete new value;
- `UPDATE` with an existing row UUID and complete replacement fields;
- `DELETE` with an existing row UUID.

Persistence verifies that UPDATE/DELETE IDs belong to the current profile. APPEND
uses the next position under a per-profile advisory transaction lock and
deduplicates equivalent active values. A later extraction cannot silently replace
position 0.

Photo persistence uses the same per-profile serialization, a unique
`(profile_id, position)` guard, and Telegram `file_id` deduplication.

Progress is recomputed from persisted profile fields and child-row counts. `current_step` is updated to the next missing block and never advanced blindly.

Required completion blocks:

```text
name, age, city, district, height, weight, breast_size,
description, >=1 photo, >=1 price, >=1 meeting place
```

Finalization is a single PostgreSQL statement guarded by both
`profile.status = DRAFT` and `session.status = IN_PROGRESS`. A successful call
completes the session, sets `PENDING_MODERATION`, creates one pending moderation
row, and writes an idempotent audit event. A repeated or stale call returns a
controlled no-op and creates no additional side effects.

The DeepSeek call has a finite timeout. Transport errors and malformed model
JSON route to `WOMAN_PROCESSING_UNAVAILABLE`; they do not reach persistence,
cursor advancement, or finalization.

Before any future import, validate the exact n8n node versions, bind DEV-only
credentials explicitly, execute a real isolated HTTP Request -> Webhook test,
and repeat the disposable-DB integration test on a native PostgreSQL version
matching the target environment.
