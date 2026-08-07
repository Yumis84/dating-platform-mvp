# WF_01 Deployment Checklist

Дата: 2026-08-07  
Статус: Pre-Deployment Checklist  
Назначение: Пошаговые инструкции для развёртывания WF_01 в production-ready окружении.

---

## Phase 1: Pre-Deployment Verification

### 1.1 Environment Check

#### PostgreSQL

```bash
# Verify PostgreSQL is running
psql --version
# Expected: psql (PostgreSQL) 15.x or higher

# Verify connectivity
psql -h localhost -p 5432 -U your_db_user -d dating_platform_mvp -c "SELECT 1;"
# Expected: 1

# Verify uuid-ossp extension
psql -d dating_platform_mvp -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"; SELECT 1;"
# Expected: 1
```

**✓ Checklist:**
- [ ] PostgreSQL 15+ installed
- [ ] Database `dating_platform_mvp` exists
- [ ] User `your_db_user` has full permissions
- [ ] Port 5432 accessible
- [ ] uuid-ossp extension available

#### n8n Instance

```bash
# Verify n8n is running
curl -s http://localhost:5678/api/v1/status | jq .status
# Expected: "ok"

# Verify n8n version
curl -s http://localhost:5678/api/v1/status | jq .version
# Expected: 1.x.x or higher

# Check Postgres node availability
curl -s http://localhost:5678/api/v1/credentials/postgres-node-exists | jq .
```

**✓ Checklist:**
- [ ] n8n UI accessible at http://localhost:5678
- [ ] n8n status is "ok"
- [ ] n8n version 1.0+
- [ ] No pending migrations in n8n
- [ ] Basic auth configured (if required)

### 1.2 Database Migration Verification

```bash
# Run dry-run migrations
chmod +x scripts/dry_run_migrations.sh
./scripts/dry_run_migrations.sh
# Expected: [PASS] All checks passed! Database is ready for WF_01

# Verify all tables exist
psql -d dating_platform_mvp -c "\dt"
# Expected: tables list includes users, telegram_accounts, audit_events

# Verify users table structure
psql -d dating_platform_mvp -c "\d users"
# Expected:
#  id | uuid primary key
#  role | varchar(16)
#  created_at | timestamp with time zone
#  updated_at | timestamp with time zone

# Verify telegram_accounts table structure
psql -d dating_platform_mvp -c "\d telegram_accounts"
# Expected:
#  id | uuid primary key
#  user_id | uuid not null (foreign key)
#  telegram_id | bigint not null unique
#  username | text
#  created_at | timestamp with time zone

# Verify audit_events table structure
psql -d dating_platform_mvp -c "\d audit_events"
# Expected:
#  id | uuid primary key
#  user_id | uuid (foreign key)
#  event_type | text not null
#  event_data | jsonb
#  created_at | timestamp with time zone

# Verify indexes
psql -d dating_platform_mvp -c "SELECT indexname FROM pg_indexes WHERE tablename='audit_events';"
# Expected: 4 indexes (user_id, event_type, event_type_created, created_at)
```

**✓ Checklist:**
- [ ] Dry-run migrations PASSED
- [ ] users table exists and has correct structure
- [ ] telegram_accounts table exists with FK and UNIQUE constraints
- [ ] audit_events table exists with indexes
- [ ] All foreign keys properly defined
- [ ] No orphaned records in audit_events

### 1.3 Network & Access Verification

#### Local Development (localhost)

```bash
# Verify localhost access
curl -i http://localhost:5678
# Expected: 200 OK response

# Verify database access from localhost
psql -h localhost -p 5432 -U your_db_user -d dating_platform_mvp -c "SELECT 1;"
# Expected: 1
```

#### Remote Access (ngrok for testing)

```bash
# Start ngrok tunnel (if needed for local testing)
ngrok http 5678
# Expected output:
# Forwarding                    https://abc123.ngrok.io -> http://localhost:5678

# Verify ngrok tunnel works
curl -i https://abc123.ngrok.io
# Expected: 200 OK response from n8n

# Save ngrok URL for webhook configuration
export NGROK_URL="https://abc123.ngrok.io"
```

**✓ Checklist:**
- [ ] localhost:5678 returns 200 OK
- [ ] localhost PostgreSQL access works
- [ ] (Optional) ngrok tunnel active if using local development
- [ ] (Optional) ngrok URL copied to environment variable

---

## Phase 2: PostgreSQL Credential Setup in n8n

### 2.1 Access n8n UI

