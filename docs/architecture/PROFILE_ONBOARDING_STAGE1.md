# Profile onboarding — ЭТАП 1

Дата: 2026-08-10

Статус: design/implementation plan. Этот документ не меняет production n8n.

## Цель

После успешного выбора роли в WF_01 создать или продолжить одну активную onboarding-session пользователя и задать первый вопрос анкеты: имя.

Каноническое состояние onboarding хранится только в:

`profile_ai_sessions.current_step`

`profiles.status` используется только для lifecycle профиля/модерации и не является шагом анкеты.

## Canonical steps

| current_step | field |
|---:|---|
| 0 | name |
| 1 | age |
| 2 | city |
| 3 | description |
| 4 | interests |
| 5 | purpose |
| 6 | hobbies |
| 7 | job |
| 8 | education |
| 9 | communication_style |
| >=10 | finalize |

После завершения:

- `profiles.status = 'PENDING_MODERATION'`
- `profile_ai_sessions.status = 'COMPLETED'`

## ЭТАП 1 scope

На этом этапе реализуется только безопасный старт onboarding после выбора роли:

1. Получить `user_id`, для которого роль успешно сохранена.
2. Найти существующую `profile_ai_sessions` со статусом `IN_PROGRESS`.
3. Если session есть — переиспользовать её.
4. Если session нет — создать с `current_step = 0`, `ai_context = {}` и `status = 'IN_PROGRESS'`.
5. Не создавать вторую активную session.
6. Отправить вопрос для текущего шага. Для новой session это: `Как тебя зовут?`

Важно: повторный callback или `/start` не должен сбрасывать уже начатую session обратно на шаг 0.

## Рекомендуемый SQL для find-or-create

Предпочтительно одним запросом, чтобы workflow не зависел от разветвления `SELECT -> IF -> INSERT`:

```sql
WITH existing AS (
  SELECT id, user_id, profile_id, current_step, ai_context, status
  FROM profile_ai_sessions
  WHERE user_id = $1
    AND status = 'IN_PROGRESS'
  ORDER BY created_at DESC
  LIMIT 1
), inserted AS (
  INSERT INTO profile_ai_sessions (
    user_id,
    profile_id,
    current_step,
    ai_context,
    status,
    created_at,
    updated_at
  )
  SELECT
    $1,
    NULL,
    0,
    '{}'::jsonb,
    'IN_PROGRESS',
    now(),
    now()
  WHERE NOT EXISTS (SELECT 1 FROM existing)
  RETURNING id, user_id, profile_id, current_step, ai_context, status
)
SELECT * FROM existing
UNION ALL
SELECT * FROM inserted
LIMIT 1;
```

Примечание: без DB-level unique constraint два конкурентных execution теоретически могут создать две sessions. Для MVP workflow должен минимизировать этот риск, но отдельная schema-hardening миграция с partial unique index предпочтительна позднее после проверки текущих данных.

## N8n insertion point

Текущий live callback flow:

`Extract role vars -> Resolve user -> User found? -> Update role -> Send role confirm -> Insert role audit -> answerCallbackQuery`

Для ЭТАПА 1 нельзя ломать существующее подтверждение callback.

Рекомендуемая последовательность после успешного `Update role`:

`Update role -> Send role confirm -> Insert role audit -> Ensure profile session -> Ask onboarding question -> answerCallbackQuery`

Допустимый вариант — оставить callback acknowledgement раньше, если это необходимо для быстрого ответа Telegram, но existing callback semantics должны сохраниться.

Новые логические nodes:

- `Ensure profile session` — Postgres find-or-create IN_PROGRESS session.
- `Prepare onboarding question` — определяет текст по `current_step`.
- `Send onboarding question` — Telegram sendMessage.

На первом изменении можно ограничить `Prepare onboarding question` только корректным resume шага 0..9, чтобы повторный выбор роли не спрашивал имя заново у пользователя на шаге >0.

## Question mapping

```text
0 -> Как тебя зовут?
1 -> Сколько тебе лет?
2 -> В каком городе живёшь?
3 -> Расскажи немного о себе.
4 -> Какие у тебя интересы?
5 -> Какова цель знакомства?
6 -> Расскажи о своих хобби. Можно пропустить.
7 -> Чем ты занимаешься / где работаешь? Можно пропустить.
8 -> Какое у тебя образование? Можно пропустить.
9 -> Какой стиль общения тебе ближе? Можно пропустить.
```

## Message routing — следующий подэтап

После завершения безопасного старта onboarding обычные Telegram messages должны идти через отдельную проверку active session:

```text
Telegram Trigger
  -> callback?       -> existing callback/role flow
  -> /start?         -> existing registration flow
  -> normal message  -> load IN_PROGRESS session
                        -> session exists? -> onboarding answer handler
                        -> none            -> non-onboarding behavior
  -> photo            -> photo handler / profile_photos
```

Нельзя направлять любой `message` напрямую в регистрацию, иначе ответы анкеты будут снова проходить `/start`/welcome flow.

## Duplicate protection

Обязательные инварианты:

- не создавать несколько IN_PROGRESS sessions для одного user;
- не создавать duplicate user / telegram_account на повторном `/start`;
- не создавать второй profile при finalization;
- existing IN_PROGRESS session продолжать с её `current_step`;
- role callback не сбрасывает `current_step` существующей session;
- finalization выполняется идемпотентно.

## Photo handling

`profile_photos` хранит только Telegram `file_id` metadata.

В текущей schema `profile_photos.profile_id` допускает NULL, но предпочтительная реализация должна либо:

- привязывать photo к существующему profile, либо
- временно хранить reference/session context до finalization и затем связать с profile.

Не хранить бинарные Telegram images в PostgreSQL.

## Finalization contract

После `current_step >= 10`:

1. Проверить, существует ли profile для `user_id`.
2. Создать profile только если его нет.
3. Сохранить canonical публичные поля.
4. `profiles.status = 'PENDING_MODERATION'`.
5. Записать `profile_id` в session.
6. `profile_ai_sessions.status = 'COMPLETED'`.
7. Создать audit event идемпотентно/осознанно.
8. Передать profile в moderation flow.

## Preconditions before n8n draft edit

Перед первой write-операцией в n8n через Claude:

1. Получить свежий `get_workflow_details`.
2. Проверить, что draft всё ещё содержит 19-node base либо явно понять новые изменения.
3. Получить/сохранить полный JSON snapshot текущего draft.
4. Убедиться, что GitHub design соответствует реальным node parameters и credentials live workflow.
5. Объяснить пользователю точный planned diff.
6. Только после этого менять draft.
7. После изменения выполнить read-only verification.
8. Не публиковать без отдельного подтверждения.

## Repository note

Текущий GitHub export `n8n/workflows/registration/WF_01_USER_REGISTRATION.json` не является live source of truth и не должен перезаписываться проектируемым графом до получения полного 19-node export из n8n.
