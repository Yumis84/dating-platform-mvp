# AI context

Updated: 2026-08-11. Read original TZ files and `docs/PROJECT_CONTEXT_TRANSFER.md` before changing product flows.

## Canonical role flows

```text
MAN
-> confirm Telegram first_name or enter name
-> normalized city
-> optional preferences or catalog

WOMAN
-> name -> age -> city -> district -> height -> weight -> breast_size
-> description -> photos -> prices -> meeting_places -> moderation
```

MAN data is private `male_search_context` plus optional `male_search_preferences`. Never create a MAN public `profiles` row or send MAN through WOMAN `profile_ai_sessions`.

WF_03 is WOMAN-only. It uses actual structured AI extraction and may fill several fields from one message. Persisted structured fields and child rows determine completeness; `current_step` is only the next-missing-block cursor.

## Catalog

The only candidate filters are ACTIVE status, WOMAN owner, and normalized city equality. All nullable preferences affect ranking only.

```text
matched_preferences
considered_preferences
match_score = considered > 0 ? matched / considered : 0
```

Do not implement a MAN preference until the corresponding WOMAN field exists in structured schema.

## Data contracts

- Telegram ID only in `telegram_accounts`.
- Telegram photos store `file_id`, never binary data.
- PostgreSQL is source of truth.
- `profile_prices` and `profile_meeting_places` are WOMAN child tables.
- City stores display and normalized values; a future `city_id` remains possible.
- Secrets and credentials never appear literally in workflow JSON.

## Feature drafts

- `009_woman_profile_tz02_schema.sql`;
- `010_man_search_context_preferences_schema.sql`;
- `WF_01_USER_REGISTRATION_MAN_WOMAN_DEV.json`;
- `WF_03_AI_PROFILE_AGENT.json`;
- `WF_05_PROFILE_CATALOG_RANKING_DEV.json`;
- `database/queries/man_catalog_ranking_prototype.sql`.

All are inactive/unapplied repository drafts. Production, shared DB, live n8n, credentials, and Google Sheets require separate approval.
