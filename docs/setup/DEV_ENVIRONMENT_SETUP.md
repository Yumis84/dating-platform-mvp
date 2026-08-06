# Development environment setup

This document describes how to boot the local development environment for the Dating Platform MVP,
apply database migrations, and configure n8n and external credentials.

Prerequisites
-------------
- Docker and Docker Compose installed on your machine
- git and basic familiarity with containers

1) Prepare environment file
---------------------------
Copy the example environment file and edit placeholders:

  cp infrastructure/.env.example infrastructure/.env
  # Edit infrastructure/.env and replace placeholder values with secure local values.

2) Start core services
----------------------
Start PostgreSQL first so migrations can run:

  docker-compose -f infrastructure/docker-compose.yml up -d postgres

Wait for Postgres to be ready (check logs):

  docker-compose -f infrastructure/docker-compose.yml logs -f postgres

3) Apply database migrations (001..007)
--------------------------------------
We use the migrate/migrate tool inside the provided migrator service. From the repository root run:

  docker-compose -f infrastructure/docker-compose.yml run --rm \
    -e DATABASE_URL="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}?sslmode=disable" \
    migrator migrate -path=/migrations -database "$DATABASE_URL" up

Notes:
- Ensure the folder database/migrations contains migration files named in sequence: 001_*.sql .. 007_*.sql.
- If a migration fails, inspect the SQL file, fix, and retry. For safety run migrations on a fresh DB in dev.

4) Start n8n
-----------

  docker-compose -f infrastructure/docker-compose.yml up -d n8n

Open n8n at http://localhost:${N8N_PORT} (default 5678) and log in using the credentials from the .env file.

5) Import n8n workflows
-----------------------
You can import workflows via the n8n UI (Settings → Workflows → Import) or by using the mounted folder:
- Copy JSON workflow templates into n8n/workflows/ and then use the n8n CLI or UI to import.

Workflows expected for MVP (to verify):
WF_01 registration
WF_02 role selection
WF_03 AI profile creation
WF_04 profile moderation
WF_05 catalog
WF_06 profile view
WF_07 favorites
WF_08 create chat
WF_09 message router
WF_10 block/report
WF_11 delivery worker
WF_12 message moderation

6) Set up Telegram Bot and AI provider credentials
-------------------------------------------------
- Telegram: create a bot with @BotFather, obtain the token and set TELEGRAM_BOT_TOKEN in infrastructure/.env
- Moderation/notification chat: set MODERATION_CHAT_ID to the Telegram chat id where moderators will receive REVIEW alerts

- AI Provider: obtain API key and endpoint for your moderation model; set AI_API_KEY and AI_API_URL in infrastructure/.env

7) Environment variables
------------------------
See infrastructure/.env.example for the complete list of variables. Do not commit real credentials.

8) Useful commands
------------------
- Re-run migrations:
  docker-compose -f infrastructure/docker-compose.yml run --rm \
    -e DATABASE_URL="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}?sslmode=disable" \
    migrator migrate -path=/migrations -database "$DATABASE_URL" up

- Stop services:
  docker-compose -f infrastructure/docker-compose.yml down

- Remove volumes (will delete DB data):
  docker-compose -f infrastructure/docker-compose.yml down -v

Compatibility
-------------
This setup is designed to be compatible with the current project architecture and migration ordering:
users → profiles → moderation → catalog → chat → reliability → message moderation

If you need automation of importing workflows or running tests after migrations, consider adding a small script or CI job to run:
- docker-compose up postgres
- run migrate
- docker-compose up n8n

