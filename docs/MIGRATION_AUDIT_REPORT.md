# Migration Audit Report

Дата: 2026-08-07
Автор: Copilot (automated audit)

Обзор
-----
Проведён аудит файлов в каталоге database/migrations/ для оценки готовности схемы БД и соответствия рабочим процессам WF_01..WF_03. Ниже — результирующий список миграций, их содержимое в терминах создаваемых таблиц, зависимости и найденные проблемы.

Найденные файлы миграций (в порядке сортировки по имени)
-------------------------------------------------------
- 001_initial_users_schema.sql
- 001_users_and_telegram_accounts_schema.sql
- 002_profiles_schema.sql
- 003_moderation_schema.sql
- 004_catalog_schema.sql
- 005_chat_schema.sql
- 006_chat_reliability_schema.sql
- 007_chat_message_moderation_schema.sql
- README.md (описание каталога)

Примечание: в каталоге присутствуют два файла с префиксом "001_..." (два варианта первой миграции). Это критический сигнал о конфликте/дублировании и требует разбора перед применением миграций на рабочей базе.

Детальный список миграций
-------------------------

001_initial_users_schema.sql
- Создаёт таблицы:
  - users
  - telegram_accounts
  - audit_events
- Подробно:
  - users: id UUID PK, telegram_id BIGINT UNIQUE NOT NULL, username, first_name, last_name, role (CHECK 'man','woman','admin'), status, timestamps.
  - telegram_accounts: id UUID PK, user_id UUID REFERENCES users(id), telegram_id BIGINT, init_data_hash, last_login_at.
  - audit_events: id UUID PK, user_id UUID, event_type, event_data JSONB, created_at.
- Зависимости: требует существования расширения uuid-ossp.
- Используемые FK: telegram_accounts.user_id → users(id).
- Замечания: audit_events.user_id не объявлен как FOREIGN KEY (нет REFERENCES). users содержит telegram_id (потенциальное дублирование хранения Telegram ID).

001_users_and_telegram_accounts_schema.sql
- Создаёт таблицы:
  - users
  - telegram_accounts
- Подробно:
  - users: id UUID PK, role VARCHAR, created_at, updated_at.
  - telegram_accounts: id UUID PK, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, telegram_id BIGINT NOT NULL UNIQUE, username, created_at.
- Зависимости: uuid-ossp.
- Используемые FK: telegram_accounts.user_id → users(id) (NOT NULL, ON DELETE CASCADE).
- Замечания: в этой версии users не содержит telegram_id — модель раздельного хранения контактов. Эта миграция конфликтует с 001_initial_users_schema.sql (см. раздел "Проблемы").

002_profiles_schema.sql
- Создаёт таблицы:
  - profiles
  - profile_photos
  - profile_ai_sessions
  - profile_fields_history
- Подробно:
  - profiles: id UUID PK, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, status CHECK(...), name, age, city, description, interests JSONB, preferences JSONB, timestamps.
  - profile_photos: id UUID PK, profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL, telegram_file_id, position, created_at.
  - profile_ai_sessions: id UUID PK, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, profile_id UUID REFERENCES profiles(id) ON DELETE SET NULL, current_step INT, ai_context JSONB, status, timestamps.
  - profile_fields_history: id UUID PK, profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE, field_name, old_value JSONB, new_value JSONB, changed_by, created_at.
- Зависимости: users table must exist prior to application.
- Используемые FK: profiles.user_id → users(id); profile_photos.profile_id → profiles(id); profile_ai_sessions.user_id → users(id); profile_ai_sessions.profile_id → profiles(id); profile_fields_history.profile_id → profiles(id).

003_moderation_schema.sql
- Создаёт таблицы:
  - profile_moderation
  - moderation_rules
  - moderation_history
- Зависимости: profiles table.
- FK: profile_moderation.profile_id → profiles(id); moderation_history.profile_id → profiles(id).

004_catalog_schema.sql
- Создаёт таблицы:
  - profile_views
  - favorites
  - profile_search_events
- Зависимости: profiles, users.
- FK: profile_views.profile_id → profiles(id); profile_views.viewer_user_id → users(id); favorites.user_id → users(id); favorites.profile_id → profiles(id); profile_search_events.user_id → users(id).

005_chat_schema.sql
- Создаёт таблицы:
  - chat_sessions
  - messages
  - chat_blocks
  - chat_reports (partial in file preview)
- Зависимости: profiles (for chat_sessions.profile_id), users (for initiator/respondent, messages.sender_id), chat_sessions (for messages/chat_blocks/chat_reports).
- FK: chat_sessions.profile_id → profiles(id); chat_sessions.initiator_user_id → users(id); chat_sessions.respondent_user_id → users(id); messages.chat_id → chat_sessions(id); messages.sender_id → users(id); chat_blocks.chat_id → chat_sessions(id); chat_blocks.blocker_user_id → users(id); chat_reports.chat_id → chat_sessions(id) etc.

