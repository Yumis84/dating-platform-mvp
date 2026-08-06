# WF_06: Profile View

Trigger: Webhook (from WebApp)

Purpose
-------
Record that a user viewed a profile and return profile card data for display.

Input
-----
- viewer_user_id (UUID)
- profile_id (UUID)

Processing
----------
1. Insert a record into profile_views (viewer_user_id, profile_id).
2. Query profile details (id, name, age, city, avatar_file_id, description) and return as JSON.

Security
--------
Do not return telegram_id or other private fields.

