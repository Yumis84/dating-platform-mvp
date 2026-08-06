# Chat Reliability Flow

High level flow
---------------
User message (WebApp / Telegram)
  ↓
n8n (Message Router WF_09)
  ↓
messages (persisted)
  ↓
message_delivery_queue (outbox row created)
  ↓
Message Delivery Worker (WF_11) polls PENDING items
  ↓
Telegram Bot API (send)
  ↓
Delivery status updated (SENT / FAILED)
  ↓
Audit (audit_events) and moderation (chat_moderation_events if flagged)

Failure and retry
-----------------
- On transient failures, WF_11 reschedules the item with an increased attempts count and updated scheduled_at according to backoff policy.
- On permanent failures or max attempts exceeded, WF_11 marks the item FAILED and generates an audit_event and admin notification.

Moderation integration
----------------------
- Messages can be sent to AI moderation either before queuing for delivery (sync pre-filter) or after delivery (async monitoring). The architecture supports both approaches; choose policy based on acceptable moderation latency.

Monitoring
----------
- Expose metrics for queue length, items processed per minute, failure rate, average attempts. Alert on threshold breaches.
