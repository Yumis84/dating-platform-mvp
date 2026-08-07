# WF_01 Implementation Guide

Дата: 2026-08-07  
Статус: MVP Implementation Guide  
Назначение: Пошаговые инструкции для импорта и использования WF_01_USER_REGISTRATION в n8n.

---

## 1. Назначение WF_01

**WF_01_USER_REGISTRATION** — первый рабочий workflow Dating Platform MVP.

Функция:
- Принимает Telegram webhook с `/start` командой
- Создаёт нового пользователя в PostgreSQL
- Связывает Telegram аккаунт с пользователем
- Записывает событие регистрации в audit_events
- Возвращает приветственное сообщение

Архитектура:

```
Telegram user sends /start
        ↓
n8n Webhook Trigger
        ↓
Extract telegram_id, username from Telegram update
        ↓
PostgreSQL: INSERT INTO users (UUID)
        ↓
PostgreSQL: INSERT INTO telegram_accounts (telegram_id, username)
        ↓
PostgreSQL: INSERT INTO audit_events (event='user_registration')
        ↓
Return welcome message
```

Документация:
- Architecture: `docs/architecture/WF_01_ARCHITECTURE_DECISION.md`
- Dry-run script: `scripts/dry_run_migrations.sh`
- Smoke tests: `docs/WF_01_SMOKE_TEST.md`

---

## 2. Canonical Workflow Path

**Import source**: `n8n/workflows/auth/WF_01_USER_REGISTRATION.json`

**Do NOT use**: `n8n/workflows/registration/WF_01_USER_REGISTRATION.json` (legacy, out of scope for MVP)

### Why auth/ is canonical for MVP:

| Aspect | auth/ (MVP) | registration/ (Legacy) |
|--------|-----------|----------------------|
| Trigger | Webhook HTTP | Telegram Trigger |
| Nodes | 7 (minimal) | 10 (elaborate) |
| Scope | Registration only | Registration + role selection |
| User check | No (MVP limit) | Yes (existing user branch) |
| Role UI | No | Yes (out of scope) |
| MVP ready | ✅ YES | ⚠️ Overscoped |

---

## 3. Pre-requisites

### Database

✅ Migrations applied:

```bash
# Verify on your Postgres instance:

# 1. Check canonical 001 applied
psql -d your_database -c "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='users');"
# Expected: t

# 2. Check reconciliation 008 applied
psql -d your_database -c "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='audit_events');"
# Expected: t

# 3. Verify tables
psql -d your_database -c "\dt"
# Expected tables: users, telegram_accounts, audit_events
```

Run dry-run script to verify:

```bash
chmod +x scripts/dry_run_migrations.sh
./scripts/dry_run_migrations.sh
```

Expected output:
```
[PASS] All checks passed! Database is ready for WF_01
[PASS] Sample data insertion successful (WF_01 simulation)
```

### n8n Instance

✅ n8n running (v1.0+)  
✅ Access to n8n UI  
✅ Postgres node available in n8n  

### Telegram Bot

✅ Telegram bot created via @BotFather  
✅ Bot token (will use for Telegram credential in n8n)  
✅ Webhook domain configured (n8n accessible from Telegram servers)  

---

## 4. PostgreSQL Credential Setup in n8n

### Step 1: Get Database Connection Details

From your PostgreSQL instance:
- **Host**: localhost (or your Postgres server IP)
- **Port**: 5432 (default)
- **Database**: dating_platform_mvp (or your database name)
- **User**: your_db_user
- **Password**: your_db_password

Verify connection:

```bash
psql -h localhost -p 5432 -U your_db_user -d dating_platform_mvp -c "SELECT 1;"
```

### Step 2: Create Postgres Credential in n8n UI

1. Open n8n UI → **Credentials** (left sidebar)
2. Click **Create new** → **Postgres**
3. Fill in:
   - **Display name**: `PostgreSQL_MVP` (or memorable name)
   - **Host**: `localhost` (or your server IP)
   - **Port**: `5432`
   - **Database**: `dating_platform_mvp`
   - **User**: `your_db_user`
   - **Password**: `your_db_password`
   - **SSL**: Only if your Postgres requires SSL
4. Click **Test connection** → should show ✅ Success
5. Click **Save**

