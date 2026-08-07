# AI_CONTEXT

Дата: 2026-08-07
Автор: Copilot (handover snapshot)

Назначение проекта
------------------
Dating Platform MVP — минимально жизнеспособный продукт для анонимных/полуанонимных знакомств через Telegram с поддержкой AI‑помощника для создания профилей, модерацией контента и анонимным чатом.

Краткая цель: обеспечить поток регистрации → создание AI‑сгенерированного профиля → верификация/модерация → показ в каталоге и общение в чате.

Текущая архитектура (высокоуровнево)
-----------------------------------
- Telegram Bot layer — приём обновлений и инициирование WF через вебхуки.
- n8n — оркестратор workflows (регистрация, роль, AI диалог, модерация, чат‑роутинг и т.д.).
- PostgreSQL — единое хранилище данных и source of truth для сущностей и очередей.
- AI services — внешний провайдер для генерации/помощи при создании профиля и модерации.
- Admin moderation layer — (планируется) интерфейс/канал для модераторов (пока: Telegram или нотификации).

Стек технологий
---------------
- Orchestration: n8n (workflow engine)
- Database: PostgreSQL 15
- Containers: Docker + docker-compose
- Migrations: migrate/migrate (containerized migrator)
- Workflows: n8n JSON templates (stored in n8n/workflows/)
- Language/format: SQL (migration files), JSON (n8n workflows), Markdown for docs

Структура репозитория (ключевые папки)
-------------------------------------
- infrastructure/ — docker‑compose.yml, .env.example, README для dev env
- database/migrations/ — SQL миграции (001..)
- n8n/workflows/ — каталоги для workflow шаблонов (auth/, profile/, chat/ и т.д.)
- docs/setup/ — инструкции по запуску dev env и применению миграций
- docs/architecture/ — архитектурные обзоры
- PROJECT_STATUS.md, PROJECT_DOCUMENTATION_INDEX.md — индекс/статусы проекта

Описание рабочих процессов (WF)
------------------------------
WF_01_USER_REGISTRATION
- Триггер: Telegram webhook (n8n webhook).
- Действия:
  1. Извлечь telegram_id и username из тела update.
  2. Создать запись users (UUID PK).
  3. Создать telegram_accounts, связав user_id с telegram_id (telegram_id хранится ТОЛЬКО здесь).
  4. Создать audit_event с типом user_registration и минимальной метаинформацией.
  5. Вернуть приветственное сообщение (или отдаёт полезную нагрузку для delivery flow).
- Примерные ноды: Webhook Trigger → Set (extract) → Postgres (insert user) → Postgres (insert telegram_account) → Postgres (insert audit_event) → Respond.
- Требования: использовать placeholders для Postgres credentials; не хранить лишние PII.

WF_02_ROLE_SELECTION
- Триггер: Webhook при выборе роли от пользователя.
- Вход: user_id, role (MAN|WOMAN).
- Действия:
  1. Валидация роли.
  2. UPDATE users.role.
  3. Create audit_event role_selection.
  4. Если WOMAN → триггер WF_03 (WF_03_TRIGGER_URL); если MAN → интеракция переводит пользователя в каталог (будущий шаг).
- Требования: idempotency, Postgres placeholder credential, WF_03_TRIGGER_URL environment variable.

WF_03_AI_PROFILE_AGENT
- Триггер: Webhook с user_id (от WF_02) и опционально session_id, user_answer, photo_file_id.
- Назначение: вести диалог с пользователем (через Telegram) и собрать профиль; сессии сохраняются в profile_ai_sessions для возможности возобновления.
- Ключевая логика:
  1. Найти существующую сессию: по session_id либо последнюю IN_PROGRESS по user_id; иначе создать новую сессию profile_ai_sessions.
  2. На каждый вход (user_answer) сохранять значение в ai_context JSONB, увеличивать current_step.
  3. Сохранять метаданные фото (telegram_file_id) в profile_photos (не храним бинарные данные).
  4. После заполнения обязательных полей собрать/создать запись в profiles (status = PENDING_MODERATION) и пометить сессию COMPLETED.
  5. Создать audit_event profile_created и триггернуть WF_04 (moderation) с profile_id.
- Обязательные вопросы: name, age, city, description, interests, purpose. Дополнительные: hobbies, job, education, communication_style.
- Поддержка: возобновление сессии, отсутствие дубликатов профиля для одного user_id.
- Требования: placeholder credentials, обработка ошибок AI/Postgres, idempotency.

