# WF_01 n8n Import Checklist

Дата: 2026-08-07  
Статус: Pre-Import Preparation  
Назначение: Пошаговая проверка перед импортом WF_01 в n8n.

---

## Pre-Import Verification

### 1. Environment Setup

- [ ] PostgreSQL running with migrations 001 + 008 applied
- [ ] n8n instance running (v1.0+)
- [ ] n8n accessible via HTTPS (for Telegram webhook)
- [ ] Network connectivity: n8n ↔ PostgreSQL
- [ ] Telegram bot created via @BotFather
- [ ] Telegram bot token available (will use for future enhancements)

Verification:
```bash
# Check Postgres
psql -h localhost -p 5432 -U your_user -d dating_platform_mvp -c "SELECT 1;"
# Expected: 1

# Check n8n
curl http://localhost:5678/api/v1/status
# Expected: {"status":"ok"}

# Check migrations applied
psql -d dating_platform_mvp -c "\dt users telegram_accounts audit_events"
# Expected: All 3 tables exist
```

### 2. Credential Creation in n8n

#### Step 1: PostgreSQL Credential

1. Open n8n UI → **Credentials** (left sidebar)
2. Click **+ Create new** → **Postgres**
3. Fill in connection details:
   - **Display name**: `PostgreSQL_MVP` (or your preference)
   - **Host**: `localhost` (or your Postgres server IP)
   - **Port**: `5432`
   - **Database**: `dating_platform_mvp`
   - **User**: `your_db_user`
   - **Password**: `your_db_password`
   - **SSL**: Uncheck (unless required)
4. Click **Test connection** → verify ✅ Success
5. Click **Save**

**Important**: Write down the **Credential ID** displayed after save (e.g., `pg_abc123def456`)

#### Step 2: Verify Credential Works

1. Create a test workflow (temporary)
2. Add **Postgres** node
3. Select `PostgreSQL_MVP` credential
4. Enter test query: `SELECT 1;`
5. Click **Execute** → should return `1`
6. Delete test workflow

---

## Workflow Import

### Step 1: Download Workflow File

Source: `n8n/workflows/auth/WF_01_USER_REGISTRATION.json`

**CRITICAL**: Do NOT import from `n8n/workflows/registration/WF_01_USER_REGISTRATION.json` (legacy)

### Step 2: Import Workflow

1. Open n8n UI → **Workflows** (left sidebar)
2. Click **Import from file**
3. Select `n8n/workflows/auth/WF_01_USER_REGISTRATION.json`
4. Click **Import**
5. Workflow should load with name: `WF_01_USER_REGISTRATION`

### Step 3: Resolve Credential Warnings

After import, you'll see credential warnings for `POSTGRES_PLACEHOLDER`.

For each Postgres node in the workflow:
1. Click the node name to open node details
2. In **Credentials** field, select `PostgreSQL_MVP` (the credential you created)
3. Click **Save node**

Nodes to update:
- [ ] **Create user** (Postgres node)
- [ ] **Create telegram_account** (Postgres node)
- [ ] **Create audit_event** (Postgres node)

All three must have **valid Postgres credentials** (not placeholders).

### Step 4: Verify Workflow Structure

After credential binding, verify node connections:

```
Webhook Trigger
        ↓
Extract input
        ↓
Create user (Postgres)
        ↓
Create telegram_account (Postgres)
        ↓
Create audit_event (Postgres)
        ↓
Prepare response
        ↓
Respond to Webhook
```

Check in n8n UI:
- [ ] All nodes connected in correct order
- [ ] No red error indicators
- [ ] All Postgres nodes have green credential checkmarks

### Step 5: Configure Webhook URL

1. Click **Webhook Trigger** node
2. Copy the **Webhook URL** displayed (e.g., `https://your-n8n-domain.com/webhook/user-registration`)
3. Save this URL — you'll need it for Telegram webhook setup

