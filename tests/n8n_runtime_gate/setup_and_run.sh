#!/usr/bin/env bash
set -euo pipefail

ROOT="${GITHUB_WORKSPACE:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$ROOT"

APPROVED_BASE_SHA="30ab0911bae090b668c74768da0e3ea33faf6f0c"
N8N_IMAGE="${N8N_IMAGE:-docker.n8n.io/n8nio/n8n:2.34.5}"
RUNTIME_DIR="$ROOT/.runtime"
GATE_DIR="$RUNTIME_DIR/n8n-gate"
N8N_DATA_DIR="$RUNTIME_DIR/n8n-data"
ARTIFACT_DIR="$RUNTIME_DIR/artifacts"
MOCK_LOG="$GATE_DIR/mock-ai.log"

: "${RUNTIME_GATE_PG_PASSWORD:?RUNTIME_GATE_PG_PASSWORD is required}"
: "${RUNTIME_GATE_HEADER_VALUE:?RUNTIME_GATE_HEADER_VALUE is required}"
: "${N8N_ENCRYPTION_KEY:?N8N_ENCRYPTION_KEY is required}"

mkdir -p "$GATE_DIR" "$N8N_DATA_DIR" "$ARTIFACT_DIR"
chmod 0777 "$N8N_DATA_DIR"

MOCK_PID=""
cleanup() {
  set +e
  docker logs n8n-runtime-gate >"$ARTIFACT_DIR/n8n-final.log" 2>&1 || true
  docker rm -f n8n-runtime-gate >/dev/null 2>&1 || true
  if [[ -n "$MOCK_PID" ]]; then
    kill "$MOCK_PID" >/dev/null 2>&1 || true
  fi
  if [[ -f "$MOCK_LOG" ]]; then
    cp "$MOCK_LOG" "$ARTIFACT_DIR/mock-ai.log"
  fi
  if [[ -f "$GATE_DIR/gate-report.json" ]]; then
    cp "$GATE_DIR/gate-report.json" "$ARTIFACT_DIR/gate-report.json"
  fi
  # Never expose generated credential material as an artifact.
  rm -f "$GATE_DIR/credentials.json"
}
trap cleanup EXIT

printf '\n== Repository safety preflight ==\n'
git merge-base --is-ancestor "$APPROVED_BASE_SHA" HEAD || {
  echo "Current test branch does not descend from approved PRE-RUNTIME commit $APPROVED_BASE_SHA" >&2
  exit 1
}
if [[ "${GITHUB_REF_NAME:-}" != "test/n8n-runtime-gate" ]]; then
  echo "Runtime gate may run only on test/n8n-runtime-gate; got ${GITHUB_REF_NAME:-unknown}" >&2
  exit 1
fi
echo "HEAD=$(git rev-parse HEAD)"
echo "approved_base=$APPROVED_BASE_SHA"

printf '\n== Disposable PostgreSQL preflight ==\n'
export PGHOST="${RUNTIME_GATE_PG_HOST:-127.0.0.1}"
export PGPORT="${RUNTIME_GATE_PG_PORT:-5432}"
export PGDATABASE="${RUNTIME_GATE_PG_DATABASE:-runtime_gate}"
export PGUSER="${RUNTIME_GATE_PG_USER:-runtime_gate}"
export PGPASSWORD="$RUNTIME_GATE_PG_PASSWORD"

DB_PREFLIGHT="$(psql -X -A -t -F '|' -c "SELECT current_database(),current_user,COALESCE(inet_server_addr()::text,'local'),inet_server_port(),version();")"
echo "$DB_PREFLIGHT"
DB_NAME="${DB_PREFLIGHT%%|*}"
REST="${DB_PREFLIGHT#*|}"
DB_USER="${REST%%|*}"
if [[ "$DB_NAME" != "runtime_gate" || "$DB_USER" != "runtime_gate" ]]; then
  echo "Refusing runtime gate: database/user is not the disposable runtime_gate identity" >&2
  exit 1
fi
if [[ "$PGHOST" != "127.0.0.1" && "$PGHOST" != "localhost" ]]; then
  echo "Refusing runtime gate: PostgreSQL host is not local runner ($PGHOST)" >&2
  exit 1
fi

printf '\n== Apply exact migration allowlist ==\n'
MIGRATIONS=(
  database/migrations/001_users_and_telegram_accounts_schema.sql
  database/migrations/002_profiles_schema.sql
  database/migrations/003_moderation_schema.sql
  database/migrations/004_catalog_schema.sql
  database/migrations/008_audit_events_schema.sql
  database/migrations/009_woman_profile_tz02_schema.sql
  database/migrations/010_man_search_context_preferences_schema.sql
)
for migration in "${MIGRATIONS[@]}"; do
  echo "Applying $migration"
  psql -X -v ON_ERROR_STOP=1 -f "$migration" >/dev/null