006_chat_reliability_schema.sql
- Создаёт таблицы:
  - message_delivery_queue
  - message_rate_limits
  - chat_moderation_events
- Зависимости: messages, chat_sessions.
- FK: message_delivery_queue.message_id → messages(id); message_rate_limits.user_id → users(id); chat_moderation_events.chat_id → chat_sessions(id); chat_moderation_events.message_id → messages(id).

007_chat_message_moderation_schema.sql
- Создаёт таблицу:
  - message_moderation_queue
- Зависимости: messages, chat_sessions
- FK: message_moderation_queue.message_id → messages(id); message_moderation_queue.chat_id → chat_sessions(id).

Проверка наличия критичных таблиц
--------------------------------
(Основные таблицы, перечисленные в задании):
- users — присутствует (создаётся в 001_initial_users_schema.sql и в 001_users_and_telegram_accounts_schema.sql) — ДА (но есть конфликт версий)
- telegram_accounts — присутствует (в обоих 001 файлах) — ДА
- audit_events — присутствует (в 001_initial_users_schema.sql) — ДА (но в том же файле audit_events.user_id не имеет FK)
- profiles — присутствует (002_profiles_schema.sql) — ДА
- profile_photos — присутствует (002_profiles_schema.sql) — ДА
- profile_ai_sessions — присутствует (002_profiles_schema.sql) — ДА
- profile_fields_history — присутствует (002_profiles_schema.sql) — ДА
- message_moderation_queue — присутствует (007_chat_message_moderation_schema.sql) — ДА

Итого: все перечисленные критичные таблицы имеются в миграциях, но есть важные замечания по согласованности миграций и FK (см. ниже).

Найденные проблемы и риски
--------------------------
1) Дублирование и конфликт миграций с префиксом "001_" (BLOCKER)
- В каталоге находятся два различных файла, начинающиеся с префикса 001:
  - 001_initial_users_schema.sql
  - 001_users_and_telegram_accounts_schema.sql
- Оба файла пытаются создать таблицу users и таблицу telegram_accounts, но с разными колонками и моделями:
  - 001_initial_users_schema.sql: users содержит telegram_id и другие PII‑поля; telegram_accounts существует как дополнительная таблица. audit_events создаётся здесь.
  - 001_users_and_telegram_accounts_schema.sql: users — минимальная таблица, telegram_accounts содержит telegram_id (NOT NULL, UNIQUE) и user_id NOT NULL.
- Риск: при применении миграций с одинаковым номером поведение зависит от выбранного инструмента миграции — если оба файла будут применены, возникнут ошибки CREATE TABLE IF NOT EXISTS may hide conflicts or the second may be a no-op. Однако структуры конфликтуют (duplicates of column telegram_id or absence). Это может привести к:
  - Непредсказуемой схеме в среде, где оба файла присутствуют.
  - Потерям данных или несовместимости WF, которые ожидают Telegram ID в telegram_accounts vs users.
- Рекомендация: Решить единую стратегию хранения Telegram ID (в telegram_accounts предпочтительнее). Удалить/объединить дубликаты и нормализовать 001‑миграцию. До разрешения — применение миграций на production БЛОКИРОВАНО.

2) audit_events: отсутствие FK (WARNING)
- В 001_initial_users_schema.sql таблица audit_events имеет поле user_id UUID, но не объявлено REFERENCES users(id). Это уменьшает целостность ссылок и может допустить ситуацию, когда audit_event ссылается на несуществующего пользователя.
- Recommendation: добавить FOREIGN KEY audit_events.user_id → users(id) в отдельной миграции (или явно задокументировать причину отсутствия FK), и/или индекс для быстрого поиска по user_id.

3) Несогласованность типов/constraints (WARNING)
- В 001_initial_users_schema.sql users.role и values in lower-case ('man','woman','admin') в CHECK, а в других местах WF_02 expects roles 'MAN'/'WOMAN' uppercase. 002_profiles_schema.sql uses status values 'DRAFT','PENDING_MODERATION' etc. Неоднородность регистра/форматов ролей может привести к логическим несоответствиям.
- Recommendation: согласовать константы (roles, statuses) на уровне всего проекта и при необходимости привести данные/миграции к единому формату.

4) Отсутствующие или недостаточные индексы (WARNING)
- Некоторые таблицы не имеют индексов на поля, активно используемые в WHERE/JOIN:
  - audit_events.user_id — рекомендуется индекс для быстрых запросов по пользователю.
  - profiles.user_id — рекомендуется индекс (хотя FK обычно не создает индекс автоматически on referenced column; but many DBs require explicit index for fk target for performance).
  - profile_ai_sessions.user_id — стоит индексировать если часто выполняются SELECT by user_id.
