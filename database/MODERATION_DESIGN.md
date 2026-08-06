# Moderation design — profiles

Overview
--------
This document describes the design of the moderation subsystem for user profiles. It complements the AI profile creation flow and the Admin Panel design. The moderation subsystem handles automated (AI) and manual (ADMIN) checks and records decisions/audit trails.

Core tables
-----------
1) profile_moderation
- Purpose: stores moderation tasks/records for a profile. Can be created by the AI agent (automatic checks) or by an admin (manual review).
- Key fields:
  - id (UUID)
  - profile_id (FK -> profiles.id)
  - moderator_type (AI | ADMIN)
  - status (PENDING | APPROVED | REJECTED)
  - reason (TEXT) — optional human-readable reason
  - moderation_data (JSONB) — structured metadata, e.g., detected policy violations, confidence scores, model outputs
  - created_at, updated_at
- Notes: multiple moderation records may exist per profile (e.g., AI pre-check + subsequent admin decision).

2) moderation_rules
- Purpose: store configurable rules for automated moderation and for admin guidance.
- Key fields:
  - id (UUID)
  - rule_name (TEXT)
  - description (TEXT)
  - severity (LOW | MEDIUM | HIGH | CRITICAL)
  - enabled (BOOLEAN)
  - created_at
- Notes: rules can be used by the AI agent to map detected issues to severity and to build moderation_data.

3) moderation_history
- Purpose: immutable audit/log of moderation-related actions and profile status transitions.
- Key fields:
  - id (UUID)
  - profile_id (FK -> profiles.id)
  - action (TEXT) — e.g., 'ai_check', 'admin_approve', 'admin_reject', 'auto_reject'
  - old_status, new_status
  - actor_type (AI | ADMIN | SYSTEM)
  - actor_id (UUID) — optional link to admin user id or AI run/session id
  - comment (TEXT)
  - created_at
- Notes: Used for tracing decisions and for compliance/appeals.

Flow (high level)
------------------
1. Profile creation via AI flow results in profiles.status = DRAFT.
2. AI pre-checks run (synchronous or asynchronous) and create a profile_moderation record with moderator_type = 'AI' and status = 'PENDING' or with a preliminary decision. Detected issues are placed in moderation_data.
3. If AI signals high severity issues (CRITICAL) the profile may be auto-rejected; otherwise a human moderator reviews PENDING items.
4. Admin reviews via Admin Panel (not implemented here) and sets decision: APPROVED or REJECTED. Each decision creates an entry in moderation_history and an updated profile_moderation record.
5. On APPROVED: profiles.status -> ACTIVE; on REJECTED: profiles.status -> REJECTED or BLOCKED per business rules.

Roles
-----
- AI
  - Performs primary automated checks using moderation_rules and models.
  - Can create profile_moderation records and populate moderation_data with findings.
  - May auto-approve or auto-reject based on configured thresholds.

- ADMIN
  - Performs manual review of PENDING profiles and makes final decisions.
  - Can override AI decisions and add comments.

Indexes, FKs and constraints
---------------------------
- profile_moderation.profile_id -> FK to profiles(id), ON DELETE CASCADE.
- moderation_history.profile_id -> FK to profiles(id), ON DELETE CASCADE.
- Indexes added for profile_id, status (for efficient lookup of PENDING items), and actor_id.
- CHECK constraints added for enumerated fields (moderator_type, status, actor_type, severity).

Operational notes
-----------------
- Retention: keep moderation_history for compliance; consider archiving older records to long-term storage if necessary.
- Queueing: implement an efficient queue or materialized view for admin UI to fetch PENDING items (e.g., ORDER BY created_at LIMIT N).
- Idempotency: ensure moderation actions are idempotent; use unique constraints on moderation tasks if needed to avoid duplicates.

Security and privacy
--------------------
- moderation_data may contain sensitive analysis results; restrict access to admin roles and store it encrypted at rest if required.
- Do NOT store user contact details or payment information in moderation tables.

