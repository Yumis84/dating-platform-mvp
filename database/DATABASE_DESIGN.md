# Database design — User registration module

This document describes the initial database design for the user registration module of Dating Platform MVP.

Tables and purpose
------------------
- users
  - Core user entity tied to the application's concept of a user.
  - Fields: id (UUID), telegram_id (BIGINT, unique), username, first_name, last_name, role, status, created_at, updated_at.
  - Holds minimal personal information required for the MVP. No passwords, emails, or sensitive PII are stored.

- telegram_accounts
  - Stores Telegram-specific account linkage and metadata.
  - Rationale: separating Telegram account data allows linking multiple Telegram accounts to one application user in future, storing init_data_hash (to verify Telegram WebApp init payload changes), and tracking last_login_at.
  - Fields: id (UUID), user_id (FK -> users.id), telegram_id (BIGINT), init_data_hash (TEXT), last_login_at (TIMESTAMP).

- audit_events
  - Stores audit trail entries related to user activities (registration, login, role changes, status updates, etc.).
  - Use JSONB for flexible event payloads.
  - Fields: id (UUID), user_id (UUID), event_type (TEXT), event_data (JSONB), created_at (TIMESTAMP).

Relationships
-------------
- users (1) <-> (0..N) telegram_accounts
  - One user may have multiple Telegram account links in future; current MVP will typically have one.
- audit_events link to users via user_id (nullable) to allow system-wide events not tied to a user if needed.

Design choices
--------------
- UUID primary keys
  - Use UUID (uuid_generate_v4()) for all primary keys to avoid predictable integer IDs and facilitate cross-environment merges and migrations.
  - UUIDs simplify merging datasets between environments and sharding if needed later.

- telegram_id stored separately
  - telegram_id is stored both on users (for quick lookup and unique constraint) and in telegram_accounts (to support multiple accounts and to keep account-specific metadata separate).
  - Keeping telegram_id on users simplifies fast lookups by Telegram ID (common operation in Telegram-first architecture).

- JSONB for event_data
  - Audit events can have varying payloads; JSONB allows flexible storage while keeping queryability.

Future migration and portability
-------------------------------
- All schema changes will be applied via versioned migrations stored in database/migrations.
- For data migrations (e.g., splitting users or merging accounts), versioned migration scripts will include explicit data transformation steps with backups.
- Consider adding a migration runner (Flyway, Liquibase, or an ORM-based tool) integrated into CI to apply migrations automatically in test/staging environments.

Planned tables for later stages
------------------------------
- profiles — public user profile details (bio, photos references, preferences).
- matches — records of matching proposals and statuses.
- chat_sessions / messages — chat session metadata and message storage (might be split between Postgres for metadata and object storage for media).
- meetings — scheduling, confirmation, and location hints (no sensitive PII stored).
- system_events / logs — cross-service event logs and operational telemetry.
- admin_users / roles — administrative access control beyond basic role on users.

Privacy and minimal data
------------------------
- The schema intentionally avoids storing emails, passwords, or sensitive identification documents.
- Only minimal personal data needed for the app flows is stored (names, Telegram identifiers).

