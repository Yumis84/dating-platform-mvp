# WF_05: Profile Catalog

Trigger: Webhook (from WebApp)

Purpose
-------
Return a JSON list of ACTIVE profiles matching optional filters. The workflow also logs the search event for analytics.

Input
-----
- user_id (UUID)
- filters (JSON) — optional, e.g., { "city": "Moscow", "min_age": 25, "max_age": 35 }

Processing
----------
1. Record search filters into profile_search_events (analytics).
2. Query profiles WHERE status = 'ACTIVE' and apply basic filters (city, age range).
3. Return a list of profiles with fields: id, name, age, city, avatar_file_id, description

Security
--------
Do NOT return telegram_id or any private data.

