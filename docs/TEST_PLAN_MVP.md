# TEST_PLAN_MVP

Дата: 2026-08-07
Автор: Copilot (manual test plan)

Цель
----
Руководство по ручному тестированию MVP: проверить ключевые пользовательские сценарии, корректность работы n8n workflows (WF_01..WF_03) и согласованность данных в PostgreSQL после применения миграций.

Общие предпосылки
-----------------
- Dev environment поднят: postgres + n8n (инструкция: infrastructure/README.md).
- Все миграции (минимум 001 и 002) применены к чистой базе.
- n8n имеет настроенный Postgres credential (заменён placeholder POSTGRES_PLACEHOLDER).
- WF_01, WF_02, WF_03 импортированы в n8n и включены (active=true) или готовы к ручному вызову через webhook.
- В .env заполнены тестовые значения (TELEGRAM_BOT_TOKEN not required for manual HTTP tests unless using real bot).

Как читать тест-план
--------------------
Каждый сценарий содержит шаги, SQL-проверки, ожидаемые результаты, возможные ошибки и рекомендации по отладке.

Сценарий 1: Новый пользователь Telegram — регистрация
----------------------------------------------------
Цель: убедиться, что при первом обращении Telegram пользователя создаются записи в users и telegram_accounts и логируется событие в audit_events.

Шаги:
1. Подготовить тестовые данные: sample Telegram update JSON (имитируем /start):

{
  "update_id": 1000000,
  "message": {
    "message_id": 1,
    "from": {"id": 123456789, "is_bot": false, "first_name":"Test","username":"testuser"},
    "chat": {"id": 123456789, "type":"private"},
    "date": 1620000000,
    "text": "/start"
  }
}

2. Вызвать webhook регистрации в n8n (WF_01):
   POST http://localhost:${N8N_PORT}/webhook/user-registration
   Body: приведённый JSON

3. Проверить ответ от n8n: HTTP 200 и тело ответа содержит приветственное сообщение (text с инструкцией по выбору роли).

SQL‑проверки в БД:
- Найти telegram_accounts:
  SELECT id, user_id, telegram_id, username, created_at FROM telegram_accounts WHERE telegram_id = 123456789;
  Ожидаемый результат: одна запись с telegram_id=123456789; user_id не NULL.

- Найти users:
  SELECT id, role, created_at FROM users WHERE id = '<user_id_from_telegram_accounts>';
  Ожидаемый результат: одна запись, role IS NULL (или default), created_at заполнен.

- Проверить audit_events:
  SELECT id, user_id, event_type, event_data, created_at FROM audit_events WHERE user_id = '<user_id>' ORDER BY created_at DESC LIMIT 5;
  Ожидаемый результат: запись с event_type = 'user_registration' и event_data минимальная (source: 'telegram').

Ожидаемые результаты:
- users и telegram_accounts созданы и связаны.
- audit_event регистрации создан.
- Никаких дублирующих users для одного telegram_id.

Возможные ошибки и диагностика:
- Нет записи telegram_accounts: проверьте логи n8n, убедитесь, что Postgres credential корректен и что нода Postgres не вернула ошибку UNIQUE violation или permissions issue.
- Дублирование users: возможно, workflow запускается несколько раз и не обрабатывает idempotency — в таком случае проверить логи и изменить WF (нужно отдельное исправление).

Сценарий 2: Выбор роли (MAN / WOMAN) и проверка idempotency
---------------------------------------------------------
Цель: убедиться, что роль сохраняется в users.role и поведение соответствует выбору (WOMAN → запускает WF_03; MAN → каталог).

Шаги:
1. Использовать user_id из сценария 1.
2. Вызвать webhook роли в n8n (WF_02) с payload:
   { "user_id": "<user_id>", "role": "WOMAN" }

3. Ожидания по ответу HTTP: 200, сообщение: "Role set to WOMAN. AI profile creation started." (или аналогичный текст).
4. Проверить SQL:
   SELECT id, role, updated_at FROM users WHERE id = '<user_id>';
   Ожидаемый результат: role = 'WOMAN' (uppercase), updated_at изменён.

5. Проверить audit_events:
   SELECT * FROM audit_events WHERE user_id = '<user_id>' AND event_type = 'role_selection' ORDER BY created_at DESC LIMIT 5;
   Ожидаемый результат: запись role_selection с деталями role=WOMAN.

6. Проверить, что WF_03_trigger выполняется (если WF_03_TRIGGER_URL задан): посмотреть логи n8n на вход/вызов внешнего webhook или проверку profile_ai_sessions creation (см. сценарий 3).

