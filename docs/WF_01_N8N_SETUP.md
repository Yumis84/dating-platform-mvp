# WF_01 n8n Setup Guide

Дата: 2026-08-07  
Статус: MVP Import Guide  
Назначение: Пошаговые инструкции для подготовки n8n к импорту и запуску WF_01_USER_REGISTRATION.

---

## 1. Требования перед импортом

### PostgreSQL

✅ **Миграции применены:**

Убедитесь, что canonical миграции применены на целевой БД:

```bash
# Проверка 1: users table exists
psql -h localhost -p 5432 -U your_db_user -d dating_platform_mvp -c \
  "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='users');"
# Expected: t

# Проверка 2: telegram_accounts table exists
psql -h localhost -p 5432 -U your_db_user -d dating_platform_mvp -c \
  "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='telegram_accounts');"
# Expected: t

# Проверка 3: audit_events table exists (миграция 008)
psql -h localhost -p 5432 -U your_db_user -d dating_platform_mvp -c \
  "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='audit_events');"
# Expected: t
```

**Или запустить dry-run скрипт:**

```bash
chmod +x scripts/dry_run_migrations.sh
./scripts/dry_run_migrations.sh
```

### n8n Instance

✅ **n8n запущен и доступен:**

```bash
# Проверка статуса
curl http://localhost:5678/api/v1/status
# Expected: 200 OK response with status info
```

### Webhook Access

✅ **n8n accessible from external callers** (для Telegram webhook):

- Для **локальной разработки**: используйте ngrok
- Для **production**: используйте domain name

---

## 2. PostgreSQL Credential Setup в n8n

### Шаг 1: Получить Connection Details

Из вашей PostgreSQL инстанции:

```bash
# Пример для docker-compose setup
cat .env | grep POSTGRES
```

**Параметры:**
- **Host**: `localhost` (или ваш server IP)
- **Port**: `5432` (default)
- **Database**: `dating_platform_mvp` (или ваше имя БД)
- **User**: `your_db_user`
- **Password**: `your_db_password`

**Проверка соединения:**

```bash
psql -h localhost -p 5432 -U your_db_user -d dating_platform_mvp -c "SELECT 1;"
# Expected: 1
```

### Шаг 2: Создать PostgreSQL Credential в n8n UI

1. Откройте n8n UI: `http://localhost:5678`

2. В левом sidebar нажмите **Credentials** (иконка ключа)

3. Нажмите **Create new** → **PostgreSQL**

4. Заполните форму:

| Поле | Значение | Пример |
|------|---------|--------|
| **Display name** | Запоминающееся имя | `PostgreSQL_MVP` или `dating_platform` |
| **Host** | Адрес Postgres сервера | `localhost` или `postgres` (если в Docker) |
| **Port** | Порт (обычно 5432) | `5432` |
| **Database** | Имя базы данных | `dating_platform_mvp` |
| **User** | Пользователь БД | `postgres` или `mvp_user` |
| **Password** | Пароль пользователя | `your_secure_password` |
| **SSL** | Only if required | Обычно `Disable` для dev |

5. Нажмите **Test connection** (должен показать ✅ Success)

6. Нажмите **Save**

### Шаг 3: Запомнить Credential ID

После сохранения n8n выдаст ID credential (например: `pg_abc123def456`).

**Вариант A:** Это будет видно в URL:
```
http://localhost:5678/credentials/edit/pg_abc123def456
```

**Вариант B:** В списке Credentials будет показано имя `PostgreSQL_MVP`.

---

## 3. Импорт WF_01 Workflow

### Вариант A: Импорт через UI (Рекомендуется)

1. В n8n откройте **Workflows** (левый sidebar)

2. Нажмите **Import from file**

3. Выберите файл: `n8n/workflows/auth/WF_01_USER_REGISTRATION.json`

4. Нажмите **Import**

5. Workflow появится в списке с именем **WF_01_USER_REGISTRATION** (статус: INACTIVE)

