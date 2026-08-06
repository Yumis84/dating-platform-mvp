# Chat flow (architecture)

High-level sequence
-------------------
Telegram Client / WebApp (user)
        ↓
Telegram Bot or WebApp frontend
        ↓
n8n workflows (orchestrator)
        ↓
PostgreSQL (chat_sessions, messages, chat_blocks, chat_reports)
        ↓
Telegram Bot (deliver messages to recipient)

Scenarios
---------
1) Create chat
- User (man) opens female profile and presses "Начать чат".
- WebApp / Telegram sends request to n8n endpoint to create or resume chat.
- n8n validates profile is ACTIVE, checks rate limits, creates chat_sessions row with initiator_user_id and profile_id, returns chat_id.
- n8n notifies respondent (female) via Telegram bot or WebApp to accept or responds automatically depending on settings.

2) Send message
- User sends message via WebApp or Telegram (bot relays to n8n).
- n8n checks session status and block lists, applies rate limiting, persists message in messages table (sender_id, content, metadata), and forwards message to recipient through Telegram bot / WebApp.
- If session is flagged, the message may be queued for moderation.

3) Receive message
- Recipient's Telegram bot / WebApp receives the proxied message and shows it to the user. The sender is shown as an alias (no contact info).

4) Blocking
- If a participant presses "Block", n8n inserts a row into chat_blocks, updates chat_sessions.status = 'BLOCKED', and prevents further messages from the blocked user. An audit_event is created.

5) Report / Complaint
- Either participant can file a report (chat_reports). n8n creates a report row and triggers the AI moderation / admin review workflow (WF_04). The report is visible to moderators with context (recent messages). Moderators may change session status or take account actions.

Notes on delivery
-----------------
- Platform acts as a relay: Telegram message IDs may be stored for delivery attempts, but Telegram IDs must not be exposed in API responses returned to the other participant.
- For WebApp to Telegram bridging, n8n orchestrates inbound/outbound messages and manages retries/backoff for message delivery.

Security and privacy
--------------------
- Do not expose Telegram IDs, emails or phone numbers in messages or profile payloads.
- Limit who can access raw message content (moderators + system services) and provide auditing for such access.

Scaling considerations
----------------------
- Use indexing on chat_sessions.last_message_at and messages.created_at for querying active sessions and recent messages.
- Consider sharding or partitioning messages table if volume grows large. Implement archival pipeline for old messages.
