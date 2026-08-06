# Chat Reliability Design

Purpose
-------
This document outlines reliability and safety improvements for the Anonymous Chat module. It focuses on ensuring messages are delivered reliably to external APIs (Telegram), preventing duplicates, implementing retries and backoff, protecting against abusive traffic and integrating automated moderation.

Problems addressed
------------------
- The Telegram API (or other delivery channels) can be transiently unavailable or rate limited, causing message loss unless retried.
- Direct synchronous delivery during user request can cause user‑facing errors if external API fails.
- Duplicate updates from Telegram or network retransmits can lead to duplicate messages.

Outbox pattern (message_delivery_queue)
----------------------------------------
- Write the message to the primary messages table in the same transaction as the user action, then insert a row into message_delivery_queue (outbox).
- A separate delivery worker polls message_delivery_queue for PENDING items scheduled for sending and performs delivery to Telegram API.
- This decoupling ensures user requests are fast and durable even if Telegram is down.

Retry and backoff
-----------------
- Each queue row tracks attempts and last_error. Worker increments attempts and sets next scheduled_at according to backoff strategy (e.g., exponential backoff: 1m, 5m, 30m, 2h).
- After a configured max_attempts (e.g., 5), mark the row as FAILED and notify admins or create a moderation event to investigate.

Handling Telegram errors
------------------------
- Distinguish transient errors (5xx, timeouts, rate limits) from permanent errors (403 forbidden, chat not found).
- For transient errors, schedule retry; for permanent errors, mark FAILED and include actionable last_error.
- Respect Telegram rate limit headers and throttle worker concurrency accordingly.

Duplicate protection
--------------------
- Use deduplication keys from incoming updates (dedup_key) stored in message metadata to avoid double insertion.
- For outgoing delivery, worker should guard against re-sending the same message if a prior send attempt actually succeeded but the confirmation was lost; use sent_at and external message_id metadata to identify success.

Rate limiting and anti‑spam
--------------------------
- message_rate_limits table provides a persisted counter per user/action window to enforce limits on messages per minute/hour/day.
- For high throughput environments, complement with in-memory counters (Redis, token bucket) to avoid DB contention.
- On hitting thresholds, reject new messages at workflow validation stage and create audit_events.

Integration with AI moderation
------------------------------
- The worker or a separate moderation worker can send message text to AI moderation (WF_04) before or after delivery depending on policy (sync pre‑filter or async post‑filter).
- If AI flags a message as high risk, action options: block delivery, mark message hidden, escalate to admin (create chat_moderation_events and chat_reports entries).
- Keep chat_moderation_events to store verdicts and actions taken for auditability.

Observability and alerting
--------------------------
- Track metrics: queue depth, failure rate, average delivery latency, attempts distribution.
- Alert on growing queue depth, surge in FAILED rows, or spike in errors from Telegram API.

Retention and privacy
---------------------
- Delivery queue and moderation events contain minimal contextual data and message_id references. Do not duplicate full message content unless necessary for moderation — prefer referencing messages table.
- Apply retention policy to delivery queue (archive old FAILED items) and moderation events as per data retention rules.