Idempotency test:
- Повторно послать тот же запрос role = WOMAN ещё 1–2 раза.
- Ожидаемый результат: users.role остаётся 'WOMAN'; не создаётся дополнительных audit_event (или создаются, но не дублируют логику) — на уровне audit_event допускается запись, но логика должна оставаться idempotent для downstream (например, не создавать несколько profile_ai_sessions если уже создана IN_PROGRESS/COMPLETED).

Возможные ошибки:
- Роль не сохраняется: проверить ноду Postgres и её credential.
- Множественные profile_ai_sessions: проверить запросы создания сессии в WF_03 (WF_02 инициирует WF_03) и убедиться, что WF_03 найдёт существующую IN_PROGRESS сессию.

Сценарий 3: Создание AI профиля (WF_03) — диалог, фото, сохранение
------------------------------------------------------------------
Цель: проверить, что WF_03 ведёт диалог, сохраняет ответы в profile_ai_sessions.ai_context, сохраняет фото metadata и в конце создаёт запись profiles со статусом PENDING_MODERATION.

Шаги — пошаговый диалог:
1. Инициировать WF_03 (как от WF_02) или напрямую:
   POST http://localhost:${N8N_PORT}/webhook/ai-profile
   Body: { "user_id": "<user_id>" }

   Ожидается: HTTP 200, body содержит session_id и next_question (например, "What is your name?").

2. Отправить ответ пользователя (пример):
   POST /webhook/ai-profile
   Body: { "user_id":"<user_id>", "session_id":"<session_id>", "user_answer":"Alice" }

   Повторять для каждого вопроса (age, city, description, interests, purpose). Для полей interests желательно передать JSON/CSV string.

3. По желанию: загрузка фото метаданных
   POST /webhook/ai-profile
   Body: { "user_id":"<user_id>", "session_id":"<session_id>", "photo_file_id":"ABC123_file_id" }

   Ожидается: запись в profile_photos с telegram_file_id='ABC123_file_id' и profile_id NULL (если профиль ещё не создан).

4. После ответа на последний обязательный вопрос ожидаем:
   - Создание записи в profiles (status = 'PENDING_MODERATION').
   - profile_ai_sessions.status = 'COMPLETED' и profile_id заполнен.
   - Создание audit_event profile_created.
   - Триггер WF_04 (moderation) — если WF_04_TRIGGER_URL задан, в логах n8n должен быть исходящий HTTP call.

SQL‑проверки:
- Проверить session ai_context accumulation:
  SELECT id, current_step, ai_context, status FROM profile_ai_sessions WHERE id = '<session_id>';
  Ожидаемый результат: status IN_PROGRESS или COMPLETED (в финале), ai_context содержит поля name, age, city, description, interests, purpose и optional fields if provided.

- Проверить profile_photos:
  SELECT id, profile_id, telegram_file_id, created_at FROM profile_photos WHERE telegram_file_id = 'ABC123_file_id';
  Ожидаемый результат: запись с telegram_file_id и profile_id NULL или заполненным (если профиль уже создан).

- Проверить profiles:
  SELECT id, user_id, status, name, age, city, description FROM profiles WHERE user_id = '<user_id>' ORDER BY created_at DESC LIMIT 1;
  Ожидаемый результат: статус = 'PENDING_MODERATION', поля заполнены корректно.

- Проверить audit_events:
  SELECT * FROM audit_events WHERE user_id = '<user_id>' AND event_type = 'profile_created';

Edge cases / возможные ошибки:
- Некорректное преобразование age (не число) — workflow должен корректно валидировать или сообщать пользователю об ошибке; проверьте логи и тексты ошибок.
- Дублирование профилей при повторном завершении сессии: должно быть LOGIC: INSERT profiles ... WHERE NOT EXISTS (SELECT 1 FROM profiles WHERE user_id=...), убедитесь, что условие работает.
- AI сервис возвращает ошибку/таймаут: workflow должен оставить сессию IN_PROGRESS; проверить ноды для continueOnFail.

Сценарий 4: Проверка базы данных — какие SQL запросы выполнить
-------------------------------------------------------------
Общие команды для инспекции (заменяйте placeholders реальными значениями):

-- Пользователь и аккаунт Telegram
SELECT * FROM telegram_accounts WHERE telegram_id = 123456789;
SELECT * FROM users WHERE id = '<user_id>';

