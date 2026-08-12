# Dating Platform MVP — контекст для переноса между чатами

> Этот файл создан как переносимый контекст проекта. Новый ChatGPT должен сначала прочитать его, затем связанные canonical-файлы репозитория, и только после этого продолжать разработку.

## 1. Правило продолжения

Ты работаешь над проектом `Yumis84/dating-platform-mvp`.

Главная задача сейчас — продолжить разработку Telegram-first Dating Platform MVP, не ломая уже работающий Telegram/n8n flow.

**Не считать старый чат источником истины.** Источники истины:
1. текущий код и SQL в GitHub;
2. этот файл как накопленный контекст текущего этапа;
3. подтверждённые пользователем сведения о live n8n.

Перед любыми изменениями:
- прочитай этот файл;
- прочитай `README.md`;
- прочитай `database/migrations/002_profiles_schema.sql`;
- прочитай `database/migrations/003_moderation_schema.sql`;
- прочитай `database/PROFILE_DESIGN.md`;
- прочитай `docs/architecture/REGISTRATION_FLOW.md`;
- прочитай `docs/architecture/AI_PROFILE_FLOW.md`;
- прочитай `n8n/workflows/profile/WF_03_AI_PROFILE_AGENT.md` и JSON;
- если работа касается WF_01, отдельно проверь его live-состояние через подключённый n8n/MCP, а не предполагай, что GitHub JSON совпадает с production.

**Не публиковать изменения в production без отдельного явного подтверждения пользователя.**

---

## 2. Цель продукта

MVP — Telegram-first сервис знакомств.

Основные компоненты из репозитория:
- Telegram Bot;
- Telegram WebApp;
- n8n как оркестратор;
- PostgreSQL как основная БД;
- Google Sheets как дополнительное MVP-хранилище;
- AI Agent для рекомендаций, обработки контента и модерации.

Текущий этап сфокусирован на создании/заполнении профиля через Telegram и n8n.

---

## 3. Canonical схема профиля

### `profiles`
Публичная анкета.

Фактическая миграция `002_profiles_schema.sql` содержит:
- `id UUID PK`;
- `user_id UUID NOT NULL FK users(id) ON DELETE CASCADE`;
- `status VARCHAR(32) NOT NULL DEFAULT 'DRAFT'`;
- CHECK: `DRAFT | PENDING_MODERATION | ACTIVE | BLOCKED`;
- `name TEXT`;
- `age INT`;
- `city TEXT`;
- `description TEXT`;
- `interests JSONB`;
- `preferences JSONB`;
- timestamps.

Важно: `profiles.status` — **lifecycle публикации/модерации**, а не номер шага анкеты.

### `profile_photos`
Метаданные фотографий:
- `profile_id`;
- `telegram_file_id`;
- `position`;
- timestamp.

Бинарные изображения в БД не хранятся.

### `profile_ai_sessions`
Состояние AI-assisted заполнения профиля:
- `id`;
- `user_id`;
- `profile_id`;
- `current_step INT DEFAULT 0`;
- `ai_context JSONB`;
- `status VARCHAR(32) DEFAULT 'IN_PROGRESS'`;
- timestamps.

**`current_step` — каноническое состояние onboarding.**

### `profile_fields_history`
Аудит изменений полей профиля.

Подробности подтверждены миграцией и `PROFILE_DESIGN.md`.

---

## 4. Каноническое соответствие шагов анкеты

По `WF_03_AI_PROFILE_AGENT`:

| current_step | ai_context | Вопрос |
|---:|---|---|
| 0 | `name` | Как тебя зовут? |
| 1 | `age` | Сколько тебе лет? |
| 2 | `city` | В каком городе живёшь? |
| 3 | `description` | Расскажи немного о себе |
| 4 | `interests` | Какие у тебя интересы? |
| 5 | `purpose` | Какова цель знакомства? |
| 6 | `hobbies` | Хобби — необязательно |
| 7 | `job` | Работа — необязательно |
| 8 | `education` | Образование — необязательно |
| 9 | `communication_style` | Предпочтительный стиль общения — необязательно |
| >=10 | — | завершение |

Обязательные поля по canonical WF_03:
- name;
- age;
- city;
- description;
- interests;
- purpose.

Опциональные:
- hobbies;
- job;
- education;
- communication_style.

После завершения профиль должен переходить в `PENDING_MODERATION`.

---

## 5. Canonical WF_03

GitHub содержит `n8n/workflows/profile/WF_03_AI_PROFILE_AGENT.json` и `.md`.

