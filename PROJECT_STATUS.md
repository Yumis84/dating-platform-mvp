# Project status — Dating Platform MVP

Текущий статус инфраструктуры и плана работ.

## Этап 0 — Infrastructure
- Статус: 🟩 Завершено
- Комментарии: Подготовлена базовая инфраструктура для разработки (docker-compose, n8n, Postgres, pgAdmin, Adminer, WebApp nginx) и соответствующая документация.

## Следующий этап
- Этап 1 — Registration
  - Описание: Реализация регистрации пользователей, первичных сущностей (профиль, связка с Telegram), валидация и поток регистрации.

## Прогресс по регистрации

- users schema: ✅
- telegram_accounts schema: ✅
- audit_events schema: ✅
- WF_01 registration design: ✅
- WF_02 role selection: ✅

## Этап 2 — AI Profile
- Статус: 🟩 Workflow design completed
- Комментарии: Дизайн WF_03_AI_PROFILE_AGENT готов. Миграция профилей подготовлена (002_profiles_schema.sql). Следующий шаг — реализация и тестирование в dev (импорт workflow, подготовка credentials, прогон миграции).

## Этап 2.3 — Moderation
- Статус: 🟩 Database design completed
- Комментарии: Добавлены таблицы profile_moderation, moderation_rules, moderation_history и дизайн модерации оформлен в database/MODERATION_DESIGN.md.

## Этап 2.4 — AI Moderation
- Статус: 🟩 AI Moderation workflow design completed
- Комментарии: Добавлен WF_04_AI_MODERATION design (n8n workflow template) and documentation for AI moderation flow.

## Этап 3 — Catalog
- Статус: 🟩 Catalog design completed
- Комментарии: Добавлены миграция 004_catalog_schema.sql, CATALOG_DESIGN.md, and n8n workflows WF_05_PROFILE_CATALOG and WF_06_PROFILE_VIEW (design + JSON templates).