# MIGRATION_MANIFEST — Dating Platform MVP v1.0

Дата: 2026-08-07  
Статус: **канонический порядок миграций (документация)**  
Источник аудита: `docs/MIGRATION_AUDIT_REPORT.md`, `docs/PROJECT_CONSISTENCY_REPORT.md`  

> Этот файл **не изменяет** SQL. Он фиксирует, *какой* набор миграций считать рабочим и *как* безопасно разрешить конфликт `001_*`.

---

## 1. Канонический порядок миграций

Применять **только** в этом порядке (после разрешения конфликта 001):

| № | Файл | Создаёт / расширяет |
|---|------|---------------------|
| 1 | `001_users_and_telegram_accounts_schema.sql` | `users`, `telegram_accounts` |
| 2 | `002_profiles_schema.sql` | `profiles`, `profile_photos`, `profile_ai_sessions`, `profile_fields_history` |
| 3 | `003_moderation_schema.sql` | `profile_moderation`, `moderation_rules`, `moderation_history` |
| 4 | `004_catalog_schema.sql` | `profile_views`, `favorites`, `profile_search_events` |
| 5 | `005_chat_schema.sql` | `chat_sessions`, `messages`, `chat_blocks`, `chat_reports` |
| 6 | `006_chat_reliability_schema.sql` | `message_delivery_queue`, `message_rate_limits`, `chat_moderation_events` |
| 7 | `007_chat_message_moderation_schema.sql` | `message_moderation_queue` |

**Не включать в канонический прогон:**

- `001_initial_users_schema.sql` — legacy / conflict (см. §3)

---

## 2. Почему выбран `001_users_and_telegram_accounts_schema.sql`

Каноническая модель проекта (AI_CONTEXT, PROJECT_CONTEXT, WF design):

1. **`telegram_id` только в `telegram_accounts`**  
   Не дублировать Telegram ID в `users` (PII-изоляция, единая точка связи с Telegram).

2. **Минимальный `users`**  
   UUID PK, `role`, timestamps — без `first_name` / `username` на уровне users; контактные поля живут в `telegram_accounts`.

3. **Согласованность с WF_01…03**  
   Workflows описаны как: создать user → связать `telegram_accounts` → писать audit (отдельно).

4. **FK-дисциплина**  
   `telegram_accounts.user_id NOT NULL REFERENCES users(id) ON DELETE CASCADE`, `telegram_id BIGINT NOT NULL UNIQUE`.

5. **Масштабирование**  
   Разделение identity (users) и канала (telegram_accounts) упрощает будущие аккаунты / мульти-канальность.

Итог: файл `001_users_and_telegram_accounts_schema.sql` соответствует принятой архитектуре **source of truth = PostgreSQL + разделение PII**.

---

## 3. Почему `001_initial_users_schema.sql` — legacy / conflict

| Аспект | `001_initial_users_schema.sql` | Канон (`001_users_and_telegram_accounts…`) |
|--------|--------------------------------|--------------------------------------------|
| `users.telegram_id` | Есть (UNIQUE NOT NULL) | Нет — ID только в `telegram_accounts` |
| PII в users | username, first_name, last_name | Минимальная модель |
| role CHECK | `'man','woman','admin'` (lowercase) | VARCHAR без CHECK; WF ожидают `MAN`/`WOMAN` |
| `telegram_accounts` | telegram_id без UNIQUE/NOT NULL | NOT NULL UNIQUE + FK NOT NULL |
| `audit_events` | Создаётся здесь | **Отсутствует** в канон-001 |

**Конфликт:** оба файла — префикс `001_` и оба делают `CREATE TABLE users` / `telegram_accounts` с **разной** структурой.

Риски при «прогоне всего каталога»:

- непредсказуемый порядок (лексикографически `001_initial_…` идёт **перед** `001_users_…`);
- `IF NOT EXISTS` скрывает ошибку, оставляя **неверную** схему от initial;
- WF ломаются (ожидают telegram_id в accounts, role casing, audit_events).

**Оценка аудита:** применение миграций на prod/shared DB **заблокировано**, пока конфликт не разрешён.

---

## 4. План безопасного разрешения конфликта

Документационный план (SQL в этом PR **не меняется**). Выполнение — отдельный cleanup-PR после согласования.

### 4.1. Принципы

- Не удалять legacy-файл без бэкапа и записи в git history.  
- Не применять оба 001 на одну БД.  
- Сначала **чистая dev-БД**, потом staging.

### 4.2. Рекомендуемые шаги

1. **Зафиксировать канон** (этот manifest) — done.  
2. **Пометить legacy** (отдельный docs/SQL PR):  
   - переименовать, например:  
     `001_initial_users_schema.sql` → `legacy/001_initial_users_schema.sql.disabled`  
     **или**  
     `999_LEGACY_DO_NOT_RUN_001_initial_users_schema.sql`  
   - цель: исключить из автопрогона migrate, сохранив историю.