1. Open browser: `http://localhost:5678`
2. Login with n8n credentials (if auth enabled)
3. Left sidebar → Click **Credentials** (key icon)

### 2.2 Create PostgreSQL Credential

**Step 1: Create New Credential**

1. Click **Create new** button
2. Search for or select **PostgreSQL**
3. Click to add PostgreSQL credential type

**Step 2: Fill Credential Form**

| Field | Value | Example |
|-------|-------|----------|
| Display name | Memorable name | `PostgreSQL_MVP` |
| Host | PostgreSQL server hostname | `localhost` or `postgres` (Docker) |
| Port | PostgreSQL port | `5432` |
| Database | Database name | `dating_platform_mvp` |
| User | Database user | `postgres` or `mvp_user` |
| Password | Database password | `your_secure_password` |
| SSL | Connection security | `Disable` (dev) or `Require` (prod) |

**Visual guide:**

```
┌─────────────────────────────────────┐
│ Create new credential: PostgreSQL   │
├─────────────────────────────────────┤
│ Display name:  [PostgreSQL_MVP____] │
│ Host:          [localhost_________] │
│ Port:          [5432______________] │
│ Database:      [dating_platform_mvp] │
│ User:          [postgres__________] │
│ Password:      [••••••••••••••••••] │
│ SSL:           [Disable ▼__________] │
├─────────────────────────────────────┤
│ [Test connection]  [Save]           │
└─────────────────────────────────────┘
```

**Step 3: Test Connection**

1. Click **Test connection** button
2. Expected response: ✅ **Connection successful**
3. If failed:
   - Verify PostgreSQL is running
   - Check host/port/credentials
   - Check network connectivity
   - Review error message in n8n UI

**Step 4: Save Credential**

1. Click **Save** button
2. Credential is now available for use in workflows
3. Note the credential name: `PostgreSQL_MVP` (used in next phase)

**✓ Checklist:**
- [ ] Credential creation form accessed
- [ ] All fields filled with correct values
- [ ] Test connection returns ✅ Success
- [ ] Credential saved with display name `PostgreSQL_MVP`
- [ ] Credential appears in Credentials list

---

## Phase 3: Import WF_01 Workflow

### 3.1 Access Workflows Section

1. Left sidebar → Click **Workflows** (document icon)
2. Click **Import from file** button

### 3.2 Select Workflow JSON

1. File browser dialog appears
2. Navigate to: `n8n/workflows/auth/WF_01_USER_REGISTRATION.json`
3. Select file
4. Click **Open** or **Import**

**File path verification:**
```bash
ls -la n8n/workflows/auth/WF_01_USER_REGISTRATION.json
# Expected: file exists and is readable
```

### 3.3 Workflow Import Completion

1. Workflow is imported with name: **WF_01_USER_REGISTRATION**
2. Status: **INACTIVE** (not yet running)
3. Expected screen:
   ```
   Workflow: WF_01_USER_REGISTRATION
   Status: INACTIVE
   ID: WF_01_USER_REGISTRATION_0001
   Nodes: 7
   Last active: Never
   ```

**✓ Checklist:**
- [ ] File dialog opened
- [ ] Correct JSON file selected
- [ ] Import succeeded
- [ ] Workflow appears in Workflows list
- [ ] Workflow name is "WF_01_USER_REGISTRATION"
- [ ] Status shows "INACTIVE"

---

## Phase 4: Bind PostgreSQL Credential to Nodes

### 4.1 Open Workflow

1. In Workflows list, click **WF_01_USER_REGISTRATION**
2. Workflow canvas appears with 7 nodes

### 4.2 Identify PostgreSQL Nodes

Three nodes require credential binding:

1. **Create user** (position: center-left)
2. **Create telegram_account** (position: center)
3. **Create audit_event** (position: center-right)

### 4.3 Bind Credential to Each Node

**For each PostgreSQL node:**

#### Node 1: Create user

1. Click on **Create user** node on canvas
2. Right panel shows node configuration
3. Look for **Credentials** field
4. Click dropdown: `SELECT POSTGRES_PLACEHOLDER` or empty
5. Select **PostgreSQL_MVP** from dropdown list
6. Dropdown now shows: `PostgreSQL_MVP` ✅
7. Click **Save** button (or Ctrl+S)