### Вариант B: Импорт через CLI (если доступно)

```bash
n8n workflow:import --input=n8n/workflows/auth/WF_01_USER_REGISTRATION.json
```

---

## 4. Привязка PostgreSQL Credential к Nodes

После импорта workflow будет содержать placeholder credentials. Нужно их заменить:

### Шаг 1: Откройте WF_01_USER_REGISTRATION Workflow

В n8n UI нажмите на workflow в списке.

### Шаг 2: Для каждого PostgreSQL Node:

Workflow содержит **3 PostgreSQL node'а**:
1. **Create user**
2. **Create telegram_account**
3. **Create audit_event**

Для каждого:

1. Нажмите на node на canvas
2. В правой панели найдите **Credentials** dropdown
3. Выберите `PostgreSQL_MVP` (credential, который вы создали на Шаге 2)
4. Сохраните node (нажав где-то вне node'а или Ctrl+S)

**Визуально:**

```
[Workflow Canvas]
  ┌─────────────────────┐
  │  Create user node   │ ← Нажмите
  └─────────────────────┘
         ↓
  [Right Panel: Credentials]
  ┌─────────────────────┐
  │ PostgreSQL: ▼       │ ← Dropdown
  │   PostgreSQL_MVP    │ ← Выберите это
  │   (Test connection) │
  └─────────────────────┘
```

Повторите для **Create telegram_account** и **Create audit_event** nodes.

### Шаг 3: Сохраните Workflow

Нажмите **Save** (или Ctrl+S).

---

## 5. Настройка Webhook URL

### Шаг 1: Найти Webhook URL

1. В workflow нажмите на **Webhook Trigger** node

2. В правой панели скопируйте **Webhook URL**

Пример:
```
http://localhost:5678/webhook/user-registration
```

Для **production** это будет:
```
https://your-n8n-domain.com/webhook/user-registration
```

### Шаг 2: Для локальной разработки (localhost)

Используйте **ngrok** для tunneling:

```bash
# Установить ngrok (если не установлено)
# https://ngrok.com/download

# Запустить tunnel на порт 5678
ngrok http 5678

# Output:
# Forwarding                    https://abc123.ngrok.io -> http://localhost:5678
```

Итоговый webhook URL для тестирования:
```
https://abc123.ngrok.io/webhook/user-registration
```

### Шаг 3: Настроить Telegram Webhook (если используется Telegram bot)

⚠️ **Для MVP:** WF_01 не требует активного Telegram webhook. Вы можете тестировать через curl.

Если нужно привязать к реальному Telegram боту:

```bash
curl -X POST \
  https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \
  -d url=https://abc123.ngrok.io/webhook/user-registration
```

Проверить:

```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

---

## 6. Активация Workflow

⚠️ **Важно:** Перед активацией убедитесь, что:
- ✅ Все 3 PostgreSQL nodes имеют привязанный credential
- ✅ Webhook URL доступен (или используется локальная разработка)
- ✅ БД содержит миграции 001 и 008

### Активировать:

1. В workflow нажмите **Active** toggle (top-right corner)

2. Нажмите **Confirm activation**

Workflow перейдёт в состояние **ACTIVE** и будет слушать на webhook URL.

---

## 7. Проверка перед запуском

### Чеклист:

```
☐ PostgreSQL credential создан и проверен (Test connection: ✅)
☐ WF_01 workflow импортирован
☐ Все 3 Postgres nodes привязаны к credential
☐ Webhook URL скопирован и доступен
☐ Workflow в режиме INACTIVE (для первого теста)
☐ Dry-run миграции выполнен успешно (./scripts/dry_run_migrations.sh)
☐ БД содержит таблицы: users, telegram_accounts, audit_events
```

---

## 8. Тестовый Webhook Call (curl)

**Запустить после активации workflow:**

```bash
# Замените WEBHOOK_URL на реальный
WEBHOOK_URL="http://localhost:5678/webhook/user-registration"

curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": 1001,
    "message": {
      "message_id": 1,
      "date": 1691234567,
      "chat": {
        "id": 987654321,
        "type": "private"
      },
      "from": {
        "id": 123456789,
        "is_bot": false,
        "first_name": "Test",
        "username": "test_user"
      },
      "text": "/start"
    }
  }'
