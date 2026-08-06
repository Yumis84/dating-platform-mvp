# Catalog API Design

This document describes the HTTP API surface used by the WebApp (Telegram WebApp) to interact with the catalog via n8n webhooks and PostgreSQL.

Architecture
------------
WebApp
  ↓ (HTTP)
n8n Webhook
  ↓ (Postgres queries)
PostgreSQL (profiles, profile_photos, favorites, profile_views, profile_search_events)

Endpoints / Methods
-------------------
- GET catalog (POST /webhook/profile-catalog)
  - Input: user_id, filters, limit, offset
  - Output: { items: [...], total, limit, offset }
  - Notes: Returns only profiles with status = 'ACTIVE'.

- VIEW profile (POST /webhook/profile-view)
  - Input: viewer_user_id, profile_id
  - Output: profile card fields (id, name, age, city, avatar_file_id, description)
  - Side effect: records profile_views

- ADD favorite / REMOVE favorite / TOGGLE (POST /webhook/favorites)
  - Input: user_id, profile_id, action (ADD|REMOVE|TOGGLE)
  - Output: { success: true, favorite: true|false }
  - Side effect: inserts/deletes favorites and creates audit_event

Security and privacy
--------------------
- Responses must never include telegram_id or other private contact details.
- Authentication should be handled by the WebApp layer (not covered here). n8n webhooks should be protected by a token or checked origin in production.

Pagination and limits
---------------------
- Default limit is 25, max limit is 50. Use offset for paging.
- Returned payload includes total count for client‑side pagination.

Analytics
---------
- profile_search_events captures search filters for analytics.
- profile_views captures view events for engagement metrics.

