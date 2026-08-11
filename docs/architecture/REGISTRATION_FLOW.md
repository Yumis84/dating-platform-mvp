# Registration and role routing

```text
Telegram /start
-> atomically find or create users(role=NULL) + telegram_accounts
-> select role
-> persist the first valid role; reject a later opposite role
   -> MAN: resolve/confirm name -> city -> catalog choice
   -> WOMAN: create/resume DRAFT profile session
      -> POST TEXT/PHOTO payload to WF_03
```

## MAN name

Telegram `first_name` is only a suggestion. If present, show `Оставить` / `Изменить`. Persist the explicitly confirmed or manually entered value in `male_search_context`.

The resumable states are `AWAITING_NAME_CONFIRMATION`,
`AWAITING_MANUAL_NAME`, `AWAITING_CITY`, and `COMPLETED`. `/start`
resumes the state and is never persisted as a name or city.

## MAN completion

City is normalized at write time. After city, display `Настроить предпочтения` / `Смотреть анкеты`. Preferences are never required.

## Separation

WF_01 owns identity, role routing, and MAN onboarding. WF_03 is WOMAN-only. No MAN public `profiles` row or `profile_ai_sessions` row is created.

Credentials remain in n8n Credentials. Telegram identifiers remain in `telegram_accounts`.
