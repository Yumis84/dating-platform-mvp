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
- Статус: 🟨 DB design in progress
- Комментарии: Проектирование схемы для AI‑ассистента создания анкеты (profiles, profile_photos, profile_ai_sessions, profile_fields_history). Миграция 002_profiles_schema.sql подготовлена.
