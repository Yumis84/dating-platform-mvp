# PROJECT_CONSISTENCY_REPORT

Дата: 2026-08-07  
Репозиторий: `Yumis84/dating-platform-mvp`  
Тип: документационный аудит (код / SQL / JSON workflow **не изменялись**)

---

## 1. Найденные дубли

### 1.1. Миграции

| Файлы | Проблема |
|-------|----------|
| `database/migrations/001_initial_users_schema.sql` | Ранний/альтернативный 001 |
| `database/migrations/001_users_and_telegram_accounts_schema.sql` | Актуальный 001 по смыслу AI_CONTEXT |

**Риск:** неоднозначный порядок применения на чистой БД.  
**Рекомендация:** пометить канонический файл в README миграций; не удалять второй без решения (по правилам PR — только docs).

### 1.2. n8n workflows

| Workflow | Пути |
|----------|------|
| WF_01_USER_REGISTRATION | `n8n/workflows/auth/` **и** `n8n/workflows/registration/` |
| WF_02_ROLE_SELECTION | `n8n/workflows/auth/` **и** `n8n/workflows/registration/` |

Размеры JSON различаются (auth vs registration) — не идентичные копии.  
**Рекомендация:** выбрать одну каноническую папку (`registration/` или `auth/`), вторую пометить deprecated в MD.

### 1.3. Индексы документации

| Файл | Роль |
|------|------|
| `docs/README.md` | Индекс docs (обновляется этим PR) |
| `PROJECT_DOCUMENTATION_INDEX.md` (корень) | Статусы + порядок ТЗ |
| `docs/PROJECT_DOCUMENTATION_INDEX.md` | Ещё один индекс в docs |
| `docs/tz/README.md` | Индекс только ТЗ |

**Риск:** три «главных» входа.  
**Рекомендация:** единая точка — `docs/README.md` → PROJECT_CONTEXT; корневой INDEX оставить как краткий status mirror.

---

## 2. Расхождения документов

| Тема | Источник A | Источник B | Расхождение |
|------|------------|------------|-------------|
| Прогресс Этап 1 | `PROJECT_STATUS.md` — схемы/WF design ✅ | `PROJECT_ROADMAP.md` — «В работе», чеклисты пустые | Roadmap **устарел** |
| БД MVP | Ранние ТЗ / architecture README: Google Sheets | Repo: PostgreSQL + migrations | Sheets — legacy в тексте architecture/README |
| audit_events | WF + AI_CONTEXT + Documentation Index — есть | Явная миграция в списке 001–007 | **Не подтверждена** в файлах migrations |
| «Этап 1 Registration» | Documentation Index: текущая стадия | STATUS: этапы 2–4 design уже done | Index частично отстаёт по формулировке «текущая стадия» |
| Рейтинг 1–5 | TZ_06 в docs/tz | Продуктовое решение: safety flags | Нужна явная пометка в TZ_06 / CONTEXT |
| architecture/README | «PostgreSQL проектируется, БД пока не создаётся» | migrations 001–007 уже в repo | Текст architecture README **устарел** |

---

## 3. Устаревшие или слабые файлы

| Файл | Комментарий |
|------|-------------|
| `PROJECT_ROADMAP.md` | Не отражает catalog/chat; чеклисты Этапа 1 не синхронизированы |
| `docs/architecture/README.md` | Упоминает Sheets и «БД пока не создаётся» |
| `webapp/src/README.md` | Заглушка — ожидаемо до TZ_09 UI |
| Краткие TZ_*.md в `docs/tz/` | Часто короче полных DOCX из Drive; для детальной реализации сверять Drive/архив |

---

## 4. Что согласовано хорошо

- Наличие `docs/tz/00…13` с порядком разработки  
- `PROJECT_STATUS.md` детально описывает этапы 0–4.3  
- `AI_CONTEXT.md` — сильный handover для следующего агента  
- Именование WF_01…12 единообразное  
- Конвенции UUID / TIMESTAMPTZ / file_id задокументированы  

---

## 5. Рекомендации (без выполнения в этом PR)

1. **Канон статуса:** `PROJECT_STATUS.md` > Roadmap; обновить Roadmap или пометить deprecated.  
2. **Канон контекста:** `docs/PROJECT_CONTEXT.md` (этот PR).  
3. **Миграции:** в `database/migrations/README.md` указать, какой `001_*` применять.  
4. **WF:** канон WF_01/02 в одной папке; во второй — ссылка «see registration/».  
5. **audit_events:** добавить миграцию или убрать запись из WF до согласования.  
6. **architecture/README:** убрать Sheets как primary storage; отразить Postgres.  
7. **TZ_06:** зафиксировать модель safety flags vs звёзды.  
8. **Не удалять** дубли SQL/JSON до отдельного cleanup-PR с тестами migrate.

---

## 6. Объём этого PR

| Действие | Файлы |
|----------|--------|
| Создан | `docs/PROJECT_CONTEXT.md` |
| Обновлён | `docs/README.md` |
| Создан | `docs/PROJECT_CONSISTENCY_REPORT.md` |
| Не трогалось | `database/**`, `n8n/**/*.json`, `webapp/**`, docker/infra код |

---

## 7. Следующий документационный шаг (опционально)

- Синхронизировать `PROJECT_ROADMAP.md` со STATUS  
- Патч `docs/architecture/README.md` (только текст)  
- Краткие «canonical path» заметки в `n8n/workflows/README.md`
