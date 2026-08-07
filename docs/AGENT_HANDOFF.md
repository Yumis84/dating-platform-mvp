# AGENT HANDOFF — current context

Дата обновления: 2026-08-07
Репозиторий: `Yumis84/dating-platform-mvp`
Локальный проект пользователя: `/root/project-mvp`
Основная ветка: `main`
Последний известный HEAD перед текущей проверкой: `c0aac5eefeb44292f983839694c2ad83fa3c5e98`

## 1. Что происходит сейчас

Пользователь продолжает разработку **Dating Platform MVP** — Telegram-ориентированной платформы знакомств с n8n, PostgreSQL и AI-профилями/модерацией.

Copilot достиг лимита. Этот файл является handoff для нового AI/coding agent. Агент должен сначала прочитать этот файл, `PROJECT_STATUS.md`, `docs/COPILOT_CONTEXT.md`, `docs/PROJECT_CONTEXT.md`, `docs/MIGRATION_MANIFEST.md`, `database/MIGRATION_POLICY.md` и документацию WF_01.

Главное требование пользователя: **строить рабочий MVP, а не только писать документацию**.

## 2. Важное состояние репозитория

Архитектура и документация уже значительно проработаны. Не начинать проект заново и не переписывать архитектуру без необходимости.

Канонические миграции:

- `001_users_and_telegram_accounts_schema.sql`
- `002_profiles_schema.sql`
- `003_moderation_schema.sql`
- `004_catalog_schema.sql`
- `005_chat_schema.sql`
- `006_chat_reliability_schema.sql`
- `007_chat_message_moderation_schema.sql`
- `008_audit_events_schema.sql` — reconciliation migration, необходима для `audit_events`

Legacy:
- `001_initial_users_schema.sql` — НЕ использовать как каноническую схему.

Канонический WF_01:
- `n8n/workflows/auth/WF_01_USER_REGISTRATION.json`
- `n8n/workflows/auth/WF_01_USER_REGISTRATION.md`

Не использовать дубликат из:
- `n8n/workflows/registration/`

WF_02:
- `n8n/workflows/auth/WF_02_ROLE_SELECTION.json`

WF_03:
- `n8n/workflows/profile/WF_03_AI_PROFILE_AGENT.json`

## 3. Что было сделано непосредственно перед handoff

Был запущен **исправленный dry-run миграций и WF_01 smoke test** в отдельном временном Docker-контейнере:

`dating-mvp-dryrun-1786138482`

Контейнер после теста автоматически остановлен и удалён.

Итог теста:

- `PASSED: 47`
- `FAILED: 0`
- `EXIT CODE: 0`
- сообщение скрипта: `All checks passed! Database is ready for WF_01`

Это означает, что **тестовая база, создаваемая dry-run, успешно проходит проверку схемы и базовый smoke test**. Это НЕ означает, что WF_01 уже успешно работает в реальном n8n или что миграции уже применены к production/dev БД.

## 4. Что именно проверил dry-run

### Таблицы

В тестовой БД найдены ожидаемые таблицы, включая:

- `chat_sessions`
- `messages`
- `chat_blocks`
- `chat_reports`
- `message_delivery_queue`
- `message_rate_limits`
- `chat_moderation_events`
- `message_moderation_queue`
- `audit_events`

### Foreign Keys

Найдено:

- `31` foreign key constraints

Проверка прошла.

### audit_events

Проверено:

- таблица существует;
- 5 колонок:
  - `id`
  - `user_id`
  - `event_type`
  - `event_data`
  - `created_at`
- 5 индексов:
  - `audit_events_pkey`
  - `idx_audit_events_created_at`
  - `idx_audit_events_event_type`
  - `idx_audit_events_event_type_created`
  - `idx_audit_events_user_id`
- foreign key для `audit_events.user_id` существует.

### users

Проверены колонки:

- `id | uuid`
- `role | character varying`
- `created_at | timestamp with time zone`
- `updated_at | timestamp with time zone`

### telegram_accounts

Проверены колонки:

- `id | uuid`
- `user_id | uuid`
- `telegram_id | bigint`
- `username | text`
- `created_at | timestamp with time zone`

Также проверено наличие UNIQUE index/constraint для `telegram_id`.

### Smoke test WF_01 simulation

Тестовая транзакция успешно выполнила цепочку:

1. создать `users` с UUID;
2. создать `telegram_accounts` с `user_id` и `telegram_id=123456789`;
3. создать `audit_events` с `event_type='user_registration'` и JSONB `{source: telegram}`;
4. получить результат `1`.

Smoke test завершился `[PASS]`.

## 5. Очень важно: что НЕ было сделано

Не считать завершёнными следующие пункты:

- реальный импорт WF_01 в production n8n;
- настройка реального Postgres credential в n8n;
- настройка Telegram webhook;
- реальный E2E запрос Telegram → n8n → PostgreSQL;
- проверка реальных строк в рабочей БД;
- production deployment миграций.