**For local development (localhost):**
- Use **ngrok** or similar tunneling service
- Example: `ngrok http 5678` → `https://abc123.ngrok.io/webhook/user-registration`

### Step 6: Save Workflow

1. Click **Save** (top-right)
2. Workflow should save without errors
3. Status should show: **INACTIVE** (expected for MVP)

---

## Post-Import Verification

### 1. Test Database Connection

1. Open any Postgres node (e.g., **Create user**)
2. Click **Test** button
3. Should return sample data or "✅ Success"
4. If error: verify credentials and PostgreSQL is running

### 2. Validate SQL Queries

Check each Postgres node's query:

**Create user node**:
```sql
INSERT INTO users (id) VALUES (uuid_generate_v4()) RETURNING id;
```
✅ Should insert UUID, return new id

**Create telegram_account node**:
```sql
INSERT INTO telegram_accounts (id, user_id, telegram_id, username)
SELECT uuid_generate_v4(), '{{ $node["Create user"].json[0].id }}', '{{ $json["telegram_id"] }}', '{{ $json["telegram_username"] }}'
WHERE '{{ $json["telegram_id"] }}' != ''
RETURNING id;
```
✅ Should link to user_id, insert telegram_id and username

**Create audit_event node**:
```sql
INSERT INTO audit_events (user_id, event_type, event_data) 
VALUES ('{{ $node["Create user"].json[0].id }}', 'user_registration', jsonb_build_object('source','telegram'))
```
✅ Should insert audit record with event_type='user_registration'

### 3. Verify Webhook Path

- [ ] Webhook Trigger node shows path: `user-registration`
- [ ] Full webhook URL is accessible from internet (test with curl)

### 4. Test Node Connections

1. Click **Webhook Trigger** node
2. Click **Execute** (manual test)
3. Provide sample JSON input (see WF_01_RUNTIME_COMMANDS.md)
4. Workflow should execute all nodes in sequence
5. Check **Execution** tab for results

---

## Environment Variables (Optional)

If using environment variables for database connection:

```bash
# .env file (example)
N8N_POSTGRES_HOST=localhost
N8N_POSTGRES_PORT=5432
N8N_POSTGRES_DATABASE=dating_platform_mvp
N8N_POSTGRES_USER=your_user
N8N_POSTGRES_PASSWORD=your_password
```

---

## Security Checklist

- [ ] No hardcoded passwords in workflow JSON
- [ ] No Telegram tokens in workflow JSON
- [ ] Credentials stored in n8n secure store (not in JSON)
- [ ] PostgreSQL uses strong password
- [ ] Webhook endpoint requires authentication (if sensitive)
- [ ] HTTPS enabled for n8n (required for Telegram webhook)

---

## Known Issues & Workarounds

### Issue: "Credential with ID POSTGRES_PLACEHOLDER not found"

**Solution**: 
1. Check all 3 Postgres nodes have valid credentials selected
2. Verify credential exists in Credentials page
3. Re-save workflow

### Issue: "Connection refused" error

**Solution**:
1. Verify PostgreSQL is running: `psql -h localhost -U your_user -d dating_platform_mvp -c "SELECT 1;"`
2. Check n8n credential has correct host/port
3. If using Docker: ensure networks are connected

### Issue: Webhook URL returns 404

**Solution**:
1. Verify webhook path is `user-registration`
2. Check webhook is activated (toggle should show active)
3. For local development, use ngrok: `ngrok http 5678`

---

## Next Steps

1. ✅ Complete this checklist
2. ✅ Activate workflow in n8n UI (click **Active** toggle)
3. ✅ Configure Telegram webhook (see WF_01_RUNTIME_COMMANDS.md)
4. ✅ Run smoke tests (see WF_01_SMOKE_TEST.md)
5. ✅ Monitor execution logs for errors

---

**Checklist created**: 2026-08-07  
**Status**: Ready for import  
**MVP workflow**: WF_01_USER_REGISTRATION (auth/ path)