По документации WF_03:
- webhook принимает `user_id`, опционально `session_id`, `user_answer`, `photo_file_id`;
- если session не существует — создаётся `profile_ai_session`;
- существующая `IN_PROGRESS` session должна продолжаться;
- ответ записывается в `ai_context`;
- `current_step` увеличивается;
- photo сохраняется как Telegram `file_id` metadata;
- после обязательных полей создаётся `profiles` со статусом `PENDING_MODERATION`;
- создаётся `profile_created` audit event;
- вызывается WF_04 moderation через `WF_04_TRIGGER_URL`;
- при ошибке AI session должна оставаться `IN_PROGRESS`.

Важно: текущий GitHub JSON — **шаблон/canonical WF_03**, а не доказательство того, что этот workflow сейчас используется production.

---

## 6. Текущее live-состояние WF_01

Это было подтверждено в предыдущем аудите через Claude и передано пользователем в этот чат.

Production WF_01 имеет актуальную опубликованную версию:

`d2678798-5807-4813-8e24-7a819285b298`

В опубликованной версии было **18 nodes** и уже работала callback-логика Telegram:
- `callback_query`;
- `role:man` / `role:woman`;
- `Update role`;
- `Send role confirm`;
- `Extract role vars`;
- `Answer Callback Query`;
- DeepSeek/AI ветки, существующие в live.

При этом `get_workflow_details` показывал одновременно:

- top-level `nodes/connections` — **9-node draft**, старый граф;
- `activeVersion.nodes/connections` — **18-node published/production graph**.

### Критическое правило
**Production source of truth = `activeVersion`, а не top-level draft.**

`update_workflow` редактирует draft.

Поэтому нельзя брать старый 9-node top-level граф как основу для изменений WF_01.

---

## 7. Что произошло при предыдущей попытке изменения

Claude пытался изменить WF_01 через `update_workflow` и одновременно удалить connection:

`Update role -> Send role confirm`

Операция упала, потому что `Update role` существует в 18-node `activeVersion`, но отсутствует в 9-node draft.

Операция была атомарной и **ничего не изменила**.

Это важно: production не был откатан и callback/DeepSeek логика не потеряна.

---

## 8. Безопасная модель n8n draft/published

В данной инсталляции нужно считать модель такой:

```text
activeVersion (production)
        ↓
restore_workflow_version
        ↓
draft = копия актуальной published version
        ↓
update_workflow
        ↓
verify draft
        ↓
publish_workflow
        ↓
новый activeVersion / production
```

### Инструменты

`get_workflow_details`
- read-only;
- показывает draft и activeVersion.

`get_workflow_version(versionId)`
- read-only;
- возвращает полный исторический snapshot версии.

`restore_workflow_version(versionId)`
- **изменяет draft, но не публикует production**;
- безопасный способ подготовить draft из известной рабочей published version.

`update_workflow`
- редактирует draft;
- нельзя использовать, если draft основан на старом неполном графе.

`publish_workflow`
- публикует текущий draft;
- **изменяет production**;
- требует отдельного подтверждения пользователя.

### Безопасный порядок

1. READ-ONLY аудит.
2. Backup: published version уже существует в workflow history.
3. `restore_workflow_version(d2678798-...)` → подготовить правильный draft.
4. `update_workflow` → изменить полный 18-node граф.
5. `get_workflow_details` → проверить draft.
6. Отдельно получить подтверждение пользователя.
7. `publish_workflow` → сделать изменения live.
8. Пользователь вручную выполняет Telegram smoke test.

**Никогда не вызывать `publish_workflow` без явного подтверждения.**

---

## 9. Следующий этап разработки — ЭТАП 1

Цель:

После выбора роли в существующем WF_01 начать/продолжить пошаговое заполнение профиля через `profile_ai_sessions.current_step`.

### После `role_selected`

Для WOMAN flow основной сценарий:

1. Найти существующую `IN_PROGRESS` profile session.
2. Если её нет — создать.
3. Установить/сохранить `current_step = 0`.
4. Спросить имя.

### Для обычного Telegram message

После Telegram Trigger:

```text
callback_query /start
    → существующая регистрация/role логика

обычное message
    → найти IN_PROGRESS profile_ai_session
       ├─ есть → обработать как ответ анкеты
       └─ нет → не считать сообщением анкеты
```

Нужно обязательно различать:
- callback;
- `/start`;
- ответ на onboarding;
- обычное сообщение;
- фото.

---

## 10. Предлагаемые новые nodes для ЭТАПА 1

После успешного выбора роли:

1. `Find/Create Profile Session`
2. `Ask Name`

В message-ветку:

3. `Is Onboarding Answer?`
4. `Load Session`
5. `Switch by current_step` или Function
6. `Save Field + Advance Step`
7. `Save Photo` при необходимости
8. `Ask Next Question` / `Finalize Profile`
9. `Audit + Trigger Moderation` при завершении

Точные названия можно изменить, но смысл должен сохраниться.

---

## 11. SQL-логика ЭТАПА 1

### Создание session

