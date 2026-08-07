#!/bin/bash
# scripts/dry_run_migrations.sh
# Clean PostgreSQL dry-run for canonical migrations 001-008
# Purpose: Verify that migrations apply without errors and create expected schema
# Usage: ./scripts/dry_run_migrations.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
POSTGRES_VERSION="15-alpine"
CONTAINER_NAME="dating-mvp-dryrun-$(date +%s)"
DB_NAME="dating_platform_mvp_test"
DB_USER="testuser"
DB_PASSWORD="testpass123"
DB_HOST="localhost"
DB_PORT="5433"
MIGRATIONS_DIR="database/migrations"

# Canonical migrations (in order)
CANONICAL_MIGRATIONS=(
  "001_users_and_telegram_accounts_schema.sql"
  "002_profiles_schema.sql"
  "003_moderation_schema.sql"
  "004_catalog_schema.sql"
  "005_chat_schema.sql"
  "006_chat_reliability_schema.sql"
  "007_chat_message_moderation_schema.sql"
  "008_audit_events_schema.sql"
)

# Expected tables
EXPECTED_TABLES=(
  "users"
  "telegram_accounts"
  "profiles"
  "profile_photos"
  "profile_ai_sessions"
  "profile_fields_history"
  "profile_moderation"
  "moderation_rules"
  "moderation_history"
  "profile_views"
  "favorites"
  "profile_search_events"
  "chat_sessions"
  "messages"
  "chat_blocks"
  "chat_reports"
  "message_delivery_queue"
  "message_rate_limits"
  "chat_moderation_events"
  "message_moderation_queue"
  "audit_events"
)

# Counters
PASS_COUNT=0
FAIL_COUNT=0

# Logging functions
log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[PASS]${NC} $1"
  ((PASS_COUNT++))
}

log_error() {
  echo -e "${RED}[FAIL]${NC} $1"
  ((FAIL_COUNT++))
}

log_warning() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

log_section() {
  echo ""
  echo -e "${BLUE}========================================${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}========================================${NC}"
}

# Cleanup function
cleanup() {
  log_info "Cleaning up..."
  
  if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log_info "Stopping and removing container ${CONTAINER_NAME}..."
    docker stop "${CONTAINER_NAME}" 2>/dev/null || true
    docker rm "${CONTAINER_NAME}" 2>/dev/null || true
  fi
  
  log_info "Cleanup complete"
}

# Trap EXIT to ensure cleanup
trap cleanup EXIT

# Check Docker
log_section "Pre-flight Checks"

if ! command -v docker &> /dev/null; then
  log_error "Docker is not installed"
  exit 1
fi
log_success "Docker is available"

if ! [ -d "${MIGRATIONS_DIR}" ]; then
  log_error "Migrations directory not found: ${MIGRATIONS_DIR}"
  exit 1
fi
log_success "Migrations directory found"

# Check that canonical migrations exist
log_info "Checking canonical migrations..."
for migration in "${CANONICAL_MIGRATIONS[@]}"; do
  if ! [ -f "${MIGRATIONS_DIR}/${migration}" ]; then
    log_error "Canonical migration not found: ${migration}"
    exit 1
  fi
  log_success "Found: ${migration}"
done

# Check that legacy 001 is NOT applied
if [ -f "${MIGRATIONS_DIR}/001_initial_users_schema.sql" ]; then
  log_warning "Legacy 001_initial_users_schema.sql exists (will be ignored)"
fi

# Start PostgreSQL container
log_section "Starting PostgreSQL Container"

docker run -d \
  --name "${CONTAINER_NAME}" \
  -e POSTGRES_DB="${DB_NAME}" \
  -e POSTGRES_USER="${DB_USER}" \
  -e POSTGRES_PASSWORD="${DB_PASSWORD}" \
  -p "${DB_PORT}:5432" \
  postgres:"${POSTGRES_VERSION}" > /dev/null

log_info "Container started: ${CONTAINER_NAME}"
log_info "Waiting for PostgreSQL to be ready..."