- Некоторые migration files do create indexes for chat/messages and favorites; но audit_events and profiles may need more indexes.

5) Foreign key dependencies order appears mostly consistent (OK)
- Observed ordering:
  - 001 creates users (but ambiguity due to duplicates) → 002 depends on users — OK if correct 001 chosen.
  - 002 (profiles) → 005 (chat) depends on profiles — ordering 002 before 005 is correct.
  - 005 (messages) → 006,007 depend on messages — ordering is correct (005 before 006/007).
- However, the duplicate 001 files may break this ordering or lead to subtle differences.

6) audit_events used by WF_01..WF_03 — confirm existence (OK but with FK caveat)
- WF_01/WF_02/WF_03 all insert into audit_events. The migration 001_initial_users_schema.sql creates this table; if that file is not applied (e.g., if the other 001 supersedes it), audit_events may be missing.
- Recommendation: ensure audit_events creation is included exactly once in the migration set.

7) Potential UUID conflicts (LOW)
- All migrations consistently use uuid_generate_v4() — low risk. Ensure extension uuid-ossp is created and available in target DB prior to running migrations.

8) Miscellaneous risks
- Some migrations include comments about further implementation (e.g., triggers, materialized views) — ensure these are considered in later work.

MVP DATABASE READINESS (оценка)
-------------------------------
- Оценка: BLOCKER

Причина оценки:
- Наличие двух различных файлов с префиксом 001 и конфликтующих схем пользователей/telegram_accounts/audit_events — критическая проблема, блокирующая безопасное применение миграций на любой существующей базе. До решения этого конфликта нельзя гарантировать корректное состояние базы и поведение WF.

NEXT DATABASE ACTIONS (рекомендации, только чтение)
---------------------------------------------------
1. URGENT: Разобрать дублирующие 001‑миграции (BLOCKER)
   - Определить, какая версия 001 является актуальной и желательной для проекта (рекомендация: использовать модель раздельного хранения контактов — telegram_accounts хранит telegram_id; users не должен содержать telegram_id как отдельный столбец).
   - Если принимается модель из 001_users_and_telegram_accounts_schema.sql, удалить или переименовать 001_initial_users_schema.sql (или объединить содержимое так, чтобы audit_events создавалась однозначно).
   - Обновить систему миграций, чтобы номер 001 встречался только один раз.

2. Ensure audit_events exists and has FK/index (HIGH)
   - Если audit_events создаётся только в конфликтной версии 001_initial_users_schema.sql и её удаляют, создать отдельную миграцию (например, 002a_add_audit_events.sql) которая гарантированно создаст audit_events с FOREIGN KEY на users(id) и индексом по user_id.

3. Normalize role/status constants (MEDIUM)
   - Привести к единому стандарту (e.g., roles: 'MAN','WOMAN','ADMIN' uppercase) и обновить CHECK constraints или добавить migration to alter column/check accordingly.
   - Обновить WF_02/other workflows to use the canonical casing if necessary.

4. Add recommended indexes (MEDIUM)
   - audit_events(user_id) index.
   - profiles(user_id) index if not present.
   - profile_ai_sessions(user_id) index.
   - Consider indexes on commonly filtered columns (profiles.status, message_moderation_queue.status).

5. Validate FK and ordering by running migrations on a clean DB (HIGH)
   - On a clean test DB, run migrations in numeric order and observe failures.
   - Resolve any dependency errors, missing tables, or constraint violations.

6. Document authoritative migration set (HIGH)
   - Create a manifest file (e.g., MIGRATION_MANIFEST.md) listing the canonical migrations and their order; include SHAs of files to lock the set.

7. Consider adding CI checks (MEDIUM)
   - Add a CI job that runs migrations on a disposable Postgres instance and reports errors.
   - Consider tests validating that WF_01..WF_03 can run against the migrated DB (smoke tests).

8. Review and add missing constraints where necessary (LOW)
   - audit_events.user_id FOREIGN KEY (or documented reason why it must be nullable/loose).
   - Optional: add ON UPDATE/ON DELETE policies where appropriate.

Заключение
----------
Миграционная база проекта содержит большинство необходимых схем для MVP, включая users, telegram_accounts, profiles и очередь модерации. Однако наличие конфликтующих первых миграций (два варианта 001_) делает текущее состояние БАЗЫ небезопасным для автоматического применения миграций — это блокер, требующий ручного вмешательства и принятия решения об окончательной структуре users/telegram_accounts/audit_events.

Действия по приоритету описаны в разделе "NEXT DATABASE ACTIONS". Рекомендую решить конфликт 001 в первую очередь, затем выполнить миграции на чистой БД и только после этого продолжать интеграционное тестирование и импорт workflow'ов.
