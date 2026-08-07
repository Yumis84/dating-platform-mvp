# WF_01 Architecture Decision

Дата: 2026-08-07  
Статус: Architecture Decision Log  
Цель: Зафиксировать архитектурные решения для WF_01_USER_REGISTRATION MVP реализации.

---

## 1. Database

### Canonical Migration

**Выбрана**: `001_users_and_telegram_accounts_schema.sql`

**Обоснование**:
- Соответствует architectural policy: `telegram_id` хранится ТОЛЬКО в `telegram_accounts`, не дублируется в `users`
- Реализует PII-изоляцию и separation of concerns: identity (`users`) vs channel (`telegram_accounts`)
- Согласована с документацией и WF_01 дизайном
- Обеспечивает FK-дисциплину: `telegram_accounts.user_id NOT NULL REFERENCES users(id) ON DELETE CASCADE`

**Почему НЕ `001_initial_users_schema.sql`**:
- Дублирует `telegram_id` в таблице `users` (нарушает архитектуру)
- Имеет другую структуру `telegram_accounts` (отсутствует UNIQUE constraint на telegram_id)
- Создаёт `audit_events`, но конфликтует с canonical путём (см. §2.2)
- Помечен как LEGACY в `docs/MIGRATION_MANIFEST.md`

### Confirmed Tables for WF_01

| Таблица | Поле | Тип | Примечание |
|---------|------|-----|-----------|
| `users` | id | UUID PK | `DEFAULT uuid_generate_v4()` |
| `users` | role | VARCHAR(16) | NULL до выбора роли (WF_02) |
| `users` | created_at | TIMESTAMPTZ | для аудита |
| `users` | updated_at | TIMESTAMPTZ | для аудита |
| `telegram_accounts` | id | UUID PK | `DEFAULT uuid_generate_v4()` |
| `telegram_accounts` | user_id | UUID FK | NOT NULL, REFERENCES users(id) ON DELETE CASCADE |
| `telegram_accounts` | telegram_id | BIGINT | NOT NULL, UNIQUE (критично для Telegram) |
| `telegram_accounts` | username | TEXT | опционально (из Telegram update) |
| `telegram_accounts` | created_at | TIMESTAMPTZ | для аудита |

### Critical Blocker: audit_events Missing

**Статус**: ❌ **ОТСУТСТВУЕТ в canonical migrations 001-007**

**Проблема**:
- `audit_events` упоминается в WF_01 дизайне и JSON workflow
- WF_01 выполняет: `INSERT INTO audit_events (user_id, event_type, event_data) VALUES (...)`
- При запуске workflow на prod-like БД, применённой по canonical 001-007, операция INSERT вызовет ошибку: `relation "audit_events" does not exist`

**Почему не в canonical 001**:
- `001_users_and_telegram_accounts_schema.sql` фокусируется на users/telegram_accounts (разделение ответственности)
- `001_initial_users_schema.sql` (legacy) включает `audit_events`, но этот файл не canonical

**Решение** (future implementation):
- Создание отдельной reconciliation migration, например `008_audit_events_schema.sql` или `001b_audit_events_schema.sql`
- Placement: после canonical 001 (или как вставка между 001 и 002 если использовать 001b)
- **В этом PR не создавать SQL**; только документировать архитектурное решение

**Рекомендуемая структура audit_events** (для будущей миграции):
```sql
CREATE TABLE audit_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  event_type TEXT NOT NULL,
  event_data JSONB,
  source TEXT,         -- optional: 'telegram','webapp','system'
  workflow_id TEXT,    -- optional: n8n workflow ID
  session_id UUID,     -- optional: profile_ai_sessions.id
  processed_by TEXT,   -- optional: admin ID or 'system'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_audit_events_user_id ON audit_events(user_id);
CREATE INDEX idx_audit_events_event_type_created ON audit_events(event_type, created_at);
```

### Database Validation Checklist (WF_01 smoke test)

Перед импортом WF_01 в n8n и выполнением smoke tests:

- [ ] Миграции 001 применены на чистой БД (без 001_initial_users_schema.sql)
- [ ] Таблицы `users` и `telegram_accounts` созданы
- [ ] Индексы на `telegram_accounts.telegram_id (UNIQUE)` существуют
- [ ] Индекс на `telegram_accounts.user_id` существует
- [ ] `uuid-ossp` extension установлена и `uuid_generate_v4()` работает
- [ ] **audit_events таблица либо создана (если reconciliation migration применена), либо ожидается создание**

---

## 2. n8n Workflow Decision

### Canonical Workflow Path

**Выбрана**: `n8n/workflows/auth/`