**Visual:**
```
┌─ Workflow Canvas ──────────────────────┐
│                                        │
│   [Webhook Trigger]                   │
│          ↓                             │
│   [Extract input]                     │
│          ↓                             │
│   ┌─ [Create user] ← CLICK HERE       │
│   │       ↓                            │
│   │   [Create telegram_account]       │
│   │       ↓                            │
│   │   [Create audit_event]            │
│   │       ↓                            │
│   │   [Prepare response]              │
│   │       ↓                            │
│   └─ [Respond to Webhook]            │
│                                        │
└────────────────────────────────────────┘

┌─ Right Panel (Configuration) ───────────┐
│ Create user                             │
├─────────────────────────────────────────┤
│ Operation:  [executeQuery ▼]           │
│                                        │
│ Query:                                 │
│ INSERT INTO users (id)                │
│ VALUES (uuid_generate_v4())           │
│ RETURNING id;                         │
│                                        │
│ Credentials:  [PostgreSQL_MVP ▼] ✅  │
│                                        │
│ [Save]  [Test]                        │
└─────────────────────────────────────────┘
```

#### Node 2: Create telegram_account

1. Click on **Create telegram_account** node
2. Right panel shows node configuration
3. Credentials field currently shows: `POSTGRES_PLACEHOLDER`
4. Click dropdown
5. Select **PostgreSQL_MVP**
6. Dropdown now shows: `PostgreSQL_MVP` ✅
7. Click **Save** (Ctrl+S)

#### Node 3: Create audit_event

1. Click on **Create audit_event** node
2. Right panel shows node configuration
3. Credentials field currently shows: `POSTGRES_PLACEHOLDER`
4. Click dropdown
5. Select **PostgreSQL_MVP**
6. Dropdown now shows: `PostgreSQL_MVP` ✅
7. Click **Save** (Ctrl+S)

### 4.4 Verify Credential Binding

```bash
# After binding all three nodes, verify by:
# 1. Click on each node and confirm Credentials dropdown shows PostgreSQL_MVP
# 2. Click "Test" button on each Postgres node to verify connection
```

**Test Connection Example:**

1. Click on **Create user** node
2. In right panel, look for **Test** button (or similar)
3. Click **Test**
4. Expected: ✅ Connection successful (no error message)
5. Repeat for other two Postgres nodes

**✓ Checklist:**
- [ ] Create user node: Credentials = PostgreSQL_MVP
- [ ] Create telegram_account node: Credentials = PostgreSQL_MVP
- [ ] Create audit_event node: Credentials = PostgreSQL_MVP
- [ ] All three nodes show ✅ when tested
- [ ] Workflow saved (Ctrl+S)

---

## Phase 5: Webhook Configuration

### 5.1 Get Webhook URL from n8n

1. In workflow canvas, click on **Webhook Trigger** node (first node)
2. Right panel shows webhook configuration
3. Look for **Webhook URL** field
4. Copy the URL

**Example webhook URL:**
```
http://localhost:5678/webhook/user-registration
```

Or with ngrok:
```
https://abc123.ngrok.io/webhook/user-registration
```

### 5.2 (Optional) Configure Telegram Bot Webhook

**Only if using real Telegram bot:**

```bash
# Set webhook on Telegram bot
curl -X POST \
  https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \
  -d url=<YOUR_WEBHOOK_URL>

# Example:
curl -X POST \
  https://api.telegram.org/bot123456789:ABCDefghIjklMnoPqrStUvWxyz/setWebhook \
  -d url=https://abc123.ngrok.io/webhook/user-registration

# Verify webhook set
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo

# Expected response:
# {
#   "ok": true,
#   "result": {
#     "url": "https://abc123.ngrok.io/webhook/user-registration",
#     "has_custom_certificate": false,
#     "pending_update_count": 0
#   }
# }
```

**✓ Checklist:**
- [ ] Webhook URL copied from n8n UI
- [ ] Webhook URL format verified (http/https, correct path)
- [ ] (Optional) Telegram webhook configured
- [ ] (Optional) Telegram webhook verification returns 200 OK

---

## Phase 6: Workflow Activation

### 6.1 Activate Workflow

1. In workflow view, top-right corner shows **Active** toggle (currently OFF/grey)
2. Click the toggle to turn it ON
3. Confirmation dialog may appear: "Activate this workflow?"
4. Click **Confirm** or **Yes**

**Visual:**
```
Top-right of workflow:
[Active] ← OFF/grey → [Active] ← ON/green
```

### 6.2 Verify Activation

1. Toggle should now show **green** (ON)
2. Status text changes from "INACTIVE" to "ACTIVE"
3. Workflow is now listening on webhook URL

