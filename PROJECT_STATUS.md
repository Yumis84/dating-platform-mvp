# Project status — Dating Platform MVP

Текущий статус инфраструктуры и плана работ.

## Этап 0 — Infrastructure
- Статус: 🟩 Завершено
- Комментарии: Подготовлена базовая инфраструктура для разработки (docker-compose, n8n, Postgres, pgAdmin, Adminer, WebApp nginx).

## Этап 1 — Registration / WF_01
- Статус: 🟨 Dry-run готов, real E2E ещё не выполнен
- Канонический workflow: `n8n/workflows/auth/WF_01_USER_REGISTRATION.json`
- Канонические миграции: `001..008`
- Последний dry-run: **47 PASS / 0 FAIL / exit 0**
- Временный контейнер `dating-mvp-dryrun-1786138482` после теста удалён.
- Dry-run подтвердил наличие таблиц, 31 FK, `audit_events`, индексы, UNIQUE `telegram_accounts.telegram_id` и успешную цепочку sample insert `users -> telegram_accounts -> audit_events`.
- Важно: dry-run выполнялся на отдельной тестовой БД. Реальный n8n/рабочая БД ещё не подтверждены.

### Следующий шаг WF_01
1. Проверить текущий git HEAD/diff.
2. Проверить canonical migrations `001..008`.
3. Проверить `scripts/dry_run_migrations.sh`.
4. Проверить `infrastructure/docker-compose.yml` и реальные dev env параметры.
5. Импортировать WF_01 в n8n.
6. Настроить Postgres credential.
7. Настроить/проверить Telegram webhook.
8. Выполнить реальный smoke test.
9. Проверить записи в `users`, `telegram_accounts`, `audit_events`.
10. После успешного WF_01 перейти к WF_02.

Не применять production DB изменения только на основании успешного dry-run.

## Этап 2 — AI Profile
- Статус: 🟩 Workflow design completed
- Комментарии: Дизайн `WF_03_AI_PROFILE_AGENT` готов; миграция профилей подготовлена.

## Этап 2.3 — Moderation
- Статус: 🟩 Database design completed
- Комментарии: Добавлены таблицы `profile_moderation`, `moderation_rules`, `moderation_history` и дизайн модерации.

## Этап 2.4 — AI Moderation
- Статус: 🟩 AI Moderation workflow design completed
- Комментарии: Добавлен `WF_04_AI_MODERATION` design.

## Этап 3 — Catalog
- Статус: 🟩 Catalog design completed
- Комментарии: Добавлены `004_catalog_schema.sql`, дизайн каталога и workflows WF_05/WF_06/WF_07.

## Этап 3.1 — Catalog completed
- Статус: 🟩 Completed
- Комментарии: Favorites endpoint/WF_07, pagination/filters для WF_05 и API design подготовлены.

## Этап 4 — Anonymous Chat
- Статус: 🟩 Chat architecture design completed
- Комментарии: Добавлены `005_chat_schema.sql`, `CHAT_DESIGN.md` и `CHAT_FLOW.md`.

## Этап 4.1 — Chat n8n workflows
- Статус: 🟩 Chat n8n workflow design completed
- Комментарии: Templates для WF_08/WF_09/WF_10 подготовлены.

## Этап 4.2 — Chat reliability
- Статус: 🟩 Chat reliability architecture completed
- Комментарии: Delivery queue, rate limits, moderation events и WF_11 worker design подготовлены.

## Этап 4.3 — AI message moderation
- Статус: 🟩 AI chat moderation design completed
- Комментарии: `message_moderation_queue`, WF_12 и документация модерации подготовлены.

## Database policy

Canonical migration chain:

- `001_users_and_telegram_accounts_schema.sql`
- `002_profiles_schema.sql`
- `003_moderation_schema.sql`
- `004_catalog_schema.sql`
- `005_chat_schema.sql`
- `006_chat_reliability_schema.sql`
- `007_chat_message_moderation_schema.sql`
- `008_audit_events_schema.sql`

Legacy `001_initial_users_schema.sql` — conflicting variant, NOT canonical.

`audit_events` is provided by migration `008_audit_events_schema.sql` and is required by WF_01.

## Current handoff

For a new coding agent, read `docs/AGENT_HANDOFF.md` first. It contains the latest conversation/project context, current dry-run result, what has and has not been verified, and the exact next steps.