Список миграций в database/migrations (текущее состояние)
---------------------------------------------------------
- 001_users_and_telegram_accounts_schema.sql — создан (users, telegram_accounts). (added)
- 002_profiles_schema.sql — создан (profiles, profile_photos, profile_ai_sessions, profile_fields_history). (added)
- 007_chat_message_moderation_schema.sql — присутствовал ранее (message_moderation_queue). (existing)

Примечание: миграции 003..006 ожидаются по ТЗ (moderation schema, catalog, chat, reliability), их наличие/местоположение нужно подтвердить. Некоторые миграции (audit_events) упоминаются в документации — убедитесь, что соответствующая миграция/таблица существует в БД; на момент создания этого файла явной миграции audit_events в папке database/migrations не обнаружено в рамках автоматических шагов, требуется подтверждение.

Текущая схема базы данных (основные таблицы и назначение)
---------------------------------------------------------
- users
  - id UUID PK
  - role VARCHAR(16)
  - created_at TIMESTAMP WITH TIME ZONE
  - updated_at TIMESTAMP WITH TIME ZONE
  - Назначение: сущность пользователя приложения (без PII).

- telegram_accounts
  - id UUID PK
  - user_id FK → users(id)
  - telegram_id BIGINT (UNIQUE)
  - username TEXT
  - created_at
  - Назначение: хранение связи с Telegram; Telegram ID хранится только здесь.

- audit_events (описание из документации)
  - используется для хранения событий (registration, role_selection, profile_created и т.д.)
  - Структура: user_id, event_type, event_data JSONB, processed_by?, timestamps. Требует проверки схемы/миграции.

- profiles
  - id UUID PK
  - user_id FK → users
  - status (DRAFT|PENDING_MODERATION|ACTIVE|BLOCKED)
  - name, age, city, description
  - interests JSONB, preferences JSONB
  - timestamps
  - Назначение: карточка профиля, минимальный PII хранится здесь (имя, возраст, город, описание).

- profile_photos
  - id UUID PK
  - profile_id FK (nullable at time фото upload before profile create)
  - telegram_file_id TEXT
  - position INT
  - created_at
  - Назначение: метаданные фото (не храним бинарные данные).

- profile_ai_sessions
  - id UUID PK
  - user_id FK
  - profile_id FK nullable
  - current_step INT
  - ai_context JSONB (накопленные ответы)
  - status (IN_PROGRESS|COMPLETED)
  - timestamps
  - Назначение: хранение состояния AI‑сессии для возобновления/идемпотентности.

- profile_fields_history
  - id UUID PK
  - profile_id FK
  - field_name
  - old_value JSONB
  - new_value JSONB
  - changed_by
  - created_at
  - Назначение: аудирование изменений полей профиля.

- message_moderation_queue
  - id UUID PK
  - message_id FK → messages(id)
  - chat_id FK
  - status (PENDING/APPROVED/BLOCKED/REVIEW)
  - ai_score, flags JSONB, reason, processed_by, timestamps
  - Назначение: очередь модерации сообщений.

Интеграция n8n + Postgres
-------------------------
- n8n использует Postgres как источник данных для workflow нод (Postgres node в n8n). В workflow JSON‑файлах указан placeholder credential (POSTGRES_PLACEHOLDER) — в н8n UI нужно создать credential с реальными значениями и привязать его.
- n8n workflows принимают входы через вебхуки, выполняют SQL‑запросы и HTTP‑вызовы (AI provider, internal webhooks для запуска других WF).
- Dev environment: docker‑compose содержит контейнер n8n, postgres и migrator (migrate/migrate image) — миграции монтируются в контейнер migrator.

Текущий статус разработки
-------------------------
Сделано:
- Infrastructure skeleton (docker-compose, .env.example) — создан.
- WF_01 (Registration) — определён и зафиксирован (n8n JSON + MD).
- WF_02 (Role Selection) — определён и зафиксирован (n8n JSON + MD).
- WF_03 (AI Profile Agent) — определён и зафиксирован (n8n JSON + MD).
- Миграции: 001 (users, telegram_accounts) и 002 (profiles, photos, sessions, history) добавлены; 007 (message_moderation_queue) присутствовал ранее.
- PROJECT_STATUS.md обновлён для отражения статусов.

Проверено (в контексте репозитория/документации):
- Наличие шаблонов n8n для WF_01..WF_03.
- Наличие миграций 001, 002 и файла 007.
- Конвенция использования UUID и TIMESTAMP WITH TIME ZONE в миграциях.

Не проверено / Требует ручной валидации:
- Наличие и схема audit_events в миграциях/БД.
- Полный набор миграций 003..006 (moderation, catalog, chat, reliability) — нужно подтвердить наличие/содержимое.
- Импорт/выполнение миграций на реальной базе и корректность FK и constraints в runtime.
- Импорт workflows в работающий n8n и интеграционные тесты (E2E): регистрация → роль → профиль → модерация.
- Наличие UI/инструментов для модерации (Admin panel) и решение по модераторскому workflow (Telegram vs Web UI).

