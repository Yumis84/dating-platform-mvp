# WOMAN profile design

`profiles` is a public WOMAN-profile model in the current product flow. MAN search data is stored separately.

## Scalar fields

- name;
- age;
- city (confirmed display value);
- city_normalized (catalog equality key);
- district;
- height_cm;
- weight_kg;
- breast_size (`NUMERIC(3,1)`, explicitly confirmed numeric size);
- description;
- status.

The AI may extract several scalar fields from one message. It must not silently infer missing values or convert cup letters/body measurements into `breast_size`.

## Child tables

`profile_photos` stores Telegram file IDs and deterministic positions. A DRAFT profile is created before photo collection so production photo rows never need an orphan `profile_id`.

`profile_prices` stores ordered service labels, amounts, currency, optional duration, and description. MAN price matching succeeds when any active price row is in the selected range.

`profile_meeting_places` stores an MVP type (`HER_PLACE`, `HIS_PLACE`, `HOTEL`, `PUBLIC_PLACE`, `OTHER`), label, optional district, description, and position.

## Session and moderation

`profile_ai_sessions.ai_context` keeps conversational/extraction metadata. Persisted fields plus child rows determine completeness; `current_step` is derived from the next missing block.

After explicit confirmation, one transaction changes the profile to `PENDING_MODERATION`, completes the session, creates an idempotent audit event, and queues `profile_moderation`.

Only `ACTIVE` profiles are public. Photos remain Telegram metadata; binaries are not stored.
