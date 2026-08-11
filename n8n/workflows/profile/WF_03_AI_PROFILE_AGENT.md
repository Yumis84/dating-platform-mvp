# WF_03: WOMAN AI profile agent (inactive DEV)

This JSON is a repository-only, inactive DEV draft. It has not been imported into n8n.

Input: `user_id`, `session_id`, optional `text`, optional Telegram `photo_file_id`.

The caller must already have created an IN_PROGRESS WOMAN session linked to a DRAFT profile. WF_03 verifies WOMAN role when loading that session.

Text is sent to DeepSeek with a strict JSON contract. `Validate AI Extraction` permits only TZ #2 scalar fields and structured `prices` / `meeting_places`; SQL uses positional parameters.

Progress is recomputed from persisted profile fields and child-row counts. `current_step` is updated to the next missing block and never advanced blindly.

Required completion blocks:

```text
name, age, city, district, height, weight, breast_size,
description, >=1 photo, >=1 price, >=1 meeting place
```

Finalization is a single PostgreSQL statement that completes the session, sets `PENDING_MODERATION`, creates one pending moderation row, and writes an idempotent audit event.

Before any future import, validate the exact n8n node versions, bind existing credentials explicitly, add error/retry routes, and perform a disposable-DB integration test.