Известные проблемы и риски
--------------------------
- audit_events таблица/миграция не гарантирована — workflows пишут в неё; отсутствие миграции — блокер.
- Порядок миграций и зависимости FK критичны: profiles и messages должны быть созданы до ссылок из последующих миграций.
- Секреты: n8n JSON содержит placeholders; без привязки credentials workflow n8n Postgres ноды не будут работать.
- AI‑вызовы могут быть дорогими и задерживать UX; нужно лимитировать запросы и предусмотреть fallback (offline prompts, manual copy).
- Moderation latency и модераторский UX не определены; это может стать узким местом при запуске.

Список следующих шагов (по приоритету)
--------------------------------------
1. Выполнить инвентаризацию миграций: подтвердить наличие и порядок 001..007, собрать SHA файлов и задокументировать.
2. Добавить/проверить миграцию audit_events (если отсутствует) и убедиться в её корректности.
3. Запустить dev environment (infrastructure/docker-compose.yml), применить миграции на чистой базе и убедиться, что все таблицы созданы без ошибок.
4. Импортировать WF_01..WF_03 в n8n, привязать реальные (локальные тестовые) credentials и выполнить smoke tests (curl сценарии).
5. Подготовить WF_04_AI_MODERATION skeleton и интегрировать модерацию (AI + human review path).
6. Разработать минимальный Moderator UX (Telegram channel или простая Admin UI) для human review.
7. Настроить CI job: прогон миграций + импорт n8n workflows в staging, выполнения smoke tests.
8. Запланировать нагрузочное тестирование AI‑моделей и бюджет/лимиты для вызовов.

START HERE FOR NEXT AI
----------------------
Какие файлы открыть сначала:
1. docs/architecture/MVP_ARCHITECTURE_REVIEW.md — общий обзор (главный ТЗ).
2. PROJECT_DOCUMENTATION_INDEX.md и PROJECT_STATUS.md — приоритеты и статус.
3. infrastructure/docker-compose.yml и infrastructure/.env.example — dev окружение и переменные окружения.
4. database/migrations/ — посмотреть файлы миграций; начать с 001_users_and_telegram_accounts_schema.sql, 002_profiles_schema.sql, 007_chat_message_moderation_schema.sql.
5. n8n/workflows/auth/WF_01_USER_REGISTRATION.json и WF_02_ROLE_SELECTION.json — регистрация и роль.
6. n8n/workflows/profile/WF_03_AI_PROFILE_AGENT.json — AI диалог и логика сессий.
7. n8n/workflows/** — остальные available WF шаблоны (WF_04..WF_12) если есть.

С чего продолжать (пошагово):
1. Подтвердить миграции и применить их на локальной чистой базе.
2. Привязать credentials в n8n (создать Postgres credential с тем же именем, что указан в JSON или исправить JSON чтобы использовать реальный credential id).
3. Импортировать WF_01..WF_03 и выполнить E2E smoke tests (регистрация → роль → AI диалог).
4. Проверить таблицу audit_events — создать миграцию, если нужно.
5. Создать WF_04 skeleton и связать с WF_03 (Trigger URL уже присутствует как env переменная).

Решения, которые уже приняты (не менять без обоснования):
- Использовать n8n как основной оркестратор workflow.
- Postgres — единое хранилище, все PK — UUID с uuid_generate_v4().
- Timestamp fields — TIMESTAMP WITH TIME ZONE (utc-aware).
- Telegram file_id хранится в profile_photos/telegram_accounts; бинарные файлы не сохраняются в БД.
- audit_events — централизованная таблица для аудита событий и триггеров.

Что нельзя менять без анализа:
- Именование и порядок миграций (001..n) — изменение порядка может привести к ошибкам при применении.
- PK типы (UUID) и default uuid_generate_v4() — изменение потребует массштабного рефакторинга.
- Удалять или реплицировать Telegram ID в других таблицах (должен храниться только в telegram_accounts).
- Политику хранения PII: не переводите Telegram raw payloads или файлы в таблицы.
- API контракты webhooks (пути и названия полей) — менять только при согласовании с ботом/клиентом.

Контакты и дальнейшие указания
-----------------------------
- Перед запуском миграций или импортом workflows создайте резервную копию и/или запускайте на чистой БД (dev/staging).
- Для вопросов по дизайну WF обратитесь к docs/architecture и PROJECT_STATUS.md.

---

Файл зафиксирован как snapshot текущего состояния для передачи следующему AI/разработчику.