3. **Вынести `audit_events`** в отдельную миграцию после канон-001, например:  
   `001b_audit_events_schema.sql` **или** `008_audit_events_schema.sql`  
   (см. §5) — с FK на `users(id)` и индексом по `user_id`.
4. **Согласовать role casing** (`MAN`/`WOMAN` vs `man`/`woman`) в одном follow-up PR (CHECK + WF).  
5. **Dry-run на чистой Postgres** (§7).  
6. Только после green dry-run — dev/staging import WF smoke.

### 4.3. Что запрещено до cleanup

- Автоматический migrate «всех файлов в папке» на shared/prod.  
- Удаление legacy без записи в MIGRATION_AUDIT / этот manifest.  
- Смешивание схемы initial и users_and_telegram на одной БД.

---

## 5. Раздел `audit_events`

### 5.1. Текущее состояние

| Источник | Утверждение |
|----------|-------------|
| `001_initial_users_schema.sql` | Создаёт `audit_events` (user_id **без** FK) |
| `001_users_and_telegram_accounts_schema.sql` | **Не** создаёт `audit_events` |
| WF_01…03 / AI_CONTEXT | **Пишут** в `audit_events` |

Если применять только канон-001 → **таблица audit_events отсутствует** → runtime error в registration/role/profile flows.

### 5.2. Целевое решение (будущая миграция, не в этом PR)

Создать **ровно один** раз:

```text
audit_events (
  id UUID PK DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id),  -- предпочтительно ON DELETE SET NULL или CASCADE — согласовать
  event_type TEXT NOT NULL,
  event_data JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
)
INDEX ON audit_events (user_id)
INDEX ON audit_events (event_type, created_at)
```

Рекомендуемое имя файла (предложение): `001b_audit_events_schema.sql` сразу после канон-001, **или** `008_audit_events_schema.sql` в конце цепочки, если инструмент миграций требует строго монотонных номеров без суффиксов.

### 5.3. Временный workaround (только dev, осознанно)

Не рекомендуется для staging/prod. Если нужен быстрый smoke: вручную создать таблицу из §5.2 на dev после канон-001, затем оформить как миграцию.

---

## 6. Проверки перед миграциями

Чеклист перед любым прогоном:

- [ ] Прочитан этот **MIGRATION_MANIFEST** и `MIGRATION_AUDIT_REPORT.md`  
- [ ] В прогоне **нет** `001_initial_users_schema.sql`  
- [ ] Есть план для `audit_events` (миграция или явный skip smoke без audit)  
- [ ] Цель — **чистая** БД или подтверждённый snapshot  
- [ ] Есть **бэкап** (§7), если БД не пустая  
- [ ] `uuid-ossp` (или эквивалент) доступен в Postgres  
- [ ] Согласованы env: host, db name, user (не prod credentials в логах)  
- [ ] Role/status constants сверены с WF (MAN/WOMAN vs man/woman)  
- [ ] После migrate: `\dt` / information_schema — список таблиц соответствует §1 + audit  

---

## 7. Бэкап и dry-run

### 7.1. Бэкап (непустая БД)

```bash
# Пример (подставить свои параметры)
pg_dump -Fc -f backup_$(date +%Y%m%d_%H%M%S).dump "$DATABASE_URL"
```

Хранить dump вне контейнера (volume / object storage). Не коммитить dump в git.

### 7.2. Dry-run на чистой БД

1. Поднять disposable Postgres (docker).  
2. Применить **только** канонический список §1 (+ будущий audit, когда появится).  
3. Зафиксировать ошибки CREATE/FK.  
4. Проверить наличие таблиц: users, telegram_accounts, profiles, …, message_moderation_queue.  
5. Опционально: минимальный SQL insert user + telegram_account (без n8n).  
6. Уничтожить контейнер — схема не считается «боевой».

### 7.3. CI (рекомендация на будущее)

Job: Postgres service → migrate canonical set → fail on error.  
Не включать legacy 001 в CI path.

---

## 8. Связанные документы

| Документ | Роль |
|----------|------|
| `docs/MIGRATION_AUDIT_REPORT.md` | Детальный аудит Copilot |
| `docs/PROJECT_CONSISTENCY_REPORT.md` | Дубли и расхождения docs |
| `docs/PROJECT_CONTEXT.md` | Общий контекст (после merge PR #1) |
| `database/migrations/README.md` | Краткое описание каталога |
| `AI_CONTEXT.md` | Ожидания WF по таблицам |

---

## 9. Итог

| Вопрос | Ответ |
|--------|--------|
| Какой 001 применять? | **`001_users_and_telegram_accounts_schema.sql`** |
| Что с initial? | **Legacy / не запускать**; вынести из path отдельным PR |
| audit_events? | Нужна **отдельная** миграция после канон-001 |
| Можно ли сейчас migrate prod? | **Нет** — BLOCKER до cleanup 001 + audit |
| Этот PR меняет SQL? | **Нет** — только документация |
