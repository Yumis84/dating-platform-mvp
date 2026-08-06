# WF_11: Message Delivery Worker

Trigger: Cron / Polling (periodic)

Purpose
-------
Process message_delivery_queue items in PENDING state, attempt delivery to Telegram API, update status to SENT or FAILED, increment attempts, record last_error, and create audit_events.

Flow summary
------------
1. Cron trigger runs every minute (configurable).
2. Query message_delivery_queue for PENDING rows with scheduled_at <= now(), limit batch size (e.g., 50).
3. For each item:
   - Load corresponding message (messages table) and determine delivery target (recipient Telegram chat id stored securely in metadata or resolved via mapping).
   - Attempt delivery via Telegram node (placeholder credential).
   - On success: update message_delivery_queue.status = 'SENT', set sent_at, increment attempts, record external metadata if needed.
   - On transient failure: increment attempts, set last_error, set scheduled_at = now() + backoff; if attempts exceed max_attempts mark as FAILED and notify admins.
   - On permanent failure: mark FAILED and notify admins.
4. Create audit_event for each delivery attempt and status change.

Notes
-----
- Worker must respect Telegram rate limits; implement concurrency limits in n8n or external orchestrator.
- Delivery target identifiers (telegram chat ids) must be fetched securely; do not expose them in responses to users.