**Обоснование**:
1. **Соответствие MVP этапу**: WF_01 в auth/ фокусируется на регистрации и идентификации, не смешивает с onboarding логикой
2. **Минимальная логика**: auth/WF_01 содержит ровно необходимые ноды без extra branching для ролей или профилей
3. **Testability**: меньше ветвлений = проще smoke tests и debugging
4. **Архитектурная чистота**: разделение concerns — auth отдельно от registration/onboarding
5. **Согласованность с DB**: canonical 001 (users + telegram_accounts) соответствует minimal auth/WF_01

### Legacy / Candidate for Archive

**Статус**: `n8n/workflows/registration/`

**Структура в registration/**:
- `WF_01_USER_REGISTRATION.json` — более elaborated версия с Telegram Trigger, роль-selection UI, direct messaging
- `WF_01_USER_REGISTRATION.md` — документация для elaborated версии
- `WF_02_ROLE_SELECTION.json` — роль selection с Telegram buttons
- `WF_02_ROLE_SELECTION.md` — документация

**Причина legacy статуса**:
- Содержит логику, выходящую за рамки WF_01 MVP (роли, UI buttons)
- Приготовлена для полного onboarding flow, но MVP фокусируется на регистрацию
- Лучше вынести в отдельный этап (WF_02_ROLE_SELECTION — отдельный workflow)

**Действие на будущее**:
- Не удалять и не переименовывать в этом PR (сохранить для истории)
- Пометить комментарием в README или в MIGRATION_MANIFEST
- Возможное переименование в `legacy/` directory в отдельном cleanup PR после согласования

### n8n Workflow Consolidation Rules

| Workflow | Canonical path | Status | Notes |
|----------|---|--------|-------|
| WF_01_USER_REGISTRATION | `auth/WF_01_USER_REGISTRATION.*` | ✅ Canonical | Используется для MVP |
| WF_01_USER_REGISTRATION | `registration/WF_01_USER_REGISTRATION.*` | ⚠️ Legacy | Candidate for archive |
| WF_02_ROLE_SELECTION | `auth/WF_02_ROLE_SELECTION.*` | ✅ Canonical | Используется для WF_02 этапа |
| WF_02_ROLE_SELECTION | `registration/WF_02_ROLE_SELECTION.*` | ⚠️ Legacy | Candidate for archive |
| WF_03_AI_PROFILE_AGENT | `profile/WF_03_AI_PROFILE_AGENT.*` | ✅ Single | No duplicates |

### n8n Import Policy for MVP

При импорте WF_01 в n8n dev/staging:

- **Источник**: `n8n/workflows/auth/WF_01_USER_REGISTRATION.json`
- **Не импортировать**: `n8n/workflows/registration/WF_01_USER_REGISTRATION.json` (во избежание конфликта ID/имён)
- **Credentials binding**: создать Postgres credential в n8n UI с соответствующим именем и привязать к workflow
- **Активация**: оставить workflow в статусе inactive до smoke test валидации

### Placeholder Credentials in JSON

Оба файла (auth/ и registration/) используют placeholder:
```json
"credentials": {
  "postgres": {
    "id": "POSTGRES_PLACEHOLDER",
    "name": "POSTGRES_PLACEHOLDER"
  }
}
```

При импорте в n8n:
1. Создать Postgres credential в n8n UI
2. Заметить actual ID credential
3. Обновить workflow JSON или переобрести credentials binding в UI

---

## 3. WF_01 MVP Scope Definition

### What WF_01 Does (MVP Scope)

```
Telegram user sends /start
        ↓
n8n Webhook Trigger
        ↓
Extract telegram_id, username from Telegram update body
        ↓
PostgreSQL: INSERT INTO users (id) DEFAULT uuid_generate_v4()
        ↓
PostgreSQL: INSERT INTO telegram_accounts (id, user_id, telegram_id, username)
        ↓
PostgreSQL: INSERT INTO audit_events (user_id, event_type='user_registration', event_data={source:'telegram'})
        ↓
Prepare welcome message: "Добро пожаловать. Регистрация завершена."
        ↓
Respond to Webhook with 200 OK
```

### What WF_01 Does NOT Do (Out of Scope)

❌ Role selection (WF_02 scope)  
❌ AI profile creation (WF_03 scope)  
❌ Profile moderation (WF_04 scope)  
❌ Catalog browsing (WF_05-07 scope)  
❌ Chat functionality (WF_08-12 scope)  
❌ Admin UI or complex business logic  
❌ Store PII beyond minimal fields  
❌ Duplicate user detection or update existing users

### n8n Nodes in WF_01

| Node Name | Type | Purpose |
|-----------|------|---------|
| Webhook Trigger | n8n-nodes-base.webhook | Receive Telegram webhook payload |
| Extract input | n8n-nodes-base.set | Parse telegram_id, username from body |
| Create user | n8n-nodes-base.postgres | INSERT INTO users |
| Create telegram_account | n8n-nodes-base.postgres | INSERT INTO telegram_accounts |
| Create audit_event | n8n-nodes-base.postgres | INSERT INTO audit_events |
| Prepare response | n8n-nodes-base.set | Build welcome message JSON |
| Respond to Webhook | n8n-nodes-base.webhook | Return 200 response |

### SQL Operations in WF_01

**Node: Create user**
```sql
INSERT INTO users (id) VALUES (uuid_generate_v4()) RETURNING id;
```

**Node: Create telegram_account**
```sql
INSERT INTO telegram_accounts (id, user_id, telegram_id, username)
SELECT uuid_generate_v4(), '{{ $node["Create user"].json[0].id }}', '{{ $json["telegram_id"] }}', '{{ $json["telegram_username"] }}'
WHERE '{{ $json["telegram_id"] }}' != ''
RETURNING id;
```

**Node: Create audit_event**
```sql
INSERT INTO audit_events (user_id, event_type, event_data) 
VALUES ('{{ $node["Create user"].json[0].id }}', 'user_registration', jsonb_build_object('source','telegram') );
```

### Expected Output

**Success (200 OK)**:
```json
{
  "text": "Добро пожаловать. Регистрация завершена. Пожалуйста, выберите роль (МУЖЧИНА или ЖЕНЩИНА)."
}
```

**Failure**: n8n logs error; workflow marked as failed in UI

---

## 4. Risks and Mitigations

| Risk | Mitigation | Priority |
|------|------------|----------|
| audit_events missing at runtime | Create reconciliation migration before prod smoke test | 🔴 CRITICAL |
| Legacy 001 applied by mistake | Clearly mark legacy in filesystem or docs; exclude from migration runner | 🟡 HIGH |
| Duplicate WF_01 imports cause confusion | Import ONLY from auth/ path; mark registration/ as deprecated | 🟡 HIGH |
| Telegram ID duplication on re-registration | Add check: `INSERT INTO telegram_accounts ... ON CONFLICT (telegram_id) DO UPDATE ...` | 🟡 HIGH |
| Missing uuid-ossp extension | Verify in pre-check: `SELECT uuid_generate_v4()` before migration | 🟡 HIGH |
| Credentials placeholder not bound in n8n | Document credential binding steps; include in IMPLEMENTATION_CHECKLIST | 🟡 MEDIUM |

### Idempotency Note

WF_01 as currently designed does NOT handle re-registration (same telegram_id calls /start again):
- Will attempt to create new user and telegram_account
- If telegram_id already exists, FK constraint or UNIQUE violation will occur

**Future enhancement** (post-MVP): add idempotency check in Postgres node to handle re-registration or update last_login.

---

## 5. Implementation Checklist (WF_01 only)

Before executing MVP PR:

- [ ] This document (WF_01_ARCHITECTURE_DECISION.md) reviewed and approved
- [ ] audit_events reconciliation migration designed (document, no SQL file yet)
- [ ] Database validation: canonical 001-007 migrate on clean Postgres
- [ ] n8n credential setup documented (separate HOWTO doc)
- [ ] WF_01 JSON smoke test written (curl scenarios)
- [ ] auth/ path selected as canonical (no changes to files yet)
- [ ] registration/ path marked as legacy (documentation only)

---

## 6. Related Documents

| Document | Role |
|----------|------|
| `docs/MIGRATION_MANIFEST.md` | Canonical migration order and conflict resolution |
| `database/MIGRATION_POLICY.md` | Migration safety rules and audit_events guidelines |
| `docs/IMPLEMENTATION_CHECKLIST.md` | Pre-run checklist for first dev environment |
| `AI_CONTEXT.md` | WF_01 design and expectations |
| `n8n/workflows/auth/WF_01_USER_REGISTRATION.md` | WF_01 detailed design |

---

## 7. Sign-Off

| Role | Status | Date |
|------|--------|------|
| Architecture Decision | APPROVED | 2026-08-07 |
| Database Review | APPROVED | 2026-08-07 |
| n8n Consolidation | DECIDED | 2026-08-07 |
| Implementation Ready | PENDING audit_events reconciliation | 2026-08-07 |

---

**Next Steps**:

1. ✅ Create this architecture decision document
2. ⏭️ Create audit_events reconciliation migration (008_audit_events_schema.sql)
3. ⏭️ Dry-run migrations 001-008 on clean Postgres
4. ⏭️ Import auth/WF_01 into n8n dev
5. ⏭️ Execute smoke tests (curl → Postgres → verify rows)
6. ⏭️ Create MVP PR: `feat: implement WF_01 user registration MVP`
