# WF_01 live state — read-only snapshot

Дата фиксации: 2026-08-10

Источник: read-only аудит production n8n через Claude MCP.

## Workflow

- Workflow ID: `WF_01_USER_REGISTRATION_0001`
- Draft version ID: `ef5fc7d8-2c72-40b8-9df3-bd5ca7d6650a`
- Active version ID: `d2678798-5807-4813-8e24-7a819285b298`
- Draft nodes: 19
- Active nodes: 19
- Draft == Active: YES

## Production source of truth

`activeVersion` остаётся production source of truth.

На момент этого snapshot draft уже был безопасно восстановлен из опубликованной production-версии и совпадал с activeVersion по nodes и connections.

Нельзя использовать старый GitHub-export `n8n/workflows/registration/WF_01_USER_REGISTRATION.json` как основу для изменений live WF_01: этот файл содержит устаревший граф и старую модель данных.

## Active node names

1. Telegram Trigger
2. Extract User Info
3. Check user exists
4. User exists?
5. Update telegram_account
6. Create user
7. Create telegram_account
8. Create audit_event
9. Send welcome
10. Is callback?
11. Extract role vars
12. Resolve user
13. User found?
14. Update role
15. answerCallbackQuery
16. Send role confirm
17. Insert role audit
18. answerCallbackQuery (not found)
19. Send start prompt

## Main connections

Callback branch:

`Telegram Trigger -> Is callback? -> Extract role vars -> Resolve user -> User found?`

User found:

`Update role -> Send role confirm -> Insert role audit -> answerCallbackQuery`

User not found:

`answerCallbackQuery (not found) -> Send start prompt`

Message / registration branch:

`Telegram Trigger -> Is callback? -> Extract User Info -> Check user exists -> User exists?`

Existing user:

`Update telegram_account -> Send welcome`

New user:

`Create user -> Create telegram_account -> Create audit_event -> Send welcome`

## Confirmed behavior

- Telegram Trigger: present
- Telegram updates include `message` and `callback_query`
- `role:man`: present
- `role:woman`: present
- `Update role`: present
- `Send role confirm`: present
- callback acknowledgement: present
- DeepSeek / LangChain AI nodes: absent in this current 19-node graph

## Safety rules

Before any future n8n write:

1. Read fresh `get_workflow_details`.
2. Confirm draft still matches intended base.
3. Work only on the full current graph.
4. Verify draft after changes.
5. Never call `publish_workflow` without separate explicit user confirmation.

This document is informational. It does not imply that the GitHub JSON export is synchronized with production.
