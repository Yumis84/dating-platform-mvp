# Dating Platform MVP v1.0 Documentation Index

## Источник истины

Главный документ:

docs/tz/00_ARCHITECTURE/00_Glavnoe_TZ_Arhitektura_platformy_znakomstv_MVP_v1.0

Все изменения архитектуры должны сначала согласовываться с главным ТЗ.

## Порядок разработки

START
↓
00 Architecture
↓
TZ_01 Registration
↓
TZ_02 AI Profile
↓
TZ_03 Catalog
↓
TZ_04 Anonymous Chat
↓
TZ_05 Meetings
↓
TZ_06 Reviews and Reputation
↓
TZ_07 Admin Panel
↓
TZ_08 AI Security
↓
TZ_09 Telegram WebApp
↓
TZ_10 Payments
↓
TZ_11 Analytics
↓
TZ_12 Automation
↓
TZ_13 MVP Launch

## Правила AI Agent

Перед разработкой любого модуля:

1. Изучить соответствующий TZ документ.
2. Проверить архитектуру.
3. Не менять стек без согласования.
4. Не создавать лишний функционал.
5. Все секреты хранить только в credentials.
6. Все изменения делать через Git commit.

## Текущая стадия

Этап 1 Registration

Выполнено:

✅ users schema
✅ telegram_accounts schema
✅ audit_events schema
✅ WF_01 registration design

Следующий шаг:

WF_02 role selection


### Архитектура-папка

Главное ТЗ и связанная архитектурная документация расположены в:

- docs/tz/00_ARCHITECTURE/

Пожалуйста, обновляйте индекс при добавлении файлов в эту папку.
