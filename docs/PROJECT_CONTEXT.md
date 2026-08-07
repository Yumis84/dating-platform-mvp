# PROJECT_CONTEXT — Dating Platform MVP v1.0

Дата снимка: 2026-08-07  
Репозиторий: `Yumis84/dating-platform-mvp`  
Назначение файла: единый контекст для AI-агентов и разработчиков. Читать **до** изменения кода, миграций и workflow.

---

## 1. Описание проекта

Telegram-first платформа знакомств (MVP), где:

- мужчины просматривают анкеты и пишут через сервис;
- девушки создают анкеты (в т.ч. с помощью AI);
- общение идёт через **анонимный чат** (Telegram-контакты не раскрываются по умолчанию);
- система выступает **посредником**: модерация, фиксация взаимодействий, безопасность.

---

## 2. Цель MVP

Обеспечить рабочий поток:

**Регистрация → роль → AI-анкета → модерация → каталог → анонимный чат**

Далее (ещё не в runtime-схеме репозитория):

**Встречи → флаги безопасности / репутация → админ → платежи → аналитика → запуск**

---

## 3. Роли пользователей

| Роль | Возможности (MVP) |
|------|-------------------|
| **Мужчина** | Регистрация, каталог, фильтры, избранное, открытие чата, сообщения |
| **Женщина** | Регистрация, создание/ведение анкеты (AI), фото (file_id), получение сообщений, ответы |
| **Админ / модератор** | Модерация анкет и сообщений, жалобы, блокировки (дизайн; UI — частично) |

---

## 4. Функционал MVP (по этапам репозитория)

### Уже спроектировано в repo (design + migrations + n8n templates)

| Этап | Содержание |
|------|------------|
| 0 | Infrastructure (Docker, Postgres, n8n, nginx WebApp shell) |
| 1 | Registration: users, telegram_accounts, audit |
| 2 | AI Profile: profiles, photos, AI sessions |
| 2.3–2.4 | Moderation анкет (схема + WF_04) |
| 3 | Catalog: список, карточка, favorites |
| 4 | Anonymous chat: sessions, messages, block/report |
| 4.2 | Chat reliability: delivery queue, retries |
| 4.3 | AI message moderation |

### Ещё не в миграциях / WF (по ТЗ 05–13)

- Встречи (confirm, место, контакты по правилам)
- Отзывы как **флаги безопасности** (не рейтинг 1–5)
- Админ-панель, платежи, аналитика, полная автоматизация, launch checklist
- Полноценный WebApp UI (`webapp/src` пока заглушка)

---

## 5. Архитектура

```
Пользователь
    ↓
Telegram Bot / Telegram WebApp
    ↓  webhook / update
n8n  (оркестратор бизнес-логики)
    ├──→ PostgreSQL  (source of truth)
    ├──→ AI services (профиль, модерация)
    └──→ Telegram API (доставка, file_id)
```

**Правила данных:**

- `telegram_id` хранится **только** в `telegram_accounts`
- фото — только `telegram_file_id`, без бинарников в БД
- PK — UUID; timestamps — `TIMESTAMPTZ`
- секреты — только credentials / env, не в JSON workflow

---

## 6. Стек

| Слой | Технология |
|------|------------|
| Клиент | Telegram Bot API, Telegram WebApp |
| Оркестрация | n8n |
| БД | PostgreSQL 15 |
| Инфра | Docker, docker-compose |
| Миграции | SQL в `database/migrations/` |
| AI | внешний API из n8n |
| Документация | Markdown в `docs/` |

> Исторически в ранних ТЗ упоминались Google Sheets; **в текущем репо source of truth — PostgreSQL**.

---

## 7. Структура БД (текущие миграции)

| Файл | Назначение |
|------|------------|
| `001_users_and_telegram_accounts_schema.sql` | users, telegram_accounts |
| `001_initial_users_schema.sql` | **дубль** ранней 001 — не удалять без решения |
| `002_profiles_schema.sql` | profiles, photos, AI sessions, field history |
| `003_moderation_schema.sql` | модерация анкет |
| `004_catalog_schema.sql` | каталог / favorites |
| `005_chat_schema.sql` | чаты, сообщения |
| `006_chat_reliability_schema.sql` | delivery / reliability |
| `007_chat_message_moderation_schema.sql` | очередь модерации сообщений |

Доп. дизайн: `database/*.md` (DATABASE_DESIGN, PROFILE, CHAT, MODERATION, …).

**Проверить runtime:** наличие `audit_events` (упоминается в WF/AI_CONTEXT) — согласовать с миграциями.

---

## 8. n8n workflows

| Workflow | Папка | Назначение |
|----------|-------|------------|
| WF_01_USER_REGISTRATION | `auth/` **и** `registration/` | Регистрация (есть дубль) |
| WF_02_ROLE_SELECTION | `auth/` **и** `registration/` | Выбор роли (есть дубль) |
| WF_03_AI_PROFILE_AGENT | `profile/` | Диалог создания анкеты |
| WF_04_AI_MODERATION | `moderation/` | Модерация анкеты |
| WF_05_PROFILE_CATALOG | `catalog/` | Список анкет |
| WF_06_PROFILE_VIEW | `catalog/` | Карточка |
| WF_07_FAVORITES | `catalog/` | Избранное |
| WF_08_CREATE_CHAT_SESSION | `chat/` | Создание чата |
| WF_09_MESSAGE_ROUTER | `chat/` | Маршрутизация сообщений |
| WF_10_CHAT_BLOCK_REPORT | `chat/` | Блок / жалоба |
| WF_11_MESSAGE_DELIVERY_WORKER | `chat/` | Доставка / retries |
| WF_12_AI_MESSAGE_MODERATION | `chat/` | AI-модерация сообщений |

Каждый WF: `.json` (шаблон) + `.md` (описание). Credentials — placeholders.

---

## 9. Текущий статус

Источник правды по прогрессу: **`PROJECT_STATUS.md`** (актуальнее, чем `PROJECT_ROADMAP.md`).

- Этапы **0–4**: дизайн схем и workflow **завершён** в репозитории  
- E2E на живой БД / импорт в n8n: по `AI_CONTEXT.md` — **требует ручной валидации**  
- Этапы **5+** (встречи, safety flags, платежи…): **не начаты** в migrations/workflows  

---

## 10. Следующие шаги (приоритет)

1. Зафиксировать канонические пути WF_01/02 (auth vs registration) — без удаления до решения.  
2. Проверить/добавить согласованность `audit_events` с миграциями.  
3. Dev: поднять compose → применить миграции → smoke WF_01…03.  
4. Проектировать **meetings + safety flags** (вместо рейтинга 1–5).  
5. WebApp UI, admin path, payments — по ТЗ 07–10.  

---

## 11. С чего читать AI-агенту

1. Этот файл — `docs/PROJECT_CONTEXT.md`  
2. `docs/PROJECT_CONSISTENCY_REPORT.md`  
3. `AI_CONTEXT.md` + `PROJECT_STATUS.md`  
4. `docs/tz/` по порядку 00 → 13  
5. `docs/architecture/`  
6. `database/migrations/` + `n8n/workflows/`  

**Принцип:** анализ → архитектура → согласование → реализация → тестирование.