**Verification:**
```bash
# n8n should log activation
docker logs dating_n8n | grep -i "WF_01\|workflow.*active" | tail -5
```

**✓ Checklist:**
- [ ] Workflow Active toggle is ON (green)
- [ ] Workflow status shows "ACTIVE"
- [ ] No error messages in n8n UI
- [ ] No errors in n8n logs
- [ ] Webhook URL is ready to receive requests

---

## Phase 7: First Smoke Test Execution

### 7.1 Prepare Test Request

**Save this bash script as `test_wf01.sh`:**

```bash
#!/bin/bash

# Configuration
WEBHOOK_URL="http://localhost:5678/webhook/user-registration"
# Or for ngrok: WEBHOOK_URL="https://abc123.ngrok.io/webhook/user-registration"

# Test data
TELEGRAM_ID=123456789
TEST_USERNAME="test_user_$(date +%s)"

echo "=== WF_01 Smoke Test ==="
echo "Webhook URL: $WEBHOOK_URL"
echo "Telegram ID: $TELEGRAM_ID"
echo "Username: $TEST_USERNAME"
echo ""

# Send test request
echo "Sending webhook request..."
RESPONSE=$(curl -s -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"update_id\": 1001,
    \"message\": {
      \"message_id\": 1,
      \"date\": $(date +%s),
      \"chat\": {
        \"id\": 987654321,
        \"type\": \"private\"
      },
      \"from\": {
        \"id\": $TELEGRAM_ID,
        \"is_bot\": false,
        \"first_name\": \"Test\",
        \"username\": \"$TEST_USERNAME\"
      },
      \"text\": \"/start\"
    }
  }")

echo "Response:"
echo "$RESPONSE" | jq . || echo "$RESPONSE"
echo ""

# Check response contains expected message
if echo "$RESPONSE" | grep -q "Welcome"; then
  echo "✓ Webhook execution successful"
else
  echo "✗ Webhook execution failed"
  exit 1
fi
```

### 7.2 Execute Test

```bash
chmod +x test_wf01.sh
./test_wf01.sh
```

**Expected output:**
```
=== WF_01 Smoke Test ===
Webhook URL: http://localhost:5678/webhook/user-registration
Telegram ID: 123456789
Username: test_user_1691234567

Sending webhook request...
Response:
{
  "text": "Welcome! Registration complete. Please choose your role (MAN or WOMAN) using the role selection UI."
}

✓ Webhook execution successful
```

### 7.3 Check n8n Execution Logs

1. Open workflow in n8n UI
2. At bottom, look for **Execution history**
3. Should show latest execution with timestamp matching test time
4. Click on execution row to view details
5. All 7 nodes should show ✅ (green)

**If any node shows ❌ (red):**
1. Click on failing node
2. Check error message
3. Common issues:
   - Postgres credential not bound
   - PostgreSQL connection failed
   - SQL syntax error
   - Migration not applied

**✓ Checklist:**
- [ ] Test script created and executable
- [ ] Webhook request sent successfully
- [ ] Response received with "Welcome" message
- [ ] HTTP status 200 OK
- [ ] n8n execution history shows new execution
- [ ] All 7 nodes show ✅ (green) in execution

---

## Phase 8: Database Verification

### 8.1 Verify users Table

```bash
psql -d dating_platform_mvp -c "
  SELECT id, role, created_at 
  FROM users 
  WHERE created_at > NOW() - INTERVAL '5 minutes'
  ORDER BY created_at DESC 
  LIMIT 1;
"
```

**Expected output:**
```
                   id                   | role |            created_at
----------------------------------------+------+-------------------------------
 a1b2c3d4-e5f6-7890-ab12-cdef34567890 | NULL | 2026-08-07 19:30:45.123456+00
(1 row)
```

**Verification points:**
- [ ] 1 new row in users table
- [ ] id is UUID
- [ ] role is NULL
- [ ] created_at is recent (within test execution time)

### 8.2 Verify telegram_accounts Table

```bash
psql -d dating_platform_mvp -c "
  SELECT id, user_id, telegram_id, username, created_at 
  FROM telegram_accounts 
  WHERE telegram_id = 123456789
  ORDER BY created_at DESC 
  LIMIT 1;
"
```

**Expected output:**
```
                   id                   |              user_id             | telegram_id | username   |            created_at
----------------------------------------+----------------------------------+-------------+------------+-------------------------------
 b2c3d4e5-f6a7-8901-bc23-def456789abc | a1b2c3d4-e5f6-7890-ab12-cdef... | 123456789   | test_user  | 2026-08-07 19:30:45.234567+00
(1 row)
```

