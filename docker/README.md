Docker development environment for Dating Platform MVP

Purpose
-------
This directory contains Docker Compose configuration and instructions to bring up a local development environment for the project. The aim is to provide a reproducible environment for development and integration testing prior to production deployment.

Services included
----------------
- postgres — Primary relational database (PostgreSQL).
- pgadmin — Web UI for managing PostgreSQL (dpage/pgadmin4).
- n8n — Workflow/orchestration engine for integrations and automation.
- webapp (nginx) — Static server for the Telegram WebApp (serves files from /webapp).
- adminer — Lightweight DB management UI (optional).

All services are attached to a single named Docker network (dating_app_network) and use named volumes for persistent data.

Quick start
-----------
1. Copy example env file and fill secrets (do NOT commit real secrets):
   cp .env.example .env

2. Start the stack (from repository root):
   docker compose up -d

3. Check services:
   docker compose ps

How to use
---------
1. Copy example env file and fill secrets (do NOT commit real secrets):
   cp .env.example .env
   # Edit .env and set real values (or use a secrets manager)

2. Start the stack (from repository root):
   docker-compose -f docker/docker-compose.yml up -d

   Or from the docker/ directory:
   cd docker && docker-compose up -d

3. Stop the stack:
   docker-compose -f docker/docker-compose.yml down

4. Recreate after changes / update images:
   docker-compose -f docker/docker-compose.yml pull
   docker-compose -f docker/docker-compose.yml up -d --force-recreate --remove-orphans

Connecting to services
---------------------
- PostgreSQL
  - Host: localhost
  - Port: ${POSTGRES_PORT:-5432}
  - DB: value from POSTGRES_DB
  - User: value from POSTGRES_USER
  - Password: value from POSTGRES_PASSWORD
  Use psql or a DB admin (pgAdmin / Adminer).

- pgAdmin
  - URL: http://localhost:8080
  - Login with PGADMIN_EMAIL and PGADMIN_PASSWORD (set in .env)
  - In pgAdmin, create a new server connection pointing to host `postgres` (container name) on port 5432, or to `localhost` when connecting from the host machine.

- Adminer
  - URL: http://localhost:8081
  - Use database credentials from .env

- n8n
  - URL: http://localhost:5678
  - If basic auth is enabled, use N8N_BASIC_AUTH_USER / _PASSWORD

Where to store secrets
---------------------
- Do NOT commit .env with real credentials.
- Recommended options:
  - Use Docker secrets for production deployments.
  - Use CI/CD secret storage (GitHub Secrets, GitLab CI variables) for automated builds.
  - For local development, keep a local .env ignored by Git (.gitignore) with credentials.

Notes and recommendations
------------------------
- Ports in docker-compose are configured for local development. For production, prefer an orchestration platform (Kubernetes) and external secret management.
- The webapp service uses a bind mount from ../webapp. Ensure webapp build artifacts are available in that folder before running in dev.
- n8n is configured to use Postgres as its DB. Credentials are read from environment variables.
- The compose file is intended as a developer starting point. Review and tighten security before exposing services publicly.

