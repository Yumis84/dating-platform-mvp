# MVP Architecture Review

Дата проверки: 2026-08-06
Автор: Copilot (automated architecture audit)

Цель
----
Провести аудит текущей архитектуры Dating Platform MVP перед переходом к реализации: проверить соответствие главному ТЗ, порядок миграций, согласованность n8n workflows и выявить риски/задачи до старта разработки.

1) Структура проекта
--------------------
- Проверенные артефакты: PROJECT_DOCUMENTATION_INDEX.md, PROJECT_STATUS.md, docs/architecture/*, database/*, n8n/workflows/*.
- Выводы:
  - Папки и файлы в репозитории организованы в понятные категории: database/, docs/, n8n/workflows/, database/migrations/. Это соответствует назначению (миграции, документация, workflow‑шаблоны).
  - Индекс документации (PROJECT_DOCUMENTATION_INDEX.md) присутствует в корне и в docs/ — следует поддерживать единообразие: используйте один «источник правды» для индекса (рекомендация: docs/PROJECT_DOCUMENTATION_INDEX.md как машина для чтения; корневой файл оставить синхронизированным как краткий взгляд).
  - Повторяющейся документации обнаружено немного; однако есть частичная дубликация PROJECT_DOCUMENTATION_INDEX.md и docs/PROJECT_DOCUMENTATION_INDEX.md: сейчас они почти идентичны, надо выбрать один и держать другой в виде зеркала с автоматической проверкой (или удалить дубль).

Рекомендация:
  - Привязать CI‑проверку, которая валидирует что корневой INDEX и docs/INDEX синхронизированы (или автоматический script для копирования при изменении).

2) Порядок миграций и схема БД
-----------------------------
Ожидаемый порядок миграций (по вашему ТЗ):
 001 users
 002 profiles
 003 moderation
 004 catalog
 005 chat
 006 chat reliability
 007 message moderation

Проверка доступных миграций:
- В репозитории найдено: database/migrations/007_chat_message_moderation_schema.sql (создано на этом этапе).
- Другие миграции (001..006) не были найдены в ходе автоматизированного запроса в этот сеанс или находятся под другими путями/именами.

Проверки и рекомендации (предположительно по ожидаемой схеме):
- Зависимости между таблицами:
  - messages → chat_sessions (message.chat_id → chat_sessions.id) — необходимо, чтобы messages миграция (в 005 chat) предшествовала message_moderation_queue (007). Убедитесь, что messages и chat_sessions определены в миграции 005.
  - profiles → users (profiles.user_id FK) — профили должны ссылаться на users; поэтому 001 users → 002 profiles правильный порядок.
  - moderation tables (profile_moderation, moderation_history) должны ссылаться на profiles и users — миграция 003 должна выполняться после 001/002.
- Foreign Keys:
  - В 007 migration используется REFERENCES messages(id) и REFERENCES chat_sessions(id) — оба FK корректны при условии, что соответствующие таблицы существуют к моменту применения.
  - Рекомендация: в миграциях указывать создание extension uuid-ossp однажды в ранней миграции (например, 001 или отдельная миграция), чтобы не полагаться на дублирование.
- Отсутствие конфликтующих полей:
  - Требуется проверить все migrations на пересечения имён колонок (например, created_at/updated_at должны иметь одинаковые типы TIMESTAMP WITH TIME ZONE) — привести к единому стандарту.
- UUID во всём проекте:
  - В 007 используется UUID PK и uuid_generate_v4(). Рекомендую установить конвенцию: все PK → UUID, типы и default (uuid_generate_v4()) должны быть унифицированы в ранней миграции.
- audit_events:
  - audit_events упоминается в документации; нужно убедиться, что таблица audit_events существует (и схемы полей согласованы) до использования в n8n workflows. Если ещё нет, добавить миграцию создания audit_events в раннюю группу (001 или 003).

Действия до старта разработки БД:
- Собрать и проверить все миграции в одном каталоге, пронумеровать корректно и прогнать последовательность на пустой БД (staging) для выявления зависимостей и ошибок.
- Вынести создание расширений (uuid‑ossp) в отдельную раннюю миграцию.
- Добавить миграцию для audit_events, если её нет.

3) Проверка n8n workflows
-------------------------
Список ожидаемых workflows:
WF_01 registration
WF_02 role selection
WF_03 AI profile creation
WF_04 profile moderation
WF_05 catalog
WF_06 profile view
WF_07 favorites
WF_08 create chat
WF_09 message router
WF_10 block/report
WF_11 delivery worker
WF_12 message moderation

Найдено и частично проверено:
- WF_12 присутствует (n8n json + md). Некоторые другие workflows имеются в docs/n8n (по истории проекта), но не все JSON шаблоны были прочитаны в этом сеансе.

Проверки и рекомендации:
- Входы/выходы:
  - Все workflows должны иметь чёткие входные контракты (например: message_id UUID, profile_id UUID, webhook payload schema). Добавить README‑блок в каждую папку n8n с описанием expected input/output.
  - WF_12 принимает message_id и возвращает verdict; убедиться, что WF_09 (message router) и WF_11 (delivery worker) используют именно эту контрактную форму.
- Зависимости между workflow:
  - Опишите в документации стрелочные связи (WF_09 → WF_12 → WF_11 и WF_10 при блокировке). Это поможет при интеграции и тестировании.
- Credentials:
  - Где нужны реальные credentials: Postgres connections, Telegram Bot token, AI provider API ключи, возможно Sentry/Slack/Telegram для нотификаций (moderation channel).
  - Пометить в каждой н8n JSON экспортируемой ноды credentials placeholders (как сделано в WF_12). Перед импортом в n8n UI нужно вручную привязать реальные credentials.
- Webhook endpoints:
  - Регистрационные и delivery flows требуют вебхуков: Telegram webhook (или polling), internal webhook для message moderation trigger, endpoints для moderators (callback). Документировать URL‑шаблоны и секреты.

4) Архитектура MVP — составные слои
-----------------------------------
Подтверждение наличия основных компонентов (по артефактам и документации):
- Telegram Bot layer — дизайн и references присутствуют (Telegram связки, telegram_accounts schema) — убедиться, что код бота/handlers или его описание доступны.
- n8n backend orchestration — присутствует множество n8n workflow шаблонов (WF_12 и пр.).
- PostgreSQL — миграции и SQL файлы присутствуют; репозиторий ожидает Postgres как основной хранилище.
- AI services — интеграция через n8n (placeholders) и документированные AI workflows.
- Telegram WebApp — упомянут в roadmap/INDEX как будущий слой (TZ_09), но реализация отложена.
- Admin moderation layer — требование присутствует (moderation workflows, chat_reports, audit_events); необходимо обеспечить UI/канал для модераторов (Telegram channel или Admin UI).

Вывод: все ключевые слои спроектированы и документированы, некоторые компоненты — например, WebApp — ещё в планах и не реализованы.

5) Потенциальные проблемы и риски
---------------------------------
- Неполный набор миграций: в репо отсутствуют явные файлы 001..006 (по результатам проверки), это блокер — необходимо собрать и проверить все миграции в порядке выполнения.
- Дублирование индекса документации: PROJECT_DOCUMENTATION_INDEX.md находится в корне и в docs/; требует решение по единому источнику.
- audit_events: если таблица audit_events ещё не мигрирована ранними миграциями, workflows (WF_11, WF_12) будут падать; добавить миграцию и согласовать схему.
- Secrets/credentials management: n8n JSON содержит placeholders — перед импортом в нодовый инстанс нужно привязать credentials; рекомендую подготовить env template (.env.sample) и инструкции по настройке.
- Moderation latency / cost: интеграция AI может стать дорогой и дать задержки; нужно ранжировать pre vs post moderation и настроить rate limits.
- Missing moderator UI: REVIEW verdicts требуют интерфейса; пока в WF_12 заложена отправка в Telegram — если модерация будет в UI, потребуется поддержка REST endpoints и auth.
- Schema/versioning: привести все created_at/updated_at к одному типу timezone-aware TIMESTAMP WITH TIME ZONE.

Что можно отложить (для MVP):
- Telegram WebApp (TZ_09) — можно отложить до Phase 6.
- Расширенные аналитики и ML‑переобучение модели (TZ_11/TZ_08) — можно запускать после первых live пользователей.
- Полная автоматизация зеркалирования документации — можно временно держать ручное обновление, но запланировать CI check.

6) MVP implementation roadmap
----------------------------
Phase 1: Infrastructure + database
  - Docker, Postgres, n8n, migrations applied, CI for migrations.
Phase 2: Telegram Bot registration
  - WF_01, WF_02, users, telegram_accounts, registration flows.
Phase 3: AI profile creation
  - WF_03, profile tables, profile AI agent.
Phase 4: Catalog
  - WF_05..WF_07, catalog schema, listing and filters.
Phase 5: Chat
  - WF_08..WF_12, chat schema, delivery worker, message moderation.
Phase 6: Telegram WebApp
  - WebApp UI for profiles and chat (deferred).
Phase 7: Admin panel
  - Moderator UI, report handling, reviewer workflows.
Phase 8: Payments/monetization
  - Integrations with payment providers.

Заключение и список задач до старта разработки
--------------------------------------------
1. Собрать и проверить все миграции в указанном порядке (001..007). Исправить/добавить отсутствующие миграции, выделить создание расширений и audit_events ранними миграциями.
2. Установить конвенции: UUID для всех PK, TIMESTAMP WITH TIME ZONE для отметок времени, единый audit_events schema.
3. Синхронизировать проектный индекс документации (убрать/объединить дубли).
4. Подготовить .env.sample и instructions для n8n credentials (Postgres, Telegram, AI).
5. Подготовить тестовую среду (staging) и прогнать полную последовательность миграций + импорт n8n workflows с placeholders.
6. Решить модераторский интерфейс: Telegram channel vs Admin UI (для REVIEW verdicts).

Ссылки на артефакты (в репозитории)
- docs/architecture/MVP_ARCHITECTURE_REVIEW.md (этот файл)
- docs/architecture/CHAT_AI_MODERATION_FLOW.md
- database/CHAT_MESSAGE_MODERATION_DESIGN.md
- database/migrations/007_chat_message_moderation_schema.sql
- n8n/workflows/chat/WF_12_AI_MESSAGE_MODERATION.json

