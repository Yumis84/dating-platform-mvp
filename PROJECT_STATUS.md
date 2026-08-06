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
- Комментарии: Добавлены миграция 004_catalog_schema.sql, CATALOG_DESIGN.md, and n8n workflows WF_05_PROFILE_CATALOG, WF_06_PROFILE_VIEW, WF_07_FAVORITES (design + JSON templates).

## Этап 3.1 — Catalog completed
- Статус: 🟩 Completed
- Комментарии: Добавлены favorites endpoint (WF_07), pagination and filters for WF_05, and API design documentation.

## Этап 4 — Anonymous Chat
- Статус: 🟩 Chat architecture design completed
- Комментарии: Добавлены chat schema (005_chat_schema.sql), CHAT_DESIGN.md and CHAT_FLOW.md describing flows, blocking and reporting.

## Этап 4.1 — Chat n8n workflows
- Статус: 🟩 Chat n8n workflow design completed
- Комментарии: Добавлены templates for WF_08 (create session), WF_09 (message router), WF_10 (block/report) and CHAT_N8N_FLOW.md.

## Этап 4.2 — Chat reliability
- Статус: 🟩 Chat reliability architecture completed
- Комментарии: Добавлены delivery queue, rate limits, moderation events and a WF_11 worker design for reliable delivery and retries.