```sql
INSERT INTO profile_ai_sessions (user_id, current_step, status, ai_context)
SELECT $user_id, 0, 'IN_PROGRESS', '{}'::jsonb
WHERE NOT EXISTS (
  SELECT 1
  FROM profile_ai_sessions
  WHERE user_id = $user_id
    AND status = 'IN_PROGRESS'
)
RETURNING id, current_step;
```

### Сохранение ответа

```sql
UPDATE profile_ai_sessions
SET ai_context = ai_context || jsonb_build_object(
  CASE current_step
    WHEN 0 THEN 'name'
    WHEN 1 THEN 'age'
    WHEN 2 THEN 'city'
    WHEN 3 THEN 'description'
    WHEN 4 THEN 'interests'
    WHEN 5 THEN 'purpose'
    ELSE 'extra'
  END,
  to_jsonb($answer)
),
current_step = current_step + 1,
updated_at = now()
WHERE id = $session_id
  AND status = 'IN_PROGRESS'
RETURNING id, current_step, ai_context;
```

### Finalization

```sql
INSERT INTO profiles (
  user_id,
  status,
  name,
  age,
  city,
  description,
  interests
)
SELECT
  user_id,
  'PENDING_MODERATION',
  ai_context->>'name',
  (ai_context->>'age')::int,
  ai_context->>'city',
  ai_context->>'description',
  COALESCE(ai_context->'interests', '[]'::jsonb)
FROM profile_ai_sessions
WHERE id = $session_id
  AND NOT EXISTS (
    SELECT 1
    FROM profiles
    WHERE user_id = profile_ai_sessions.user_id
  )
RETURNING id;
```

После успешного создания:

```sql
UPDATE profile_ai_sessions
SET status = 'COMPLETED',
    profile_id = $profile_id,
    updated_at = now()
WHERE id = $session_id;
```

---

## 12. Защита от дублей

Нельзя создавать новую IN_PROGRESS session при каждом `/start`.

Правила:
- один активный onboarding должен переиспользоваться;
- повторный `/start` не должен создавать дубли `users` или `telegram_accounts`;
- существующую `IN_PROGRESS` profile session нужно продолжать;
- при финализации дополнительно проверять существующий profile.

В текущей миграции 002 **нет UNIQUE(user_id) на profiles**, поэтому защита от дублей должна быть реализована на уровне логики/SQL до отдельного изменения схемы.

---

## 13. `/restart`

Canonical документация не содержит официальной команды `/restart`.

Если её добавлять, предпочтительный вариант:

```sql
UPDATE profile_ai_sessions
SET current_step = 0,
    ai_context = '{}'::jsonb,
    updated_at = now()
WHERE user_id = $user_id
  AND status = 'IN_PROGRESS';
```

Но **не добавлять `/restart` самовольно**, если пользователь отдельно не подтвердил это решение.

---

## 14. Модерация

После финализации:

```text
profiles.status = PENDING_MODERATION
        ↓
profile_moderation
        ↓
WF_04 AI moderation
        ↓
ACTIVE / BLOCKED
```

Миграция `003_moderation_schema.sql` подтверждает таблицы:
- `profile_moderation`;
- `moderation_rules`;
- `moderation_history`.

---

## 15. Что пока НЕ делать

Без отдельного решения пользователя:

- не делать `ALTER TABLE` для profile schema;
- не менять `profiles.status` на onboarding state;
- не публиковать WF_01;
- не удалять существующие callback/DeepSeek nodes;
- не переписывать production workflow из 9-node draft;
- не создавать отдельную новую архитектуру вместо согласованной;
- не добавлять `/restart` без подтверждения;
- не считать canonical WF_03 JSON production source of truth для live WF_01.

---

## 16. Важное расхождение документации и фактического состояния

GitHub README и часть старой документации описывают проект как ранний MVP, где workflows ещё только планировались. Например, README содержит старый статус подготовки инфраструктуры.

Это **историческая документация**, а не описание текущего live-состояния.

Поэтому при конфликте:

```text
LIVE / подтверждённый production
        >
текущий GitHub workflow/code
        >
старый README / ранние design notes
```

Но для схемы БД canonical migration остаётся источником истины, пока live DB не покажет обратное.

---

## 17. Не найденный файл TZ_02

В текущем репозитории по ожидаемому пути `docs/tz/02_PROFILE_AI_AGENT/...` через GitHub API конкретный файл из старого аудита не был найден. Не придумывать его содержимое.

Если понадобится точная сверка TZ_02 — найти фактическое имя файла через GitHub search.

---

## 18. Что уже проверено read-only

