# WF_01 role-separated DEV patch specification

Status: repository DEV draft only. Do not import or publish without separate approval.

## Preserved infrastructure

Keep Telegram Trigger, callback acknowledgement, `role:man` / `role:woman`, unknown-callback protection, parameterized registration SQL, role audit, and credential placeholders.

## Required replacement

Do not append the old generic `profile_ai_sessions` questionnaire after every role callback.

```text
Register/resolve Telegram user with role NULL
-> apply first-wins role decision
-> role == MAN
   -> load male_search_context
   -> suggest Telegram first_name when name is missing
   -> keep/change/manual name
   -> save normalized city
   -> catalog choice
-> role == WOMAN
   -> create/resume DRAFT WOMAN profile session
   -> POST every WOMAN TEXT/PHOTO event to WF_03
```

## MAN callbacks

- `man_name:keep`
- `man_name:change`
- `man_preferences:open`
- `man_catalog:open`

Unknown callback data must be acknowledged without changing a role or onboarding state.

Opposite-role callbacks are also acknowledged but rejected. Automatic MAN ↔ WOMAN
conversion is outside this patch.

## MAN states

- `AWAITING_NAME_CONFIRMATION`;
- `AWAITING_MANUAL_NAME`;
- `AWAITING_CITY`;
- `COMPLETED`.

`START` never enters a text-field update. Text mutates name only in
`AWAITING_MANUAL_NAME` and city only in `AWAITING_CITY`.

## SQL rules

- use `$1...$n` query parameters, never interpolate Telegram text into SQL;
- normalize city on write with `normalize_city_name`;
- upsert `male_search_context` by `user_id`;
- serialize registration by Telegram ID and onboarding by canonical user ID;
- keep `users.role=NULL` until the first valid role callback;
- reject an opposite role when `users.role` is already set;
- do not create `profiles` or `profile_ai_sessions` for MAN;
- do not mutate live n8n as part of this repository patch.
