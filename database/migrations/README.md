# Database migrations

## Unapplied feature drafts

- `009_woman_profile_tz02_schema.sql` — structured WOMAN profile fields, city normalization, prices, and meeting places.
- `010_man_search_context_preferences_schema.sql` — private MAN onboarding context and nullable ranking preferences.

Both files are drafts. Do not include them in a shared/prod migration run without a separate approval, backup, duplicate preflight, and disposable/staging validation.

Place SQL migration files here. The system expects numbered migrations that run in order,
e.g. 001_users_schema.sql, 002_profiles_schema.sql, ... 007_chat_message_moderation_schema.sql.

Keep migrations small and idempotent where possible. Use UUID primary keys and TIMESTAMP WITH TIME ZONE for timestamps by convention.
