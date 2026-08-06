# WF_05: Profile Catalog (updated — pagination + filters)

Trigger: Webhook (from WebApp)

Purpose
-------
Return a paginated JSON list of ACTIVE profiles matching optional filters. The workflow also logs the search event for analytics.

Input
-----
- user_id (UUID)
- filters (JSON) — optional, e.g., { "city": "Moscow", "age_from": 25, "age_to": 35 }
- limit (int) — maximum number of items to return (max 50)
- offset (int) — pagination offset

Processing
----------
1. Record search filters into profile_search_events (analytics).
2. Query profiles WHERE status = 'ACTIVE' and apply filters (city, age_from, age_to). Apply limit/offset.
3. Return a JSON object with items array and total count.

Response
--------
{
  "items": [ ... ],
  "total": 123,
  "limit": 25,
  "offset": 0
}