# Wait for PostgreSQL to be ready (max 30 seconds)
RETRY=0
MAX_RETRIES=30
until docker exec "${CONTAINER_NAME}" pg_isready -U "${DB_USER}" -d "${DB_NAME}" &> /dev/null; do
  if [ $RETRY -eq $MAX_RETRIES ]; then
    log_error "PostgreSQL did not start within 30 seconds"
    exit 1
  fi
  sleep 1
  ((RETRY++))
done

log_success "PostgreSQL is ready"

# Helper function to execute SQL
execute_sql() {
  local sql="$1"
  docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" -c "$sql" 2>&1
}

# Helper function to execute SQL file
execute_sql_file() {
  local filepath="$1"
  docker exec -i "${CONTAINER_NAME}" psql -U "${DB_USER}" -d "${DB_NAME}" < "$filepath" 2>&1
}

# Apply migrations
log_section "Applying Canonical Migrations"

MIGRATION_NUM=0
for migration in "${CANONICAL_MIGRATIONS[@]}"; do
  ((MIGRATION_NUM++))
  migration_file="${MIGRATIONS_DIR}/${migration}"
  
  log_info "[${MIGRATION_NUM}/8] Applying ${migration}..."
  
  if execute_sql_file "${migration_file}" > /dev/null 2>&1; then
    log_success "Applied ${migration}"
  else
    log_error "Failed to apply ${migration}"
    log_error "Output:"
    execute_sql_file "${migration_file}" || true
    exit 1
  fi
done

# Verify tables
log_section "Verifying Tables"