```

**Ожидаемый ответ:**

```
HTTP 200 OK
{
  "text": "Welcome! Registration complete. Please choose your role (MAN or WOMAN) using the role selection UI."
}
```

### Проверка в n8n UI:

1. Откройте workflow
2. Нажмите на Webhook Trigger node → **Logs** tab
3. Должно быть видно выполнение workflow
4. Все nodes должны быть зелёными (✅)

---

## 9. Проверка данных в БД

После успешного webhook call проверьте БД:

### users table:

```bash
psql -d dating_platform_mvp -c "
  SELECT id, role, created_at, updated_at 
  FROM users 
  ORDER BY created_at DESC 
  LIMIT 1;
"
```

**Ожидаемо:**
- 1 новая строка с UUID
- role = NULL
- created_at и updated_at содержат текущий timestamp

### telegram_accounts table:

```bash
psql -d dating_platform_mvp -c "
  SELECT id, user_id, telegram_id, username, created_at 
  FROM telegram_accounts 
  WHERE telegram_id = 123456789 
  ORDER BY created_at DESC 
  LIMIT 1;
"
```

**Ожидаемо:**
- 1 новая строка
- telegram_id = 123456789 (из webhook)
- username = 'test_user' (из webhook)
- user_id связан с user из таблицы users

### audit_events table:

```bash
psql -d dating_platform_mvp -c "
  SELECT id, user_id, event_type, event_data, created_at 
  FROM audit_events 
  WHERE event_type = 'user_registration' 
  ORDER BY created_at DESC 
  LIMIT 1;
"
```

**Ожидаемо:**
- 1 новая строка
- event_type = 'user_registration'
- event_data содержит JSON: {\"source\": \"telegram\"}
- user_id связан с user из таблицы users

---

## 10. Troubleshooting

### Issue: "Postgres credential not found"

**Решение:**
1. Вернитесь в Credentials
2. Убедитесь, что credential создан
3. В workflow повторно выберите credential для каждого node

### Issue: "Connection refused" при тестировании credential

**Решение:**
1. Проверьте, что Postgres запущен: `pg_isready -h localhost -p 5432`
2. Проверьте параметры соединения (host, port, database, user, password)
3. Если используете Docker: убедитесь, что n8n контейнер может reach Postgres контейнер

### Issue: "relation users does not exist"

**Решение:**
1. Миграции не применены
2. Запустите dry-run: `./scripts/dry_run_migrations.sh`
3. Проверьте, что миграции 001 и 008 были выполнены

### Issue: Webhook call не вызывает workflow

**Решение:**
1. Убедитесь, что workflow в режиме ACTIVE
2. Проверьте webhook URL (скопируйте из n8n UI)
3. Убедитесь, что URL доступен (для ngrok проверьте, что tunnel активен)
4. Проверьте n8n logs: `docker logs dating_n8n` (если используется Docker)

### Issue: Workflow выполнен, но данные не в БД

**Решение:**
1. Проверьте n8n execution logs (Workflow → Logs tab)
2. Убедитесь, что PostgreSQL node не имеет ошибок
3. Проверьте SQL query в каждом node (должны быть видны в logs)
4. Убедитесь, что credential привязан к каждому Postgres node

---

## 11. Следующие шаги

После успешного первого импорта и тестирования WF_01:

1. ✅ Verify smoke test прошел успешно
2. → Запустить полный test suite (если будет)
3. → Приступить к WF_02 (Role Selection)

---

**Document revision**: 2026-08-07  
**Status**: Ready for import