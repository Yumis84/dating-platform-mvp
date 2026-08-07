# Документация Dating Platform MVP v1.0

Единая точка входа в документацию репозитория.

---

## Быстрый старт для AI / разработчика

1. [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) — **контекст проекта** (читать первым)  
2. [PROJECT_CONSISTENCY_REPORT.md](./PROJECT_CONSISTENCY_REPORT.md) — дубли и расхождения  
3. [../PROJECT_STATUS.md](../PROJECT_STATUS.md) — текущий прогресс  
4. [../AI_CONTEXT.md](../AI_CONTEXT.md) — handover snapshot для агентов  
5. [tz/README.md](./tz/README.md) — комплект ТЗ  
6. [docs/MIGRATION_MANIFEST.md](./MIGRATION_MANIFEST.md) — canonical migration order and reconciliation plan
7. [database/MIGRATION_POLICY.md](../database/MIGRATION_POLICY.md) — migration policy and safety rules
8. [docs/IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md) — developer pre-run checklist (Postgres, n8n, smoke)

---

## Индекс разделов

### Project Context

| Документ | Описание |
|----------|----------|
| [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) | Цель, роли, архитектура, стек, БД, WF, статус |
| [PROJECT_CONSISTENCY_REPORT.md](./PROJECT_CONSISTENCY_REPORT.md) | Аудит согласованности документации |
| [../PROJECT_STATUS.md](../PROJECT_STATUS.md) | Статусы этапов |
| [../PROJECT_ROADMAP.md](../PROJECT_ROADMAP.md) | Roadmap (⚠️ может отставать от STATUS) |
| [../PROJECT_DOCUMENTATION_INDEX.md](../PROJECT_DOCUMENTATION_INDEX.md) | Корневой индекс ТЗ/этапов |
| [../AI_CONTEXT.md](../AI_CONTEXT.md) | Подробный AI handover |
| [../FINAL_HANDOVER.md](../FINAL_HANDOVER.md) | Финальная передача |

### ТЗ (Technical Specifications)

| Путь | Содержание |
|------|------------|
| [tz/](./tz/) | Полный комплект 00_START … 13_MVP_LAUNCH |
| [tz/README.md](./tz/README.md) | Порядок изучения ТЗ |
| [tz/00_START/](./tz/00_START/) | README AI Agent, Development Rules |
| [tz/00_ARCHITECTURE/](./tz/00_ARCHITECTURE/) | Главное ТЗ, TASK_00, Architecture Plan |
| [tz/01_REGISTRATION/](./tz/01_REGISTRATION/) … [tz/13_MVP_LAUNCH/](./tz/13_MVP_LAUNCH/) | Модульные ТЗ |

### Architecture

| Путь | Содержание |
|------|------------|
| [architecture/](./architecture/) | Flows и обзоры |
| [architecture/README.md](./architecture/README.md) | Краткое введение |
| [architecture/MVP_ARCHITECTURE_REVIEW.md](./architecture/MVP_ARCHITECTURE_REVIEW.md) | Обзор архитектуры |
| [architecture/REGISTRATION_FLOW.md](./architecture/REGISTRATION_FLOW.md) | Регистрация |
| [architecture/AI_PROFILE_FLOW.md](./architecture/AI_PROFILE_FLOW.md) | AI-анкета |
| [architecture/AI_MODERATION_FLOW.md](./architecture/AI_MODERATION_FLOW.md) | Модерация анкет |
| [architecture/CATALOG_API_DESIGN.md](./architecture/CATALOG_API_DESIGN.md) | API каталога |
| [architecture/CHAT_*.md](./architecture/) | Чат, n8n, reliability, AI msg |

### Database

| Путь | Содержание |
|------|------------|
| [../database/README.md](../database/README.md) | Обзор БД |
| [../database/DATABASE_DESIGN.md](../database/DATABASE_DESIGN.md) | Дизайн |
| [../database/migrations/](../database/migrations/) | SQL миграции 001–007 |
| [../database/*_DESIGN.md](../database/) | Profile, Catalog, Chat, Moderation, … |

### n8n workflows

| Путь | Содержание |
|------|------------|
| [../n8n/README.md](../n8n/README.md) | Конвенции именования WF |
| [../n8n/workflows/](../n8n/workflows/) | JSON + MD по фичам |
| `auth/`, `registration/` | WF_01, WF_02 (см. consistency report — дубли) |
| `profile/` | WF_03 |
| `moderation/` | WF_04 |
| `catalog/` | WF_05–07 |
| `chat/` | WF_08–12 |

### Setup

| Путь | Содержание |
|------|------------|
| [setup/DEV_ENVIRONMENT_SETUP.md](./setup/DEV_ENVIRONMENT_SETUP.md) | Dev-окружение |
| [../infrastructure/](../infrastructure/) | docker-compose, env |
| [../docker/](../docker/) | Compose, nginx, checklist |
| [../.env.example](../.env.example) | Пример переменных |

### Testing

| Путь | Содержание |
|------|------------|
| [TEST_PLAN_MVP.md](./TEST_PLAN_MVP.md) | План тестирования MVP |
| [MIGRATION_AUDIT_REPORT.md](./MIGRATION_AUDIT_REPORT.md) | Аудит миграций |

### Rules & Operations

| Путь | Содержание |
|------|------------|
| [rules/](./rules/) | Правила разработки |
| [tz/00_START/DEVELOPMENT_RULES_AI_AGENT_v1.0.md](./tz/00_START/DEVELOPMENT_RULES_AI_AGENT_v1.0.md) | Правила AI Agent |

### Roadmap

| Документ | Примечание |
|----------|------------|
| [../PROJECT_STATUS.md](../PROJECT_STATUS.md) | **Предпочтительный** статус этапов |
| [../PROJECT_ROADMAP.md](../PROJECT_ROADMAP.md) | Устаревшие чеклисты — сверять со STATUS |

---

## Принцип работы

```
анализ → архитектура → согласование → реализация → тестирование
```

Не менять стек, порядок миграций, политику PII и контракты webhook без согласования.