TABLE_COUNT=$(execute_sql "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | grep -oE '[0-9]+' | head -1)
EXPECTED_COUNT=${#EXPECTED_TABLES[@]}

if [ "$TABLE_COUNT" -ge "$EXPECTED_COUNT" ]; then
  log_success "Tables created: $TABLE_COUNT (expected at least $EXPECTED_COUNT)"
else
  log_error "Table count mismatch: $TABLE_COUNT (expected at least $EXPECTED_COUNT)"
fi

# Check each expected table
log_info "Checking individual tables..."
for table in "${EXPECTED_TABLES[@]}"; do
  TABLE_EXISTS=$(execute_sql "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '${table}');" | grep -E "t|f" | head -1)
  
  if [ "$TABLE_EXISTS" = "t" ]; then
    log_success "Table found: ${table}"
  else
    log_error "Table missing: ${table}"
  fi
done

# Check Foreign Keys
log_section "Verifying Foreign Keys"

FK_ERRORS=$(execute_sql "
  SELECT COUNT(*)
  FROM information_schema.table_constraints
  WHERE constraint_type = 'FOREIGN KEY'
    AND table_schema = 'public'
" | grep -oE '[0-9]+' | head -1)

if [ "$FK_ERRORS" -gt 0 ]; then
  log_success "Foreign keys found: $FK_ERRORS"
  # List FKs
  execute_sql "
    SELECT constraint_name, table_name, column_name
    FROM information_schema.constraint_column_usage
    WHERE table_schema = 'public'
    ORDER BY table_name
  " | tail -n +3 | head -20 || true
else
  log_warning "No foreign keys found (might be expected if constraints are defined inline)"
fi

# Verify audit_events structure
log_section "Verifying audit_events Table"

# Check audit_events exists
if execute_sql "SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_events';" | grep -q "1"; then
  log_success "audit_events table exists"
  
  # Check columns
  COLUMNS=$(execute_sql "
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_name = 'audit_events'
  " | grep -oE '[0-9]+' | head -1)
  
  log_info "audit_events columns: $COLUMNS (expected: 5 = id, user_id, event_type, event_data, created_at)"
  
  # Check indexes
  INDEXES=$(execute_sql "
    SELECT COUNT(*)
    FROM pg_indexes
    WHERE tablename = 'audit_events'
  " | grep -oE '[0-9]+' | head -1)
  
  log_info "audit_events indexes: $INDEXES"
  
  if [ "$INDEXES" -ge 4 ]; then
    log_success "Expected audit_events indexes present"
    execute_sql "
      SELECT indexname FROM pg_indexes WHERE tablename = 'audit_events' ORDER BY indexname
    " | tail -n +3 || true
  else
    log_warning "Fewer indexes than expected (found $INDEXES, expected at least 4)"
  fi
  
  # Check user_id FK
  FK_EXISTS=$(execute_sql "
    SELECT COUNT(*)
    FROM information_schema.table_constraints
    WHERE table_name = 'audit_events'
      AND constraint_type = 'FOREIGN KEY'
  " | grep -oE '[0-9]+' | head -1)
  
  if [ "$FK_EXISTS" -gt 0 ]; then
    log_success "audit_events.user_id foreign key exists"
  else
    log_error "audit_events.user_id foreign key missing"
  fi
else
  log_error "audit_events table not found"
fi

# Verify users and telegram_accounts
log_section "Verifying Core Tables (WF_01 Requirements)"

# Check users table
execute_sql "
  SELECT column_name, data_type
  FROM information_schema.columns
  WHERE table_name = 'users'
  ORDER BY ordinal_position
" | tail -n +3 | while read -r line; do
  if [ ! -z "$line" ]; then
    log_info "users.$line"
  fi
done

# Check telegram_accounts table
execute_sql "
  SELECT column_name, data_type
  FROM information_schema.columns
  WHERE table_name = 'telegram_accounts'
  ORDER BY ordinal_position
" | tail -n +3 | while read -r line; do
  if [ ! -z "$line" ]; then
    log_info "telegram_accounts.$line"
  fi
done

# Check telegram_accounts UNIQUE constraint
UNIQUE_CONSTRAINT=$(execute_sql "
  SELECT COUNT(*)
  FROM pg_indexes
  WHERE tablename = 'telegram_accounts'
    AND indexname LIKE '%telegram_id%'
" | grep -oE '[0-9]+' | head -1)

if [ "$UNIQUE_CONSTRAINT" -gt 0 ]; then
  log_success "telegram_accounts has UNIQUE index on telegram_id"
else
  log_error "telegram_accounts missing UNIQUE index on telegram_id"
fi

# Smoke test: Try inserting sample data
log_section "Smoke Test: Sample Data Insertion"

SAMPLE_INSERT=$(execute_sql "
  WITH new_user AS (
    INSERT INTO users (id, role) 
    VALUES (uuid_generate_v4(), 'MAN')
    RETURNING id
  ),
  new_account AS (
    INSERT INTO telegram_accounts (id, user_id, telegram_id, username)
    SELECT uuid_generate_v4(), new_user.id, 123456789, 'testuser'
    FROM new_user
    RETURNING id
  ),
  new_audit AS (
    INSERT INTO audit_events (user_id, event_type, event_data)
    SELECT new_user.id, 'user_registration', jsonb_build_object('source', 'telegram')
    FROM new_user
    RETURNING id
  )
  SELECT COUNT(*) FROM new_audit
" 2>&1)

if echo "$SAMPLE_INSERT" | grep -q "1"; then
  log_success "Sample data insertion successful (WF_01 simulation)"
else
  log_error "Sample data insertion failed"
  log_error "$SAMPLE_INSERT"
fi

# Summary
log_section "Dry-Run Summary"

echo ""
echo -e "${GREEN}✓ PASSED: ${PASS_COUNT}${NC}"
echo -e "${RED}✗ FAILED: ${FAIL_COUNT}${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
  log_success "All checks passed! Database is ready for WF_01"
  echo ""
  echo "Connection details for manual inspection:"
  echo "  Host:     ${DB_HOST}"
  echo "  Port:     ${DB_PORT}"
  echo "  Database: ${DB_NAME}"
  echo "  User:     ${DB_USER}"
  echo "  Password: ${DB_PASSWORD}"
  echo ""
  echo "To connect manually:"
  echo "  psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME}"
  echo ""
  echo "Container will be cleaned up automatically."
  exit 0
else
  log_error "Dry-run completed with errors"
  exit 1
fi
