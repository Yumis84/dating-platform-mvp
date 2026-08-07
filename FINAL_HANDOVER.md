# FINAL_HANDOVER

Дата: 2026-08-07
Автор: Copilot (final handover snapshot)

1. Состояние проекта на текущий момент
-------------------------------------
- MVP проект для Telegram‑ориентированного dating‑приложения с n8n‑оркестрацией и PostgreSQL хранением.
- Основные workflow WF_01 (registration), WF_02 (role selection), WF_03 (AI profile agent) подготовлены как n8n JSON + MD.
- Миграции по схемам пользователей и профилей добавлены (001, 002 и далее), однако обнаружен критический конфликт в первой миграции (два файла 001_*) — это блокер для безопасного применения миграций.
- Подготовлены и добавлены документация: AI_CONTEXT.md, PROJECT_STATUS.md, docs/TEST_PLAN_MVP.md, docs/MIGRATION_AUDIT_REPORT.md, docs/DATABASE_FIX_PLAN.md и ряд проектных описаний.

2. Все созданные документы (и где они находятся)
-----------------------------------------------
- AI_CONTEXT.md (корень репозитория)
- TEST_PLAN_MVP.md (docs/TEST_PLAN_MVP.md)
- MIGRATION_AUDIT_REPORT.md (docs/MIGRATION_AUDIT_REPORT.md)
- DATABASE_FIX_PLAN.md (корень репозитория) — план исправления конфликтов миграций (создан как документ, не изменяет SQL)
- PROJECT_STATUS.md (корень репозитория)

3. Последние git commit hash и файлы в каждом коммите
----------------------------------------------------
- 4c3d72bfb52c57aa310fb8eb702e8c27711728c2
  - Сообщение: "Add registration workflows and users migration"
  - Файлы:
    - n8n/workflows/auth/WF_01_USER_REGISTRATION.md
    - n8n/workflows/auth/WF_01_USER_REGISTRATION.json
    - n8n/workflows/auth/WF_02_ROLE_SELECTION.md
    - n8n/workflows/auth/WF_02_ROLE_SELECTION.json
    - database/migrations/001_users_and_telegram_accounts_schema.sql
    - PROJECT_STATUS.md

- 5b44ea1a4d19aff9e23bf0f74a5954bcc4a6dbd1
  - Сообщение: "Add WF_03 AI profile agent and profiles migration"
  - Файлы:
    - n8n/workflows/profile/WF_03_AI_PROFILE_AGENT.md
    - n8n/workflows/profile/WF_03_AI_PROFILE_AGENT.json
    - database/migrations/002_profiles_schema.sql
    - PROJECT_STATUS.md (обновлён)

- 2c2b630631829af98aeea994fdf6631627b78e6c
  - Сообщение: "Add AI context handover file"
  - Файлы:
    - AI_CONTEXT.md

- 2cf518c086035d90d699073735fdae49e3997de5
  - Сообщение: "Add manual test plan for MVP"
  - Файлы:
    - docs/TEST_PLAN_MVP.md

- aa2a280cb5dbffa46739d58b084c08456ca16bf4
  - Сообщение: "Add migration audit report"
  - Файлы:
    - docs/MIGRATION_AUDIT_REPORT.md

- (текущий коммит, добавлен этот файл)
  - COMMIT_HASH: (см. вывод после пуша)
  - Файлы:
    - FINAL_HANDOVER.md

4. Что уже принято как архитектурные решения
-------------------------------------------
- Orchestrator: n8n — используется как основной workflow engine для всех интеграций (телеграм вебхуки, AI вызовы, DB операции).
- Data store: PostgreSQL с UUID PK (uuid_generate_v4()) и TIMESTAMP WITH TIME ZONE для всех timestamp полей.
- Telegram IDs: canonical storage — telegram_accounts table (telegram_file_id for photos stored in profile_photos). Telegram IDs не должны дублироваться в других таблицах long‑term.
- AI flows: AI used for profile creation (WF_03) and moderation (planned WF_04). ai_context stored as JSONB in profile_ai_sessions.
- Audit events: centralized audit_events table to capture registration, role selection, profile_created, etc. (must be present and indexed).
- Migrations: numbered SQL migration files under database/migrations/; apply in numeric order. Keep them idempotent.