done

if psql -X -A -t -c "SELECT to_regclass('public.users') IS NOT NULL AND to_regclass('public.male_search_context') IS NOT NULL AND to_regclass('public.profile_prices') IS NOT NULL;" | grep -qx t; then
  echo "Disposable schema ready"
else
  echo "Disposable schema verification failed" >&2
  exit 1
fi

printf '\n== Build runtime-only workflow clones and credentials ==\n'
python tests/n8n_runtime_gate/build_runtime_gate.py
# The CLI container runs as the n8n `node` user, so the bind-mounted ephemeral file
# must be world-readable on this dedicated runner. It is deleted in cleanup and is
# never uploaded as an artifact; values are runtime-only and not production secrets.
chmod 0644 "$GATE_DIR/credentials.json"

printf '\n== Start deterministic AI/failure mock ==\n'
python -u tests/n8n_runtime_gate/mock_ai.py >"$MOCK_LOG" 2>&1 &
MOCK_PID=$!
for _ in $(seq 1 30); do
  if curl --silent --fail http://127.0.0.1:18080/healthz >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
curl --silent --fail http://127.0.0.1:18080/healthz >/dev/null

printf '\n== Initialize disposable n8n owner ==\n'
bash tests/n8n_runtime_gate/restart_n8n.sh "http://127.0.0.1:5678/webhook/runtime-gate/woman-profile"
OWNER_PASSWORD="$(python - <<'PY'
import secrets
print('Rtg!' + secrets.token_urlsafe(24) + 'aA1')
PY
)"
curl --silent --show-error --fail-with-body \
  -X POST http://127.0.0.1:5678/rest/owner/setup \
  -H 'Content-Type: application/json' \
  --data-binary "$(python - "$OWNER_PASSWORD" <<'PY'
import json,sys
print(json.dumps({
  'email':'runtime-gate@example.invalid',
  'firstName':'Runtime',
  'lastName':'Gate',
  'password':sys.argv[1],
}))
PY
)" >/dev/null
unset OWNER_PASSWORD

docker rm -f n8n-runtime-gate >/dev/null

cli_n8n() {
  docker run --rm \
    --network host \
    -e N8N_ENCRYPTION_KEY="$N8N_ENCRYPTION_KEY" \
    -e N8N_DIAGNOSTICS_ENABLED=false \
    -e N8N_PERSONALIZATION_ENABLED=false \
    -e N8N_VERSION_NOTIFICATIONS_ENABLED=false \
    -e N8N_RUNNERS_MODE=internal \
    -v "$N8N_DATA_DIR:/home/node/.n8n" \
    -v "$GATE_DIR:/data" \
    "$N8N_IMAGE" "$@"
}

printf '\n== Import runtime-only credentials and workflows ==\n'
cli_n8n import:credentials --input=/data/credentials.json
cli_n8n import:workflow --separate --input=/data/workflows

printf '\n== Publish runtime-only workflows inside disposable n8n ==\n'
for workflow_id in rtgBindProbe0001 rtgWf01Gate00001 rtgWf03Gate00001 rtgWf05Gate00001; do
  cli_n8n publish:workflow --id="$workflow_id"
done

python - "$N8N_DATA_DIR/database.sqlite" <<'PY'
import sqlite3,sys
expected={'rtgBindProbe0001','rtgWf01Gate00001','rtgWf03Gate00001','rtgWf05Gate00001'}
conn=sqlite3.connect(sys.argv[1])
rows=conn.execute("SELECT id,activeVersionId FROM workflow_entity WHERE id IN (?,?,?,?)", tuple(sorted(expected))).fetchall()
conn.close()
seen={wid for wid,active in rows if active}
if seen != expected:
    raise SystemExit(f"Runtime workflows were not all published: expected={sorted(expected)} published={sorted(seen)} rows={rows}")
print('Published runtime workflow IDs:', ', '.join(sorted(seen)))
PY

printf '\n== Start final disposable n8n runtime ==\n'
bash tests/n8n_runtime_gate/restart_n8n.sh "http://127.0.0.1:5678/webhook/runtime-gate/woman-profile"
docker exec n8n-runtime-gate n8n --version | tee "$ARTIFACT_DIR/n8n-version.txt"

for endpoint in \
  http://127.0.0.1:5678/webhook/runtime-gate/bind-probe \
  http://127.0.0.1:5678/webhook/runtime-gate/wf01 \
  http://127.0.0.1:5678/webhook/runtime-gate/catalog; do
  # 404 is acceptable for GET; this only verifies the server stays healthy before POST tests.
  curl --silent --output /dev/null --max-time 3 "$endpoint" || true
done

printf '\n== Execute R1-R14 in real n8n ==\n'
python tests/n8n_runtime_gate/run_gate.py

printf '\n== Runtime gate PASS ==\n'
