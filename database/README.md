# Database (PostgreSQL)

PostgreSQL is used as the primary relational database for the project. It will store the core domain data for the Dating Platform MVP, including but not limited to:

- chats — meta information about chat sessions between users/agents
- messages — individual messages exchanged in chats
- meetings — scheduling and confirmation information for meetings between users
- system_events — technical events, hooks, and integration events
- logs — application-level logs and audit trails (consider separate retention policies)

Notes
-----
- The physical database will be created when the infrastructure is run (container). However, the actual schema (tables, indexes, constraints) will NOT be created directly at this stage.
- Database schema changes and structure will be applied through migrations. A migrations folder exists at /database/migrations and will host sequential, versioned SQL migration scripts or a migration tool configuration (Flyway, Liquibase, or ORM migrations).
- Do NOT commit sensitive DB credentials. Use .env for local development (ignored by Git), and use secrets managers for production.

Recommended next steps
----------------------
- Define migration tooling (e.g., Flyway, Alembic, Goose, or ORM native migrations) and add an example migration runner in CI.
- Add schema design documents to /database (ER diagrams, table definitions) before writing migrations.
- Prepare backup and restore scripts in /backups for db-data volume.