**Note the credential ID** (e.g., `pg_abc123def`) — you'll need it in the next step.

### Step 3: Import WF_01 and Bind Credential

When importing `n8n/workflows/auth/WF_01_USER_REGISTRATION.json`:

1. In n8n, go to **Workflows** → **Import from file**
2. Select `n8n/workflows/auth/WF_01_USER_REGISTRATION.json`
3. Click **Import**
4. The workflow will show **credential warnings** for `POSTGRES_PLACEHOLDER`
5. For each Postgres node (Create user, Create telegram_account, Create audit_event):
   - Click the node
   - In the **Credentials** field, select the PostgreSQL credential you just created
   - Save the node
6. Save the workflow

---

## 5. Telegram Bot Setup

### Step 1: Get Telegram Bot Token

If you don't have a bot token:

1. Open Telegram
2. Search for **@BotFather**
3. Send `/newbot`
4. Follow the wizard to create a bot
5. Copy the **HTTP API token** (e.g., `1234567890:ABCDefghIjklMnoPqrStUvWxyz...`)

### Step 2: Create Telegram Credential in n8n (if using Telegram node)

⚠️ **Note**: MVP WF_01 uses HTTP Webhook Trigger (not Telegram Trigger), so this is optional.

If you want to test Telegram messages:

1. n8n UI → **Credentials** → **Create new** → **Telegram**
2. **Display name**: `Telegram_Bot`
3. **Access token**: `1234567890:ABCDefghIjklMnoPqrStUvWxyz...`
4. Test connection
5. Save

### Step 3: Configure Telegram Webhook (for bot to reach n8n)

⚠️ **Prerequisite**: Your n8n instance must be accessible from the internet (has a public domain or IP).

After importing WF_01, you'll see the **Webhook Trigger** node. Copy its webhook URL:

In n8n UI:
1. Click the **Webhook Trigger** node
2. Copy the **Webhook URL** (e.g., `https://your-n8n-domain.com/webhook/user-registration`)

Configure Telegram bot to send updates to this URL:

```bash
# Use curl or Postman to set webhook
curl -X POST \
  https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \
  -d url=https://your-n8n-domain.com/webhook/user-registration
```

**For local development** (localhost):

Use a tunneling service like **ngrok**:

```bash
ngrok http 5678  # Assuming n8n runs on port 5678
# Output: https://abc123.ngrok.io

# Set webhook to ngrok URL
curl -X POST \
  https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \
  -d url=https://abc123.ngrok.io/webhook/user-registration
```

Verify webhook:

```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

Expected response:
```json
{
  "ok": true,
  "result": {
    "url": "https://your-n8n-domain.com/webhook/user-registration",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

---

## 6. Workflow Import Order

### 1. Verify Prerequisites

```bash
# 1. Database ready
./scripts/dry_run_migrations.sh

# 2. n8n running
curl http://localhost:5678/api/v1/status

# 3. Postgres credential created in n8n UI
# (manual step above)
```

### 2. Import Workflow

```bash
# Option A: Manual import via UI
1. Open n8n UI
2. Workflows → Import from file
3. Select: n8n/workflows/auth/WF_01_USER_REGISTRATION.json
4. Click Import

# Option B: Via n8n CLI (if available)
n8n workflow:import --input=n8n/workflows/auth/WF_01_USER_REGISTRATION.json
```

### 3. Configure Credentials

For each Postgres node in the workflow:
1. Click the node
2. **Credentials** field → select PostgreSQL_MVP (your credential)
3. Save the node

### 4. Activate Workflow (Optional for Testing)

⚠️ **For MVP testing**: Keep workflow **INACTIVE** until smoke tests pass.

To activate:
1. Workflow page → Click **Active** toggle (top-right)
2. Confirm activation

---

## 7. Smoke Test Scenario

See `docs/WF_01_SMOKE_TEST.md` for detailed smoke tests.

Quick test:

```bash
# 1. With workflow INACTIVE, manually test Postgres connection:
# Open any Postgres node in workflow → click Test

# 2. Then activate workflow
# 3. Send test Telegram update to webhook:

curl -X POST https://your-n8n-domain.com/webhook/user-registration \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": 123456789,
    "message": {
      "message_id": 1,
      "date": 1691234567,
      "chat": {"id": 987654321, "type": "private"},
      "from": {
        "id": 123456789,
        "is_bot": false,
        "first_name": "Test",
        "username": "test_user"
      },
      "text": "/start"
    }
  }'

# 4. Check Postgres for new rows:
psql -d dating_platform_mvp -c "SELECT * FROM users ORDER BY created_at DESC LIMIT 1;"
psql -d dating_platform_mvp -c "SELECT * FROM telegram_accounts ORDER BY created_at DESC LIMIT 1;"
psql -d dating_platform_mvp -c "SELECT * FROM audit_events WHERE event_type='user_registration' ORDER BY created_at DESC LIMIT 1;"
```

---

## 8. Known Limitations (MVP)

### Limitation #1: No Existing User Check

**Issue**: Calling `/start` twice with same Telegram ID will fail.

**Error**: `duplicate key value violates unique constraint "telegram_accounts_telegram_id_key"`

**Reason**: WF_01 MVP always creates a new user. It doesn't check if `telegram_id` already exists.

**Workaround**: For testing, use different `telegram_id` values (e.g., 123456789, 123456790, etc.)

**Post-MVP fix**: Add IF branch to check existing user (see `n8n/workflows/registration/WF_01_USER_REGISTRATION.json` for example)

### Limitation #2: No Role Selection

**Out of scope for WF_01 MVP**. Role selection will be handled by separate workflow WF_02 (future).

### Limitation #3: No Error Handling

**Issue**: If Postgres query fails, workflow execution will fail silently.

**No retry logic** or **error notifications** yet.

**Post-MVP fix**: Add error handling branches to workflow nodes.

### Limitation #4: No Idempotency

**Issue**: Same webhook payload will be processed multiple times if n8n retries.

**Telegram message duplicates** on network failures will create multiple `audit_events`.

**Post-MVP fix**: Add deduplication logic (Telegram `update_id` tracking).

---

## 9. Troubleshooting

### Issue: "Postgres credential not found"

**Solution**:
1. Verify credential created in n8n Credentials page
2. Click each Postgres node → re-select credential from dropdown
3. Save workflow

### Issue: "Connection refused" when testing Postgres

**Solution**:
1. Check Postgres is running: `psql -h localhost -p 5432 -U your_user -d your_db -c "SELECT 1;"`
2. Check n8n has correct host/port/credentials
3. If using Docker: ensure n8n container can reach Postgres (network configuration)

### Issue: Webhook URL is unreachable from Telegram

**Solution**:
1. For local development: use ngrok tunneling
2. For production: ensure firewall allows HTTPS (port 443)
3. Test webhook endpoint directly:
   ```bash
   curl -X POST https://your-domain.com/webhook/user-registration \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'
   ```

### Issue: Workflow executes but no data in Postgres

**Solution**:
1. Check workflow execution logs in n8n UI
2. Verify `event_data` in audit_events (should have event_type='user_registration')
3. Check Postgres for errors: `psql -d your_db -c "SELECT * FROM audit_events LIMIT 1;"`

### Issue: "telegram_id already exists" error

**This is Limitation #1 (MVP)**: Use different telegram_id for testing.

Post-MVP: WF_01 will include existing user check.

---

## 10. Related Documents

| Document | Purpose |
|----------|---------|
| `docs/architecture/WF_01_ARCHITECTURE_DECISION.md` | Architecture and design decisions |
| `docs/WF_01_SMOKE_TEST.md` | Smoke test scenarios with expected results |
| `database/migrations/001_users_and_telegram_accounts_schema.sql` | users/telegram_accounts schema |
| `database/migrations/008_audit_events_schema.sql` | audit_events schema |
| `scripts/dry_run_migrations.sh` | Database migration verification script |
| `docs/IMPLEMENTATION_CHECKLIST.md` | Pre-run dev environment checklist |

---

## 11. Next Steps After MVP

Post-MVP enhancements:
1. ✅ WF_02: Role Selection (separate workflow)
2. ✅ WF_03: AI Profile Agent (separate workflow)
3. ✅ Idempotency: Handle duplicate /start calls
4. ✅ Error handling: Add retry/error branches
5. ✅ User existence check: Before creating new users

---

**Document revision**: 2026-08-07  
**MVP status**: Ready for implementation
