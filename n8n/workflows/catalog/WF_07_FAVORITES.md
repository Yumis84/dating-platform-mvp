# WF_07: Favorites (Add/Remove/Toggle)

Trigger: Webhook (from WebApp)

Purpose
-------
Add, remove or toggle favorite (bookmark) for a given profile by a user. The workflow ensures the user exists and the profile is ACTIVE before modifying favorites and records an audit_event for traceability.

Input
-----
- user_id (UUID)
- profile_id (UUID)
- action (ADD | REMOVE | TOGGLE)

Response
--------
Returns JSON:
{
  "success": true,
  "favorite": true|false
}

Behavior
--------
- ADD: create favorites record if not exists.
- REMOVE: delete favorites record if exists.
- TOGGLE: if exists -> remove, otherwise -> add.

Notes
-----
- Workflow must validate that the user exists and that the profile exists and has status = 'ACTIVE'.
- Do NOT return telegram_id or other private data.
- Use audit_events to log the action.
- No credentials or secrets are stored in the exported JSON; bind Postgres credentials in n8n UI after import.