**Verification points:**
- [ ] 1 new row in telegram_accounts
- [ ] id is UUID
- [ ] user_id matches users.id from 8.1
- [ ] telegram_id is 123456789 (from test)
- [ ] username is test_user (from test)
- [ ] created_at within 1 second of users.created_at

### 8.3 Verify audit_events Table

```bash
psql -d dating_platform_mvp -c "
  SELECT id, user_id, event_type, event_data, created_at 
  FROM audit_events 
  WHERE event_type = 'user_registration'
  AND created_at > NOW() - INTERVAL '5 minutes'
  ORDER BY created_at DESC 
  LIMIT 1;
"
```

**Expected output:**
```
                   id                   |              user_id             |   event_type      |       event_data       |            created_at
----------------------------------------+----------------------------------+-------------------+------------------------+-------------------------------
 c3d4e5f6-a7b8-9012-cd34-ef5678901234 | a1b2c3d4-e5f6-7890-ab12-cdef... | user_registration | {"source": "telegram"} | 2026-08-07 19:30:45.345678+00
(1 row)
```

**Verification points:**
- [ ] 1 new row in audit_events
- [ ] id is UUID
- [ ] user_id matches users.id from 8.1
- [ ] event_type is 'user_registration'
- [ ] event_data contains {"source": "telegram"}
- [ ] created_at within 1 second of users.created_at

### 8.4 Combined Verification Query

```bash
psql -d dating_platform_mvp -c "
SELECT 
  (SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '5 minutes') as new_users,
  (SELECT COUNT(*) FROM telegram_accounts WHERE created_at > NOW() - INTERVAL '5 minutes') as new_accounts,
  (SELECT COUNT(*) FROM audit_events WHERE created_at > NOW() - INTERVAL '5 minutes') as new_audit_events;
"
```

**Expected output:**
```
 new_users | new_accounts | new_audit_events
-----------+--------------+------------------
         1 |            1 |                1
(1 row)
```

**✓ Checklist:**
- [ ] 1 new row in users table
- [ ] 1 new row in telegram_accounts table (with matching user_id FK)
- [ ] 1 new row in audit_events table (with matching user_id FK)
- [ ] All foreign keys valid
- [ ] All timestamps consistent (within 1 second)
- [ ] event_data JSON valid
- [ ] telegram_id UNIQUE constraint not violated

---

## Phase 9: Success Confirmation

### 9.1 All Checks Passed?

If **ALL** of the following are true:

- ✅ Webhook returned HTTP 200 with welcome message
- ✅ 1 new user row created
- ✅ 1 new telegram_account row created (linked to user)
- ✅ 1 new audit_event row created (linked to user, type='user_registration')
- ✅ All n8n execution nodes green ✅
- ✅ Database foreign keys valid
- ✅ No SQL errors

**THEN: WF_01 DEPLOYMENT SUCCESSFUL** 🎉

### 9.2 Test Additional Users

Run test again with different telegram_id:

```bash
# Modify test_wf01.sh or run inline:
TELEGRAM_ID=123456790 \
TEST_USERNAME="test_user_2" \
curl -X POST "http://localhost:5678/webhook/user-registration" \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": 1002,
    "message": {
      "message_id": 2,
      "date": '$(date +%s)',
      "chat": {"id": 987654321, "type": "private"},
      "from": {
        "id": 123456790,
        "is_bot": false,
        "first_name": "Test2",
        "username": "test_user_2"
      },
      "text": "/start"
    }
  }'

# Verify in database
psql -d dating_platform_mvp -c "SELECT COUNT(*) FROM users;"
# Expected: 2 or more
```

**✓ Checklist:**
- [ ] Second user registration successful
- [ ] Third user registration successful (optional)
- [ ] Each creates separate rows in all 3 tables
- [ ] No duplicate key errors

---

## Phase 10: Rollback Procedures

### 10.1 If Deployment Fails

#### Option A: Deactivate Workflow (Quickest)

```bash
# In n8n UI:
# 1. Open WF_01_USER_REGISTRATION workflow
# 2. Toggle "Active" to OFF (grey)
# 3. Workflow stops receiving webhooks
```

**Effect:** No new registrations will be processed
**Data:** Existing registrations remain in database

#### Option B: Clear Test Data

