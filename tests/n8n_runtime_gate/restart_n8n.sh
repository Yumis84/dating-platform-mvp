#!/usr/bin/env bash
set -euo pipefail

ROOT="${GITHUB_WORKSPACE:-$(cd "$(dirname "$0")/../.." && pwd)}"
N8N_IMAGE="${N8N_IMAGE:-docker.n8n.io/n8nio/n8n:2.34.5}"
TARGET_URL="${1:-http://127.0.0.1:5678/webhook/runtime-gate/woman-profile}"
DATA_DIR="$ROOT/.runtime/n8n-data"

: "${N8N_ENCRYPTION_KEY:?N8N_ENCRYPTION_KEY is required}"

mkdir -p "$DATA_DIR"
chmod 0777 "$DATA_DIR"

docker rm -f n8n-runtime-gate >/dev/null 2>&1 || true

docker run -d \
  --name n8n-runtime-gate \
  --network host \
  -e N8N_HOST=127.0.0.1 \
  -e N8N_LISTEN_ADDRESS=127.0.0.1 \
  -e N8N_PORT=5678 \
  -e N8N_PROTOCOL=http \
  -e N8N_SECURE_COOKIE=false \
  -e N8N_ENCRYPTION_KEY="$N8N_ENCRYPTION_KEY" \
  -e N8N_DIAGNOSTICS_ENABLED=false \
  -e N8N_PERSONALIZATION_ENABLED=false \
  -e N8N_VERSION_NOTIFICATIONS_ENABLED=false \
  -e N8N_BLOCK_ENV_ACCESS_IN_NODE=false \
  -e N8N_RUNNERS_MODE=internal \
  -e EXECUTIONS_DATA_SAVE_ON_SUCCESS=all \
  -e EXECUTIONS_DATA_SAVE_ON_ERROR=all \
  -e EXECUTIONS_DATA_PRUNE=false \
  -e WEBHOOK_URL=http://127.0.0.1:5678/ \
  -e WF_03_TRIGGER_URL="$TARGET_URL" \
  -e DEEPSEEK_API_URL=http://127.0.0.1:18080/v1/chat/completions \
  -e DEEPSEEK_API_KEY=runtime-gate-dummy \
  -e DEEPSEEK_MODEL=runtime-gate-mock \
  -v "$DATA_DIR:/home/node/.n8n" \
  "$N8N_IMAGE" >/dev/null

for _ in $(seq 1 60); do
  if curl --silent --fail http://127.0.0.1:5678/healthz >/dev/null 2>&1; then
    echo "n8n ready: $TARGET_URL"
    exit 0
  fi
  sleep 1
done

echo "n8n failed to become healthy" >&2
docker logs n8n-runtime-gate >&2 || true
exit 1