Подтверждены через GitHub:
- `README.md`;
- `database/migrations/002_profiles_schema.sql`;
- `database/migrations/003_moderation_schema.sql`;
- `database/PROFILE_DESIGN.md`;
- `docs/architecture/REGISTRATION_FLOW.md`;
- `docs/architecture/AI_PROFILE_FLOW.md`;
- `docs/IMPLEMENTATION_CHECKLIST.md`;
- `n8n/workflows/profile/WF_03_AI_PROFILE_AGENT.md`;
- `n8n/workflows/profile/WF_03_AI_PROFILE_AGENT.json`.

Изменений этих файлов в рамках подготовки этого контекста нет.

---

## 19. Инструкция новому ChatGPT

Начни новый чат с этого текста:

> **Проект Dating Platform MVP.**
> Прочитай файл `docs/PROJECT_CONTEXT_TRANSFER.md` в репозитории `Yumis84/dating-platform-mvp` и все указанные в нём canonical-файлы. Это основной контекст переноса. Не начинай изменения сразу. Сначала кратко подтверди, что понял текущее состояние проекта, особенно разницу между draft и production `activeVersion` WF_01, версию `d2678798-5807-4813-8e24-7a819285b298` и план ЭТАПА 1. После этого продолжай с последнего незавершённого шага.

Если работа идёт с n8n:
- сначала read-only проверка;
- для WF_01 production source of truth — `activeVersion`;
- перед `update_workflow` draft должен быть подготовлен из актуальной published version;
- после изменения draft обязательно verify;
- publish только после моего отдельного подтверждения.

---

## 20. Текущая точка остановки

На момент создания этого файла:

**ЭТАП 1 ещё НЕ реализован в live WF_01.**

Последнее безопасное решение:

```text
restore published WF_01 version d2678798...
        ↓
получить правильный 18-node draft
        ↓
добавить onboarding nodes
        ↓
verify
        ↓
отдельное подтверждение
        ↓
publish
```

Никаких предположений, что эти изменения уже сделаны, быть не должно.

---

## Источники

- `README.md`
- `database/migrations/002_profiles_schema.sql`
- `database/migrations/003_moderation_schema.sql`
- `database/PROFILE_DESIGN.md`
- `docs/architecture/REGISTRATION_FLOW.md`
- `docs/architecture/AI_PROFILE_FLOW.md`
- `docs/IMPLEMENTATION_CHECKLIST.md`
- `n8n/workflows/profile/WF_03_AI_PROFILE_AGENT.md`
- `n8n/workflows/profile/WF_03_AI_PROFILE_AGENT.json`

Дополнительные сведения о live WF_01, `activeVersion`, версии `d2678798...` и draft/published механике основаны на read-only аудите, выполненном ранее в этом проектном чате и предоставленном пользователем/Claude/Grok. Эти сведения не следует выдавать за данные из GitHub, если они там не подтверждены.

## 2026-08-11 — Role-separated MAN/WOMAN architecture draft

This append-only entry records repository-only feature work in branch `agent/man-woman-onboarding-ranking`. It does not replace the historical production/DEV handoff above.

- MAN onboarding is private search context: confirm or manually enter name, save normalized catalog city, then optionally configure ranking preferences or open the catalog. MAN never receives a public `profiles` row.
- WOMAN onboarding owns the public DRAFT profile and resumable `profile_ai_sessions` flow. WF_01 routes WOMAN text/photo events to inactive DEV WF_03 through an explicit webhook contract.
- The only catalog hard filters are ACTIVE status, WOMAN owner role, and normalized city equality. Nullable MAN preferences affect ranking only.
- Draft migrations 009/010 define structured WOMAN fields and private MAN state/preferences. They remain unapplied and require duplicate audits, a disposable-schema run, backup/rollback planning, and separate approval.
- All feature workflow artifacts remain DEV, inactive, not imported, and not published. Production workflow IDs, activeVersion history, restore rules, and publish warnings above remain authoritative safety context.

## 2026-08-12 — Corrective Postgres v2.6 and WOMAN lifecycle draft

- Every inactive DEV Postgres v2.6 node in WF_01/WF_03/WF_05 now uses the official `parameters.options.queryReplacement` path. A single serialized JSON value is bound to `$1::jsonb` and unpacked inside SQL, preserving commas in user-controlled text without interpolation.
- The old `parameters.additionalFields.queryParams` shape is forbidden by static tests.
- WF_01 resolves WOMAN lifecycle explicitly: IN_PROGRESS resumes, PENDING_MODERATION/COMPLETED returns the pending response, ACTIVE returns the ready state, and BLOCKED does not restart onboarding.
- Repeated `/start` and `role:woman` after completion do not create a new DRAFT profile or IN_PROGRESS session and do not return the first WOMAN question.
- Tests 14/15 verify only the WF_01/WF_03 payload/session contract. The real HTTP Request to Webhook handoff remains an unresolved runtime dependency until an isolated n8n DEV runtime is separately approved and available.
- These are repository-only drafts. No workflow was imported, activated, or published, and no migration or shared/production database change was performed.