```bash
# Only if test data needs to be removed:
psql -d dating_platform_mvp << EOF
BEGIN;
  DELETE FROM audit_events WHERE created_at > NOW() - INTERVAL '1 hour';
  DELETE FROM telegram_accounts WHERE created_at > NOW() - INTERVAL '1 hour';
  DELETE FROM users WHERE created_at > NOW() - INTERVAL '1 hour';
COMMIT;
EOF

# Verify cleanup
psql -d dating_platform_mvp -c "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM telegram_accounts; SELECT COUNT(*) FROM audit_events;"
```

#### Option C: Reimport Workflow

```bash
# If workflow import was corrupted:
# 1. In n8n UI, delete WF_01_USER_REGISTRATION (or rename)
# 2. Re-import from n8n/workflows/auth/WF_01_USER_REGISTRATION.json
# 3. Repeat credential binding
# 4. Reactivate
```

#### Option D: Full Database Restore

```bash
# If critical data corruption occurred:
# 1. Stop n8n
# 2. Restore from backup
psql -d dating_platform_mvp < backup_YYYYMMDD.sql

# 3. Verify schema integrity
./scripts/dry_run_migrations.sh

# 4. Restart n8n
# 5. Reimport workflow
```

### 10.2 Common Failure Scenarios

#### Scenario: Webhook returns 500 error

**Diagnosis:**
1. Check n8n execution logs for error
2. Likely: PostgreSQL credential not bound or invalid

**Resolution:**
1. Re-verify PostgreSQL credential in n8n
2. Re-bind credential to all 3 Postgres nodes
3. Test connection on each node
4. Retry webhook call

#### Scenario: Database shows no new rows

**Diagnosis:**
1. Check n8n execution logs
2. Likely: PostgreSQL not accessible or migration not applied

**Resolution:**
1. Verify PostgreSQL is running: `psql -U postgres -c "SELECT 1;"`
2. Verify tables exist: `psql -d dating_platform_mvp -c "\dt"`
3. Re-run migrations: `./scripts/dry_run_migrations.sh`
4. Retry webhook call

#### Scenario: Duplicate key error on second test

**This is expected (MVP limitation)**

**Reason:** No duplicate check in WF_01 MVP

**Resolution:**
1. Use different telegram_id for each test
2. Or clear test data between tests (Option B above)

### 10.3 Rollback Checklist

- [ ] Identify the failure scenario
- [ ] Choose appropriate rollback option (A, B, C, or D)
- [ ] Execute rollback steps
- [ ] Verify database integrity
- [ ] Verify n8n workflow status
- [ ] Document root cause
- [ ] Proceed with deployment fix

---

## Final Deployment Checklist

### Pre-Deployment

```
☐ PostgreSQL 15+ running
☐ Database dating_platform_mvp exists
☐ Dry-run migrations PASSED
☐ All 3 required tables exist (users, telegram_accounts, audit_events)
☐ n8n running and accessible
☐ n8n status OK
```

### Credential Setup

```
☐ PostgreSQL credential created in n8n
☐ Credential name: PostgreSQL_MVP
☐ Test connection: SUCCESS
☐ Credential saved
```

### Workflow Import

```
☐ WF_01_USER_REGISTRATION.json imported
☐ Workflow shows 7 nodes
☐ Workflow status: INACTIVE
```

### Credential Binding

```
☐ Create user node: credential bound
☐ Create telegram_account node: credential bound
☐ Create audit_event node: credential bound
☐ All 3 nodes tested and connected
```

### Activation & Testing

```
☐ Workflow activated (toggle ON)
☐ Webhook URL copied
☐ First smoke test executed
☐ HTTP 200 response received
☐ n8n execution shows all nodes green ✅
```

### Database Verification

```
☐ 1 new row in users table
☐ 1 new row in telegram_accounts table (FK valid)
☐ 1 new row in audit_events table (FK valid)
☐ All timestamps consistent
☐ Foreign keys valid
```

### Post-Deployment

```
☐ Second test with different telegram_id successful
☐ No errors in n8n logs
☐ No errors in PostgreSQL logs
☐ Rollback procedures documented and tested
☐ WF_01 marked READY FOR PRODUCTION
```

---

## Support & Troubleshooting

**For detailed troubleshooting:** See `docs/WF_01_IMPLEMENTATION_GUIDE.md` → Troubleshooting section

**For runtime commands:** See `docs/WF_01_RUNTIME_COMMANDS.md`

**For live test report:** See `docs/WF_01_LIVE_TEST_REPORT.md`

---

**Deployment Checklist Status:** ✅ READY
**Date:** 2026-08-07
**WF_01 MVP:** 🚀 APPROVED FOR DEPLOYMENT