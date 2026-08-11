# Dating Platform MVP — canonical transfer context

Updated: 2026-08-11. Read original TZ files before adapting existing workflow code. GitHub drafts do not prove live n8n state.

## Safety

- PostgreSQL is the transactional source of truth.
- Never apply migrations, modify shared/prod DB, import or publish n8n workflows, change credentials, or merge to main without explicit approval.
- n8n JSON in this repository is inactive design/export material unless live state is separately verified.

## Role separation

```text
role:man
-> resolve/confirm name
-> normalized city
-> [Настроить предпочтения] / [Смотреть анкеты]

role:woman
-> name -> age -> city -> district -> height -> weight -> breast_size
-> description -> photos -> prices -> meeting_places -> moderation
```

MAN data lives in `male_search_context` and optional `male_search_preferences`. A MAN never gets a public `profiles` row or WOMAN `profile_ai_sessions` flow.

Telegram `first_name` may be offered to MAN with `Оставить` / `Изменить`, but only the explicitly confirmed value is stored.

## WOMAN source of truth

Product source: `docs/tz/02_PROFILE_AI_AGENT/TZ_02_Sozdanie_ankety_devushki_AI_Agent.md`.

WF_03 may extract several values from one free-text message. Validated DB fields and child-row counts are the progress truth. `profile_ai_sessions.current_step` is a derived cursor pointing at the next missing block.

Structured formats:

- `breast_size NUMERIC(3,1)`: explicitly confirmed numeric size; ambiguity requires clarification;
- `profile_prices`: ordered service/amount rows;
- `profile_meeting_places`: ordered typed rows with user-facing labels;
- photos: Telegram `file_id` only, linked to a DRAFT profile.

Completion sets `profiles.status = PENDING_MODERATION`, session `COMPLETED`, and creates one pending moderation record in one transaction.

## MAN catalog contract

The candidate WHERE clause contains only:

- ACTIVE profile;
- WOMAN owner;
- normalized city equality.

Preferences are nullable ranking inputs. Only configured preferences are counted.

```text
match_score = considered > 0 ? matched / considered : 0
ORDER BY match_score DESC, matched DESC, created_at DESC, id
```

No preference may be implemented before its corresponding structured WOMAN field exists.

## Draft migrations and workflows

- `009_woman_profile_tz02_schema.sql`: structured WOMAN fields and child tables.
- `010_man_search_context_preferences_schema.sql`: private MAN context/preferences.
- `WF_01_USER_REGISTRATION_MAN_WOMAN_DEV.json`: inactive role-separated DEV draft.
- `WF_03_AI_PROFILE_AGENT.json`: inactive WOMAN-only DEV draft.
- `WF_05_PROFILE_CATALOG_RANKING_DEV.json`: inactive ranked catalog DEV draft.

These files are not applied or imported automatically.
