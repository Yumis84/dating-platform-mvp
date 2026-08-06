# Infrastructure for local development (Dating Platform MVP)

This folder contains docker-compose configuration and environment variable examples
for bootstrapping a local development environment that mirrors core services used
by the MVP: PostgreSQL, n8n (workflow engine) and a migration helper container.

Files
- docker-compose.yml — service definitions for postgres, n8n, and migrator.
- .env.example — example environment variables you should copy to infrastructure/.env
- README.md — this file.

Quick start
-----------
1. Copy environment file and edit placeholders:
   cp .env.example .env
   # Edit .env and replace placeholder values with secure local values.

2. Start PostgreSQL (in background):
   docker-compose -f docker-compose.yml up -d postgres

3. Run migrations (once DB is ready):
   # Run the migrate tool against the postgres container
   docker-compose -f docker-compose.yml run --rm \
     -e DATABASE_URL="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}?sslmode=disable" \
     migrator migrate -path=/migrations -database "postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}?sslmode=disable" up

   # Note: The migrator image used is migrate/migrate and expects the SQL migration files
   # to be mounted at /migrations inside the container. Migrations should be numbered
   # and idempotent where possible.

4. Start n8n service:
   docker-compose -f docker-compose.yml up -d n8n

5. Open n8n UI at http://localhost:${N8N_PORT} and configure credentials (Postgres, Telegram, AI)

Notes
-----
- This docker compose is intentionally minimal for local development. In CI/production
  you will want to manage secrets, volumes, and health checks more robustly.
- Do NOT commit actual credentials. Keep them in a local .env that is ignored by git.
