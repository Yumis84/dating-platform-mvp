# Registration and role routing

```text
Telegram /start
-> find or create users + telegram_accounts
-> select role
-> persist role + audit
   -> MAN: resolve/confirm name -> city -> catalog choice
   -> WOMAN: create/resume DRAFT profile session -> WF_03
```

## MAN name

Telegram `first_name` is only a suggestion. If present, show `Оставить` / `Изменить`. Persist the explicitly confirmed or manually entered value in `male_search_context`.

## MAN completion

City is normalized at write time. After city, display `Настроить предпочтения` / `Смотреть анкеты`. Preferences are never required.

## Separation

WF_01 owns identity, role routing, and MAN onboarding. WF_03 is WOMAN-only. No MAN public `profiles` row or `profile_ai_sessions` row is created.

Credentials remain in n8n Credentials. Telegram identifiers remain in `telegram_accounts`.
