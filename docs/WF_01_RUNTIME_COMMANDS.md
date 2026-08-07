# WF_01 Runtime Commands

Дата: 2026-08-07  
Статус: MVP Runtime Commands  
Назначение: Реальные команды для тестирования и проверки WF_01_USER_REGISTRATION.

---

## 1. Dry-Run Миграций

Перед импортом WF_01 убедитесь, что миграции готовы:

```bash
# Из корня репозитория
chmod +x scripts/dry_run_migrations.sh
./scripts/dry_run_migrations.sh
```

**Ожидаемый выход:**

```
========================================
Pre-flight Checks
========================================
[PASS] Docker is available
[PASS] Migrations directory found
[PASS] Found: 001_users_and_telegram_accounts_schema.sql
[PASS] Found: 002_profiles_schema.sql
...
[PASS] Found: 008_audit_events_schema.sql

========================================
Starting PostgreSQL Container
========================================
[INFO] Container started: dating-mvp-dryrun-XXXXXXX
[INFO] Waiting for PostgreSQL to be ready...
[PASS] PostgreSQL is ready

========================================
Applying Canonical Migrations
========================================
[INFO] [1/8] Applying 001_users_and_telegram_accounts_schema.sql...
[PASS] Applied 001_users_and_telegram_accounts_schema.sql
[INFO] [2/8] Applying 002_profiles_schema.sql...
[PASS] Applied 002_profiles_schema.sql
...
[INFO] [8/8] Applying 008_audit_events_schema.sql...
[PASS] Applied 008_audit_events_schema.sql

========================================
Verifying Tables
========================================
[PASS] Tables created: 21 (expected at least 20)
[PASS] Table found: users
[PASS] Table found: telegram_accounts
[PASS] Table found: audit_events
...

========================================
Smoke Test: Sample Data Insertion
========================================
[PASS] Sample data insertion successful (WF_01 simulation)

========================================
Dry-Run Summary
========================================
✓ PASSED: 25
✗ FAILED: 0

[PASS] All checks passed! Database is ready for WF_01
```

**Если сценарий успешен:**
- ✅ Все миграции применены
- ✅ Все таблицы созданы
- ✅ БД готова к WF_01

---

## 2. Проверка статуса n8n

Убедитесь, что n8n запущен и доступен:

```bash
# Проверить статус
curl -s http://localhost:5678/api/v1/status | jq .
```

**Ожидаемый ответ:**

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

**Если используется Docker:**

```bash
# Проверить контейнер
docker ps | grep dating_n8n
# Ожидаемо: контейнер должен быть в статусе "Up"

# Проверить логи
docker logs dating_n8n | tail -20
```

---

## 3. Проверка подключения к PostgreSQL

Из n8n UI:

1. Откройте **Credentials**
2. Нажмите на `PostgreSQL_MVP` (или ваше имя credential'а)
3. Нажмите **Test connection**
4. Должно появиться ✅ **Connection successful**

**Или через CLI:**

```bash
# Проверить прямое подключение к БД
psql -h localhost -p 5432 -U your_db_user -d dating_platform_mvp -c "SELECT 1;"
# Ожидаемо: 1
```

---

## 4. Импорт и Активация WF_01

### Импорт:

Из n8n UI:
1. **Workflows** → **Import from file**
2. Выберите `n8n/workflows/auth/WF_01_USER_REGISTRATION.json`
3. Нажмите **Import**

### Проверка импорта:

```bash
# Проверить, что workflow импортирован (если доступно API)
curl -s http://localhost:5678/api/v1/workflows | jq '.[] | select(.name=="WF_01_USER_REGISTRATION")'
```

### Привязка Postgres credential'а:

Для каждого Postgres node (Create user, Create telegram_account, Create audit_event):
1. Нажмите на node
2. В правой панели выберите **PostgreSQL_MVP** из dropdown
3. Нажмите **Save**

### Активация workflow:

1. В workflow нажмите **Active** toggle (top-right)
2. Нажмите **Confirm**
3. Workflow статус изменится на 🟢 **ACTIVE**

---

## 5. Получить Webhook URL

Из n8n UI:

1. Откройте workflow **WF_01_USER_REGISTRATION**
2. Нажмите на **Webhook Trigger** node
3. Скопируйте **Webhook URL** из правой панели

**Пример:**

```
http://localhost:5678/webhook/user-registration
```

**Для production (ngrok для локальной разработки):**

```bash
ngrok http 5678
# Output:
# Forwarding                    https://abc123.ngrok.io -> http://localhost:5678
```

Production webhook URL:
```
https://abc123.ngrok.io/webhook/user-registration
```

---

## 6. Тестовый Webhook Call (curl)

### Подготовка:

Сохраните webhook URL в переменную:

```bash
export WEBHOOK_URL="http://localhost:5678/webhook/user-registration"
# Или для ngrok:
# export WEBHOOK_URL="https://abc123.ngrok.io/webhook/user-registration"
```

### Простой тест:

```bash
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
HTTP/1.1 200 OK
Content-Type: application/json

{
  "text": "Welcome! Registration complete. Please choose your role (MAN or WOMAN) using the role selection UI."
}
```

### Множественные тесты:

Для тестирования с разными telegram_id:

```bash
for i in {1..5}; do
  TELEGRAM_ID=$((123456789 + i))
  USERNAME="test_user_$i"
  
  echo "Test $i: telegram_id=$TELEGRAM_ID, username=$USERNAME"
  
  curl -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d "{
      \"update_id\": $i,
      \"message\": {
        \"message_id\": $i,
        \"date\": 1691234567,
        \"chat\": {\"id\": 987654321, \"type\": \"private\"},
        \"from\": {
          \"id\": $TELEGRAM_ID,
          \"is_bot\": false,
          \"first_name\": \"Test\",
          \"username\": \"$USERNAME\"
        },
        \"text\": \"/start\"
      }
    }" && echo "\n✓ Test $i passed\n" || echo "\n✗ Test $i failed\n"
  
  sleep 1
done
```

### Проверка в n8n UI:

После webhook call:

1. Откройте workflow **WF_01_USER_REGISTRATION**
2. Проверьте **Execution history**
3. Должно быть видно выполнение с всеми nodes зелёными (✅)
4. Нажмите на execution → **Logs** для деталей

---

## 7. SQL Проверки после Webhook

После каждого webhook call проверьте БД:

### Проверка 1: users table

```bash
psql -d dating_platform_mvp -c "
  SELECT 
    id, 
    role, 
    created_at, 
    updated_at 
  FROM users 
  ORDER BY created_at DESC 
  LIMIT 5;
"
```

**Ожидаемо:**
```
                   id                   | role |            created_at            |            updated_at            
----------------------------------------+------+----------------------------------+----------------------------------
 a1b2c3d4-e5f6-7890-ab12-cdef34567890 | NULL | 2026-08-07 19:30:45.123456+00   | 2026-08-07 19:30:45.123456+00
```

### Проверка 2: telegram_accounts table

```bash
psql -d dating_platform_mvp -c "
  SELECT 
    id, 
    user_id, 
    telegram_id, 
    username, 
    created_at 
  FROM telegram_accounts 
  ORDER BY created_at DESC 
  LIMIT 5;
"
```

**Ожидаемо:**
```
                   id                   |              user_id             | telegram_id | username  |            created_at            
----------------------------------------+----------------------------------+-------------+-----------+----------------------------------
 b2c3d4e5-f6a7-8901-bc23-def456789abc | a1b2c3d4-e5f6-7890-ab12-cdef... | 123456789   | test_user | 2026-08-07 19:30:45.234567+00
```

### Проверка 3: audit_events table

```bash
psql -d dating_platform_mvp -c "
  SELECT 
    id, 
    user_id, 
    event_type, 
    event_data, 
    created_at 
  FROM audit_events 
  WHERE event_type = 'user_registration'
  ORDER BY created_at DESC 
  LIMIT 5;
"
```

**Ожидаемо:**
```
                   id                   |              user_id             |   event_type    |       event_data       |            created_at            
----------------------------------------+----------------------------------+-----------------+------------------------+----------------------------------
 c3d4e5f6-a7b8-9012-cd34-ef5678901234 | a1b2c3d4-e5f6-7890-ab12-cdef... | user_registration | {"source": "telegram"} | 2026-08-07 19:30:45.345678+00
```

### Комбинированная проверка (все таблицы за один запрос):

```bash
psql -d dating_platform_mvp << EOF
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'telegram_accounts' as table_name, COUNT(*) as count FROM telegram_accounts
UNION ALL
SELECT 'audit_events' as table_name, COUNT(*) as count FROM audit_events;
EOF
```

**Ожидаемо:**
```
      table_name      | count 
---------------------+-------
 users               |     5
 telegram_accounts   |     5
 audit_events        |     5
```

---

## 8. Очистка тестовых данных

Если нужно очистить БД для переноса тестирования:

⚠️ **ОСТОРОЖНО: это удалит все данные!**

```bash
# Очистить все данные из таблиц (сохранить схему)
psql -d dating_platform_mvp << EOF
DELETE FROM audit_events;
DELETE FROM telegram_accounts;
DELETE FROM users;
EOF
```

**Проверка после очистки:**

```bash
psql -d dating_platform_mvp << EOF
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'telegram_accounts' as table_name, COUNT(*) as count FROM telegram_accounts
UNION ALL
SELECT 'audit_events' as table_name, COUNT(*) as count FROM audit_events;
EOF
```

**Ожидаемо:**
```
      table_name      | count 
---------------------+-------
 users               |     0
 telegram_accounts   |     0
 audit_events        |     0
```

---

## 9. Проверка Workflow Logs в n8n

После каждого webhook call проверьте logs:

### Через n8n UI:

1. Откройте **WF_01_USER_REGISTRATION** workflow
2. Проверьте **Execution history** (внизу экрана)
3. Нажмите на последнее выполнение
4. Проверьте, что все nodes имеют статус ✅
5. Откройте каждый node для просмотра input/output:
   - **Webhook Trigger**: должен содержать parsed Telegram payload
   - **Extract input**: должен содержать извлечённые telegram_id и username
   - **Create user**: должен вернуть new user UUID
   - **Create telegram_account**: должен вернуть new telegram_account UUID
   - **Create audit_event**: должен вернуть new audit_event UUID

### Если какой-то node красный (❌):

1. Нажмите на node
2. Проверьте **Error** tab
3. Диагностируйте ошибку:
   - Если SQL ошибка: проверьте миграции и данные
   - Если credential ошибка: проверьте PostgreSQL credential в Credentials
   - Если expression ошибка: проверьте данные из webhook

---

## 10. Полный Smoke Test Сценарий

Полный прогон тестирования WF_01:

```bash
#!/bin/bash
# Run complete WF_01 smoke test

set -e

echo "=== WF_01 Smoke Test ==="
echo ""

# Step 1: Dry-run migrations
echo "Step 1: Running dry-run migrations..."
./scripts/dry_run_migrations.sh > /dev/null 2>&1
echo "✓ Migrations OK"
echo ""

# Step 2: Check n8n status
echo "Step 2: Checking n8n status..."
RESPONSE=$(curl -s http://localhost:5678/api/v1/status)
if echo "$RESPONSE" | grep -q "ok"; then
  echo "✓ n8n is running"
else
  echo "✗ n8n is not responding"
  exit 1
fi
echo ""

# Step 3: Get webhook URL
echo "Step 3: Getting webhook URL..."
WEBHOOK_URL="http://localhost:5678/webhook/user-registration"
echo "✓ Webhook URL: $WEBHOOK_URL"
echo ""

# Step 4: Send test payload
echo "Step 4: Sending test webhook payload..."
RESPONSE=$(curl -s -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": 9999,
    "message": {
      "message_id": 1,
      "date": 1691234567,
      "chat": {"id": 987654321, "type": "private"},
      "from": {
        "id": 999999999,
        "is_bot": false,
        "first_name": "Test",
        "username": "smoke_test_user"
      },
      "text": "/start"
    }
  }')

if echo "$RESPONSE" | grep -q "Welcome"; then
  echo "✓ Webhook executed successfully"
else
  echo "✗ Webhook response error:"
  echo "$RESPONSE"
  exit 1
fi
echo ""

# Step 5: Verify database
echo "Step 5: Verifying database..."
USERS_COUNT=$(psql -d dating_platform_mvp -t -c "SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '5 minutes';")
ACCOUNTS_COUNT=$(psql -d dating_platform_mvp -t -c "SELECT COUNT(*) FROM telegram_accounts WHERE created_at > NOW() - INTERVAL '5 minutes';")
AUDIT_COUNT=$(psql -d dating_platform_mvp -t -c "SELECT COUNT(*) FROM audit_events WHERE created_at > NOW() - INTERVAL '5 minutes' AND event_type = 'user_registration';")

echo "✓ users created (last 5 min): $USERS_COUNT"
echo "✓ telegram_accounts created (last 5 min): $ACCOUNTS_COUNT"
echo "✓ audit_events created (last 5 min): $AUDIT_COUNT"

if [ "$USERS_COUNT" -gt 0 ] && [ "$ACCOUNTS_COUNT" -gt 0 ] && [ "$AUDIT_COUNT" -gt 0 ]; then
  echo ""
  echo "=== ✓ WF_01 SMOKE TEST PASSED ==="
  exit 0
else
  echo ""
  echo "=== ✗ WF_01 SMOKE TEST FAILED ==="
  exit 1
fi
```

**Сохранить в файл и запустить:**

```bash
chmod +x smoke_test_wf01.sh
./smoke_test_wf01.sh
```

---

## 11. Разбиение на Troubleshooting

### Workflow не выполняется

**Проверки:**

1. Workflow активен ли?
   ```bash
   # Откройте n8n UI → WF_01_USER_REGISTRATION → должна быть зелёная кнопка "Active"
   ```

2. Webhook URL доступен ли?
   ```bash
   curl -I "$WEBHOOK_URL"
   # Ожидаемо: 200 OK или 404 (но не Connection refused)
   ```

3. n8n логи:
   ```bash
   docker logs dating_n8n | grep -i "webhook\|error" | tail -20
   ```

### Workflow выполняется, но нет данных в БД

**Проверки:**

1. Postgresql credential проверен ли?
   ```bash
   # n8n UI → Credentials → PostgreSQL_MVP → Test connection
   ```

2. SQL query работает ли?
   ```bash
   # Откройте Create user node → проверьте SQL query
   # Убедитесь, что миграция 001 применена:
   psql -d dating_platform_mvp -c "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='users');"
   # Ожидаемо: t
   ```

3. Workflow logs:
   ```bash
   # n8n UI → WF_01_USER_REGISTRATION → Execution history
   # → нажмите на последнее выполнение → проверьте каждый node
   ```

---

## 12. Документы и Ссылки

| Документ | Цель |
|----------|------|
| `docs/WF_01_N8N_SETUP.md` | Подробная инструкция по импорту |
| `docs/WF_01_IMPLEMENTATION_GUIDE.md` | Полное руководство по реализации |
| `docs/WF_01_SMOKE_TEST.md` | Детальные сценарии тестирования |
| `scripts/dry_run_migrations.sh` | Скрипт проверки миграций |
| `database/migrations/001_users_and_telegram_accounts_schema.sql` | Schema users и telegram_accounts |
| `database/migrations/008_audit_events_schema.sql` | Schema audit_events |
| `n8n/workflows/auth/WF_01_USER_REGISTRATION.json` | Canonical workflow JSON |

---

**Document revision**: 2026-08-07  
**Status**: Ready for runtime testing