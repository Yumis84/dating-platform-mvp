# Profile design — AI-assisted profile creation (female flow focus)

Overview
--------
This document describes the database design for user profiles (profiles) and related tables used by the AI-assisted profile creation flow for the Dating Platform MVP.

Design goals
------------
- Store public user profile data with minimal PII.
- Keep media references (Telegram file_id) rather than binary blobs.
- Record AI session context to allow resuming conversations with the AI Agent.
- Provide auditable history of profile changes for moderation and rollback.
- Maintain clear separation between user identity (users table) and profile content (profiles table).

Tables
------
1) profiles
- Purpose: main public-facing user profile.
- Key columns:
  - id (UUID): PK.
  - user_id (UUID): FK -> users(id), cascade delete to remove profiles if user is removed.
  - display_name (TEXT)
  - age (INTEGER) — validated (14..120) via CHECK constraint.
  - city (TEXT)
  - description (TEXT)
  - avatar_file_id (TEXT) — Telegram file_id for avatar image reference.
  - status (VARCHAR) — lifecycle of profile: DRAFT, PENDING_MODERATION, ACTIVE, BLOCKED, ARCHIVED.
  - moderation_status (VARCHAR) — moderation workflow state: NOT_REQUIRED, PENDING, APPROVED, REJECTED.
  - created_at, updated_at (TIMESTAMPTZ)
- Indexes: user_id, status, moderation_status.

2) profile_photos
- Purpose: store additional photos for a profile using Telegram file_id references.
- Columns: id (UUID), profile_id (FK -> profiles), telegram_file_id (TEXT), sort_order (INT), created_at.
- Indexes: profile_id, telegram_file_id.

3) profile_ai_sessions
- Purpose: save AI conversation state and context while a user creates/edits a profile with the AI Agent.
- Columns: id (UUID), user_id (FK -> users, SET NULL on delete), session_status (IN_PROGRESS/COMPLETED/CANCELLED/FAILED), current_step (INT), ai_context (JSONB), created_at, updated_at.
- Indexes: user_id, session_status.

4) profile_fields_history
- Purpose: auditable history for profile field changes. Useful for moderation, rollback and analytics.
- Columns: id (UUID), profile_id (FK -> profiles), field_name (TEXT), old_value (JSONB), new_value (JSONB), changed_by (UUID refs users, SET NULL), created_at.
- Indexes: profile_id, changed_by.

Constraints and notes
---------------------
- UUIDs are used for PKs to support merging data between environments and to avoid predictable sequential IDs.
- Age has a CHECK constraint. Business may adjust allowed range later.
- Use JSONB for ai_context and field values to allow flexible or structured data from AI outputs.
- Use ON DELETE CASCADE for profile -> photos and history to keep data consistent when profiles are removed.
- For profile_ai_sessions and profile_fields_history consider a TTL / retention policy to bound storage usage.

Moderation and workflow
-----------------------
- Newly created profiles typically start in status = DRAFT and moderation_status = NOT_REQUIRED or PENDING depending on business rules.
- When ready for review, status becomes PENDING_MODERATION and moderation_status = PENDING. After review it moves to ACTIVE or REJECTED/ARCHIVED.

Privacy and limitations
----------------------
- Do NOT store contact details, payment data, passport/ID, or other sensitive PII in profiles.
- Media stored as Telegram file_id only; media binary storage should be handled via object storage if needed, referenced by stable URLs (out of scope here).

Indexes and performance
-----------------------
- Indexes added for common lookups (user_id, status) to support queries like "get active profiles in city X" (additional composite indexes may be added later for such queries).
- Consider materialized views for heavy search queries if using Postgres full-text search.

Migration notes
---------------
- Migration script 002_profiles_schema.sql creates tables and indexes. It includes checks and comments.
- Implement triggers for updated_at or handle updated_at updates in application logic.
- Before applying in staging/production, plan data retention, backups, and test the migration with sample data.

Future extensions (separate modules)
-----------------------------------
- profile_preferences — user preferences for matching (age range, distance, interests).
- photos storage migration helper to move Telegram files to dedicated object storage.
- moderation queues and review tools (admin panel tables).

