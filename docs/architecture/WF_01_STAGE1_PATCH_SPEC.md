# WF_01 — Stage 1 draft patch specification

Дата: 2026-08-10

Статус: draft изменён и проверен; production publish запрещён без отдельного подтверждения пользователя.

## Base snapshot

Workflow: `WF_01_USER_REGISTRATION_0001`

Draft version before Stage 1: `ef5fc7d8-2c72-40b8-9df3-bd5ca7d6650a`

Active production version: `d2678798-5807-4813-8e24-7a819285b298`

Base graph: 19 nodes. Draft и Active были подтверждены как идентичные перед подготовкой этого patch.

Repository snapshot:

`n8n/workflows/registration/WF_01_USER_REGISTRATION_live_snapshot_ef5fc7d8.json`

## Scope

Этот patch реализует только начало onboarding после успешного выбора роли.

Он НЕ реализует обработку ответов анкеты, фотографии или finalization. Эти изменения идут следующим подэтапом после проверки Stage 1.

## Existing successful role flow

До изменения:

`User found? -> Update role -> Send role confirm -> Insert role audit -> answerCallbackQuery`

Существующие nodes и их параметры не должны изменяться.

## Planned flow

После изменения:

`User found? -> Update role -> Send role confirm -> Insert role audit -> answerCallbackQuery -> Ensure profile session -> Prepare onboarding question -> Send onboarding question`

Причина размещения после `answerCallbackQuery`: Telegram callback должен быть подтверждён как можно раньше; создание/resume onboarding session не должно задерживать acknowledgement callback.

## New node 1 — Ensure profile session

Type: `n8n-nodes-base.postgres`

Operation: `executeQuery`

Purpose:

- найти существующую `IN_PROGRESS` session пользователя;
- если её нет — создать ровно одну session в рамках обычного execution;
- новую session создать с `current_step = 0`;
- существующую session НЕ сбрасывать на 0;
- вернуть `id`, `user_id`, `profile_id`, `current_step`, `ai_context`, `status`.

SQL for n8n expression context:

```sql
WITH existing AS (
  SELECT
    id,
    user_id,
    profile_id,
    current_step,
    COALESCE(ai_context, '{}'::jsonb) AS ai_context,
    status
  FROM profile_ai_sessions
  WHERE user_id = '{{$('Resolve user').item.json.user_id}}'
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
    '{{$('Resolve user').item.json.user_id}}',
    NULL,
    0,
    '{}'::jsonb,
    'IN_PROGRESS',
    now(),
    now()
  WHERE NOT EXISTS (SELECT 1 FROM existing)
  RETURNING
    id,
    user_id,
    profile_id,
    current_step,
    COALESCE(ai_context, '{}'::jsonb) AS ai_context,
    status
)
SELECT * FROM existing
UNION ALL
SELECT * FROM inserted
LIMIT 1;
```

`alwaysOutputData` should be enabled, consistent with critical Postgres nodes in current WF_01.

## New node 2 — Prepare onboarding question

Preferred type: `n8n-nodes-base.set`.

It must preserve at least:

- `session_id`
- `current_step`
- `question_text`

Suggested expressions:

```text
session_id = {{$json.id}}
current_step = {{$json.current_step}}
question_text = {{[
  'Как тебя зовут?',
  'Сколько тебе лет?',
  'В каком городе живёшь?',
  'Расскажи немного о себе.',
  'Какие у тебя интересы?',
  'Какова цель знакомства?',
  'Расскажи о своих хобби. Можно пропустить.',
  'Чем ты занимаешься / где работаешь? Можно пропустить.',
  'Какое у тебя образование? Можно пропустить.',
  'Какой стиль общения тебе ближе? Можно пропустить.'
][$json.current_step] || 'Анкета уже заполнена.'}}
```

Критический инвариант: повторный role callback для пользователя с `current_step > 0` должен задавать вопрос текущего шага, а не снова имя.

