# Chat n8n Flow — Architecture and operational notes

Sequence
--------
Telegram Update / WebApp action
  ↓
n8n Trigger (Webhook / Telegram Trigger)
  ↓
Validation (profile/session/block checks)
  ↓
PostgreSQL (persist session/message/block/report)
  ↓
Telegram Bot API (deliver proxied message or notification)
  ↓
Audit (audit_events recording)

Error handling, retries and anti-spam
------------------------------------
- Each workflow node that performs DB or external calls should include error branches that:
  - Create an audit_event with error details
  - Retry transient errors (n8n retry settings) with backoff
  - On persistent failure, mark the session (or related task) for manual review and notify admins
- Rate limiting: implement checks in WF_09 (message router) and optionally in WF_08 to prevent mass session creation. Throttling decisions should produce audit_events.
- Deduplication: use dedup_key from incoming Telegram updates to avoid duplicate message inserts.

Failure scenarios and fallbacks
------------------------------
- If message delivery fails (Telegram API error), persist message and mark delivery failure in metadata; schedule retry attempts.
- If DB is unavailable, respond with a transient error to user and log the event; avoid message loss by queuing retry in an outbox (future work).
- If user is blocked mid-flight, return a friendly error to sender and create audit_event.

Security and privacy
--------------------
- Do not expose Telegram IDs or internal UUIDs to counterparties. All notifications use aliases and platform-mediated delivery.
- Sensitive operations (reading raw messages) must be audited.

Operational notes
-----------------
- Bind real credentials (Postgres, Telegram) in n8n UI after import of JSON templates. Do not check secrets into version control.
- Add monitoring/alerts for error rates on these workflows; moderate peak message throughput via rate limits and autoscaling.