Dry-run использовал отдельную тестовую БД и временный контейнер. После теста контейнер удалён.

**Не применять изменения к реальной БД только на основании dry-run.** Сначала проверить актуальный `docker-compose`, env и реальные credentials/DB.

## 6. Предыдущая ошибка в контексте, которую новый агент не должен повторять

Ранее в контексте фигурировал старый результат dry-run `PASS=26 / FAIL=21 / exit 1`. Он устарел.

Актуальный результат исправленного dry-run из последнего лога пользователя:

`PASS=47 / FAIL=0 / EXIT CODE=0`.

Нельзя ссылаться на старый результат как на текущее состояние.

## 7. Текущая задача нового агента

Продолжить **WF_01 IMPLEMENTATION**, а не возвращаться к общему проектированию.

Порядок:

1. Прочитать текущий репозиторий и handoff-документы.
2. Проверить текущий git HEAD и diff.
3. Проверить `scripts/dry_run_migrations.sh` и убедиться, что исправления действительно находятся в репозитории.
4. Проверить canonical migration chain `001..008`.
5. Проверить canonical WF_01 JSON/MD.
6. Проверить `infrastructure/docker-compose.yml` и `.env.example`.
7. Определить реальные dev DB credentials только из локального env/config, не придумывать их.
8. Подготовить импорт WF_01 в n8n.
9. Настроить Postgres credential в n8n.
10. Настроить Telegram webhook/test trigger.
11. Выполнить реальный smoke test WF_01.
12. Проверить записи в `users`, `telegram_accounts`, `audit_events`.
13. Только после успешного WF_01 переходить к WF_02.

## 8. WF_01 scope

WF_01 — регистрация Telegram пользователя.

Цепочка:

`Telegram webhook → extract telegram data → users → telegram_accounts → audit_events → response`

WF_01 НЕ должен сейчас заниматься:

- role selection;
- profiles;
- AI profile agent;
- moderation;
- anonymous chat.

Это последующие workflows.

Принятые MVP-ограничения WF_01:

- idempotency пока не реализована;
- duplicate registration handling пока не реализован;
- advanced error handling пока не реализован;
- role selection относится к WF_02.

Не превращать эти ограничения в блокеры текущего WF_01, если только тесты/ТЗ явно не требуют обратного.

## 9. Архитектура MVP

Основные компоненты:

- Telegram Bot
- Telegram WebApp
- n8n
- PostgreSQL
- AI services
- Google Sheets как дополнительное упрощённое хранилище на MVP
- будущий moderation/admin layer

PostgreSQL является source of truth для основных сущностей и очередей.

n8n — оркестратор.

## 10. Главные сущности БД

- `users`
- `telegram_accounts`
- `profiles`
- `profile_photos`
- `profile_ai_sessions`
- `profile_fields_history`
- `audit_events`
- `profile_moderation`
- `moderation_rules`
- `moderation_history`
- `favorites`
- `chat_sessions`
- `messages`
- `chat_blocks`
- `chat_reports`
- `message_delivery_queue`
- `message_rate_limits`
- `chat_moderation_events`
- `message_moderation_queue`

## 11. Контекст предыдущей переписки пользователя

Пользователь хочет создать простой рабочий MVP сервиса знакомств.

Изначальная идея: Telegram-бот, через которого пользователи регистрируются; AI помогает собирать анкеты девушек/пользователей; мужчины могут просматривать анкеты и общаться; предусмотрены каталог, избранное, анонимный чат и модерация.

В проекте уже спроектированы WF_01–WF_12 и соответствующие схемы/документация. Сейчас приоритет — не расширять функциональность, а довести WF_01 до реально работающего E2E состояния.

Стиль работы с пользователем:

- русский язык;
- кратко и по делу;
- команды/пути давать готовыми к копированию;
- не заставлять пользователя повторно рассказывать историю проекта;
- перед изменениями в production всегда явно объяснять, что именно меняется;
- не выдумывать credentials, URL, ID или структуру, если их нет в репозитории/окружении;
- рабочий код важнее красивой документации.

## 12. Формат отчёта нового агента

После каждого существенного шага возвращать:

`[AGENT TASK RESULT]`

`HEAD:`
`Changed files:`
`SQL:`
`n8n:`
`Docker:`
`Code:`
`Tests:`
`Problems:`
`Next step:`

## 13. Первый ответ нового агента

Новый агент должен сказать, что контекст прочитан, и кратко подтвердить:

- repo: `Yumis84/dating-platform-mvp`
- текущий приоритет: WF_01 real implementation;
- последний dry-run: `47 PASS / 0 FAIL / exit 0`;
- тестовый контейнер удалён;
- real DB/n8n E2E ещё не подтверждены;
- далее нужно проверить репозиторий и окружение, затем выполнить реальный WF_01 smoke test.

После этого сразу переходить к проверке файлов/окружения, а не просить пользователя пересказывать проект.