## New node 3 — Send onboarding question

Type: `n8n-nodes-base.telegram`

Resource: `message`

Operation: `sendMessage`

```text
chatId = {{$('Extract role vars').item.json.chat_id}}
text = {{$('Prepare onboarding question').item.json.question_text}}
```

Использовать тот же Telegram credential, что и существующие `Send role confirm` / `Send start prompt`.

## Connection changes

Сохранить все существующие connections.

Единственное расширение существующего графа:

1. `answerCallbackQuery -> Ensure profile session`
2. `Ensure profile session -> Prepare onboarding question`
3. `Prepare onboarding question -> Send onboarding question`

Не удалять callback, registration или role connections.

## Expected graph after patch

Nodes: 22 (19 existing + 3 new).

Active production: без изменений.

Draft: 22 nodes после `update_workflow`.

## Verification after draft update

После изменения выполнить только read-only проверку:

1. `get_workflow_details`.
2. Убедиться, что top-level draft содержит 22 nodes.
3. Убедиться, что Active по-прежнему содержит 19 nodes.
4. Убедиться, что `activeVersionId` по-прежнему `d2678798-5807-4813-8e24-7a819285b298`.
5. Проверить, что все 19 старых node IDs/parameters сохранены.
6. Проверить новые nodes и connections.
7. Проверить, что `publish_workflow` НЕ вызывался.

## Verified draft state after Stage 1 update

Read-only verification after `update_workflow` confirmed:

- Draft nodes: `22`
- Active nodes: `19`
- New draft version ID: `ebbbc76d-281e-4189-94f5-ee1ab9feb0d1`
- Active version ID unchanged: `d2678798-5807-4813-8e24-7a819285b298`
- All 19 original nodes preserved with matching node IDs
- Added nodes present: `Ensure profile session`, `Prepare onboarding question`, `Send onboarding question`
- Added connections present and correct
- Existing registration/callback/role connections preserved
- `publish_workflow` was not called

## Credential blocker before publish

The draft update auto-assigned credentials to new nodes because credential identifiers are redacted from `get_workflow_details` output.

Observed assignments:

- `Ensure profile session` -> `Postgres account`
- `Send onboarding question` -> `Telegram account`

`Send onboarding question` MUST use the same Telegram credential as the existing production node `Send role confirm` (the project bot, expected to be one of the credentials named `@vstrechi18bot`). The auto-assigned generic `Telegram account` is not accepted for publish.

Before any publish:

1. Determine the exact credential ID used by existing `Send role confirm` using a read-only source if possible.
2. Rebind ONLY `Send onboarding question` to that exact credential in draft.
3. Verify the Postgres credential for `Ensure profile session` matches the existing production Postgres credential used by WF_01 nodes.
4. Re-run `get_workflow_details` and validation.
5. Keep Active unchanged until explicit user approval.

If the MCP/API cannot expose existing credential IDs read-only, the user must inspect the credential selection in the n8n UI. Do not guess between multiple similarly named credentials.

## Test cases after eventual publish

Publish не входит в этот patch, но будущий smoke test должен покрыть:

1. Новый пользователь -> `/start` -> выбор роли -> session создана -> вопрос `Как тебя зовут?`.
2. Повторный callback роли при существующей session step 0 -> новая session не создаётся.
3. Existing session step 3 -> повторный callback -> сохраняется step 3, задаётся вопрос шага 3.
4. Callback неизвестного пользователя -> существующая ветка `answerCallbackQuery (not found) -> Send start prompt` остаётся без изменений.

## Known concurrency limitation

В schema 002 пока нет partial unique index вида `UNIQUE(user_id) WHERE status='IN_PROGRESS'`. Поэтому абсолютная DB-level защита от двух параллельных inserts ещё не гарантирована. Этот schema-hardening следует сделать отдельной миграцией после проверки существующих данных, а не смешивать с первым n8n draft patch.