5. Что находится в статусе BLOCKER
---------------------------------
- Конфликт в миграциях: наличие двух разных файлов с префиксом 001_ (001_initial_users_schema.sql и 001_users_and_telegram_accounts_schema.sql). Это блокирует безопасное применение миграций и помешает созданию однозначной схемы БД.
- До решения конфликта 001 нельзя применять миграции в production или staging автоматически.

6. Что нельзя делать следующему AI без согласования
----------------------------------------------------
- Нельзя изменять существующие SQL‑миграции или их номера (не переименовывать и не редактировать 001..007) без утверждения владельцем проекта.
- Нельзя запускать миграции на production до разрешения конфликта 001 и выполнения всех реплик/проверок на staging.
- Нельзя менять архитектурные решения (n8n как orchestrator, Postgres+UUID, canonical telegram_accounts storage) без документации и согласования.
- Нельзя удалять или массово изменять существующие данные в таблицах users/telegram_accounts/profiles без явного плана миграции и бэкапа.

7. Точные следующие шаги (приоритетные)
----------------------------------------
Шаг 1 — Принять решения (OWNER ACTION)
- Владелец проекта должен принять решения из раздела "DECISIONS REQUIRED" в DATABASE_FIX_PLAN.md:
  - Выбрать авторитетную версию первой миграции (рекомендуется: 001_users_and_telegram_accounts_schema.sql).
  - Решить политику для audit_events FK и casing значений role.
- После утверждения, согласовать maintenance window для staged rollout.

Шаг 2 — Подготовить и протестировать reconciliation миграции на staging
- Создать новую миграцию(и) (пример: 008_reconcile_users_and_audit.sql) которая:
  - Гарантированно создаёт audit_events с FK/индексом (если нужно).
  - Мигрирует данные telegram_id из users в telegram_accounts, не удаляя исходные колонки.
  - Добавляет индексы и проверочные запросы.
- Запустить на clean staging DB; выполнить smoke tests (WF_01..WF_03) и SQL‑валидации.

Шаг 3 — Rollout в production (с наблюдением и откатом)
- После успеха на staging и утверждения, применить миграции на production в maintenance window.
- Выполнить post‑migration checks (integrity queries, WF smoke tests).
- Если всё стабильно — планировать follow‑up cleanups (удаление deprecated columns) как отдельные миграции после N дней стабильной работы.

8. START HERE FOR NEXT AI
-------------------------
Какие файлы открыть первыми
- docs/MIGRATION_AUDIT_REPORT.md — audit вывод о текущих миграциях и блокерах.
- docs/DATABASE_FIX_PLAN.md — план исправлений; содержит рекомендации и список решений для владельца.
- database/migrations/001_users_and_telegram_accounts_schema.sql — предложенная canonical users/telegram_accounts миграция.
- database/migrations/001_initial_users_schema.sql — альтернативная/конфликтующая версия (прочитать и сравнить).
- database/migrations/002_profiles_schema.sql — схема профилей и зависимостей.
- n8n/workflows/auth/WF_01_USER_REGISTRATION.json — посмотреть ожидания WF для регистрации.
- n8n/workflows/profile/WF_03_AI_PROFILE_AGENT.json — логика сохранения ai_context и работы с profile_ai_sessions.

Какие решения проверить
- Подтвердить canonical location для telegram_id (рекомендуется: telegram_accounts.telegram_id).
- Решить поведение audit_events.user_id (FK vs nullable) и добавить индекс.
- Утвердить canonical casing и allowed values для users.role (uppercase vs lowercase).

Какую задачу выполнять следующей
- После получения утверждений от владельца: подготовить reconciliation migration(s) (non‑destructive), протестировать на staging и предоставить отчёт smoke test результатов.

---

Если нужно, я могу сейчас подготовить:
- черновую SQL миграцию (008_reconcile_users_and_audit.sql) для review (не выполню commit), и/или
- пошаговые shell‑скрипты для выполнения миграции и валидации на staging.

Команда для добавления/коммита/пуша файла FINAL_HANDOVER.md (если вы хотите выполнить локально):

```bash
# в корне репозитория
git add FINAL_HANDOVER.md
git commit -m "Add final handover snapshot"
git push origin main

# После пуша получите hash и список файлов в коммите:
git rev-parse HEAD
git show --name-only --pretty="" HEAD
```

---

Файл создан автоматически как финальная передача состояния проекта другому AI/разработчику. Пожалуйста, подтвердите, хотите ли вы, чтобы я подготовил SQL‑черновик reconciliation миграции для ревью (я не буду коммитить или применять его без команды).