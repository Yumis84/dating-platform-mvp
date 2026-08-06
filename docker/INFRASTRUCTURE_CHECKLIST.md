# Infrastructure checklist

Use this checklist when validating the local Docker development environment for the Dating Platform MVP.

- [ ] Docker установлен
- [ ] docker compose работает
- [ ] PostgreSQL запускается
- [ ] pgAdmin подключается
- [ ] n8n запускается
- [ ] WebApp nginx отвечает
- [ ] volumes сохраняются после перезапуска
- [ ] .env настроен
- [ ] секреты не находятся в Git

Instructions:
1. Copy .env.example to .env and fill required values (do NOT commit .env with real secrets).
2. Start services: from repo root `docker-compose -f docker/docker-compose.yml up -d` or `cd docker && docker-compose up -d`.
3. Check service health and logs: `docker-compose -f docker/docker-compose.yml ps` and `docker-compose -f docker/docker-compose.yml logs -f <service>`.
4. Validate each checklist item and mark when completed.