-- Сессия AI
SELECT id, user_id, current_step, status, ai_context FROM profile_ai_sessions WHERE user_id = '<user_id>' ORDER BY created_at DESC LIMIT 5;

-- Профили
SELECT * FROM profiles WHERE user_id = '<user_id>' ORDER BY created_at DESC LIMIT 5;

-- Фото
SELECT * FROM profile_photos WHERE telegram_file_id IS NOT NULL AND profile_id IS NULL ORDER BY created_at DESC LIMIT 5;

-- Audit events
SELECT * FROM audit_events WHERE user_id = '<user_id>' ORDER BY created_at DESC LIMIT 10;

-- Общая целостность
-- Сколько пользователей без профиля
SELECT u.id FROM users u LEFT JOIN profiles p ON u.id = p.user_id WHERE p.id IS NULL LIMIT 20;

Ожидаемые результаты:
- Сопоставление users ↔ telegram_accounts верное.
- profile_ai_sessions.ai_context хранит JSON с накопленными ответами.
- profiles создаются только после завершения диалога и получают PENDING_MODERATION.

Сценарий 5: Проверка n8n — какие webhook вызвать и ответы ожидать
----------------------------------------------------------------
Список вебхуков и образцы payload:

1) Registration webhook (WF_01)
POST /webhook/user-registration
Body: Telegram update JSON (см. Сценарий 1)
Expect: HTTP 200, JSON { text: 'Welcome... choose role' }

2) Role selection (WF_02)
POST /webhook/role-selection
Body: { "user_id": "<user_id>", "role": "WOMAN" }
Expect: HTTP 200, JSON message: role set and next step; if WOMAN then WF_03 should be triggered.

3) AI Profile dialog (WF_03)
POST /webhook/ai-profile
Body for start: { "user_id": "<user_id>" }
Expect: HTTP 200, JSON { session_id: '<uuid>', next_question: 'What is your name?' }

POST for answer: { "user_id":"<user_id>", "session_id":"<session_id>", "user_answer":"Alice" }
Expect: HTTP 200, JSON with next_question or indication of completion.

4) Photo metadata
POST /webhook/ai-profile
Body: { "user_id":"<user_id>", "session_id":"<session_id>", "photo_file_id":"<telegram_file_id>" }
Expect: HTTP 200, JSON with next_question; profile_photos contains telegram_file_id.

Ожидаемые ответы n8n
- На каждом шаге WF n8n возвращает корректный JSON со следующими полями как минимум: session_id (если создан), next_question (string|null), или friendly error message with HTTP >200 on failure.
- При завершении диалога: response contains next_question = null and session_id, and profiles created in DB.

Возможные ошибки и обработка
----------------------------
- 500 Internal Server Error от нод Postgres: проверьте credential и права доступа.
- 400 Bad Request: неверный payload или отсутствует user_id/session_id.
- 502/504 при вызове внешнего AI: retry strategy и ручной retry должна быть предусмотрена; сессия остаётся IN_PROGRESS.

Критерии «MVP готов» (acceptance criteria)
-----------------------------------------
1. Регистрация (WF_01) успешно создаёт users и telegram_accounts для нового Telegram id, и audit_event регистрации логируется.
2. Выбор роли (WF_02) корректно обновляет users.role; WOMAN инициирует создание AI профиля (WF_03) без дублирования сессий/профилей.
3. AI диалог (WF_03) корректно сохраняет ответы в profile_ai_sessions.ai_context, поддерживает resumption и после завершения создаёт profiles со статусом PENDING_MODERATION.
4. Profile photos сохраняются как metadata (telegram_file_id) в profile_photos; бинарные данные не хранятся.
5. Все SQL миграции применяются последовательно без ошибок на чистой БД.
6. Нету утечек PII: Telegram ID хранится только в telegram_accounts; raw webhook payloads не сохраняются в БД.
7. Workflow ноды обрабатывают ошибки AI/Postgres корректно и не приводят к некорректному состоянию данных (например, не создают дублей профилей).

Как отмечать баги
-----------------
- Уточнить шаг воспроизведения, payload, лог исполнений n8n (Execution logs), SQL ошибок в Postgres (psql logs), и содержимое соответствующих миграций.
- Для критических ошибок остановить дальнейшие тесты и исправить миграции/ноды перед продолжением.

Заключение
----------
Этот тест‑план покрывает критические пользовательские сценарии и проверки целостности БД и n8n workflow'ов. После прохождения всех тестов и устранения критических багов MVP можно считать готовым к первичному релизу в тестовой среде.
