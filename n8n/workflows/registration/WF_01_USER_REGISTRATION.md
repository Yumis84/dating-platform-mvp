# WF_01 registration and role routing

Canonical product routing:

```text
/start -> user/account registration -> role callback
MAN -> confirm or enter name -> normalized city -> preferences/catalog choice
WOMAN -> create/resume DRAFT profile session -> WF_03
```

WF_01 must preserve callback acknowledgement, unknown-callback protection, duplicate registration protection, parameterized SQL, and audit logging.

MAN state is private `male_search_context`; optional settings are `male_search_preferences`. WF_01 must not create a MAN public profile or send MAN through WOMAN `profile_ai_sessions` questions.

Corrective DEV contract:

- `Register or Resolve Telegram User` serializes by Telegram ID, creates `users(role=NULL)` and `telegram_accounts` atomically for a new account, and always returns the canonical `user_id`;
- `/start`, `/start payload`, `/start@bot`, and `/start@bot payload` are `START`; `/start123` is not;
- the first valid role wins; a later opposite callback is acknowledged and rejected without creating opposite-role data;
- MAN states are `AWAITING_NAME_CONFIRMATION`, `AWAITING_MANUAL_NAME`, `AWAITING_CITY`, and `COMPLETED`;
- arbitrary text changes MAN data only in one of the two text-accepting states;
- WOMAN `TEXT` and `PHOTO` events are POSTed to `WF_03_TRIGGER_URL`.

WF_01 → WF_03 payload:

```text
telegram_id, chat_id, update_type, message_text, photo_file_id,
message_id, user_id, profile_id, session_id
```

The repository file `WF_01_USER_REGISTRATION_MAN_WOMAN_DEV.json` is an inactive architecture draft. It is not a production export and must not be imported or published without separate verification and approval.
