# Catalog design — Profiles catalog

Overview
--------
The catalog module provides read-only access to public, ACTIVE profiles for browsing by users (primarily men in MVP flows). The catalog is powered by the `profiles` table and supports simple filters and analytics.

Source of truth
---------------
- profiles (only rows with status = 'ACTIVE' are visible in catalog)

Key concepts
------------
- profile_views: records each time a user opens a profile. Used for analytics, rate limiting, and engagement metrics.
- favorites: allows users to mark profiles as favorite. Enforced unique per (user_id, profile_id).
- profile_search_events: logs search filters and parameters for analytics and ranking improvements.

Typical scenario (male user)
----------------------------
Registration
↓
Choose city / filters in WebApp
↓
Request list of ACTIVE profiles (WF_05)
↓
Show profile card
↓
Open profile
↓
Record view in profile_views (WF_06)
↓
Optionally add to favorites

Privacy and exposed fields
-------------------------
Responses must NOT include:
- telegram_id
- internal user IDs beyond profile.id
- any private PII (contacts, emails, payment info)

Future transition
-----------------
- n8n + PostgreSQL → Telegram WebApp: n8n will serve as a thin backend for the WebApp and Telegram interactions, querying Postgres and returning JSON payloads.
- Later improvements may include full-text search, ranking, and recommendations (separate modules).

Indexes and performance
-----------------------
- Indexes added for profile_views.profile_id, favorites user/profile, and search events created_at.
- For production, consider composite indexes for common filter combinations (city + age_range).

