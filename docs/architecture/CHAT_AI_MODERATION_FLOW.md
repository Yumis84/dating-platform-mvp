# Chat AI Moderation Flow

Primary (pre‑moderation) flow
-----------------------------
Message (user)  
↓
n8n Message Router (WF_09) — basic validation, dedup, quick heuristics
↓
Insert into messages table and create message_moderation_queue row (status = PENDING)
↓
WF_12_AI_MESSAGE_MODERATION
  - Load message
  - Send content to AI moderation model (external API)
  - Receive verdict (APPROVED|BLOCKED|REVIEW, score, flags)
  - Persist verdict to message_moderation_queue
↓
If APPROVED → insert into message_delivery_queue (PENDING) → WF_11 delivers to Telegram
If REVIEW → notify moderator; hold or deliver based on policy
If BLOCKED → do not deliver; create chat_report + audit_event

Alternative (post‑moderation) flow
----------------------------------
Message (user)  
↓
n8n Message Router (WF_09) — quick validation only
↓
Insert into messages table and immediately into message_delivery_queue (PENDING)
↓
WF_11 delivers message quickly
↓
WF_12 processes message asynchronously; on BLOCKED verdict → take remediation actions (hide message, escalate, create chat_report, possible retroactive block)

Tradeoffs
--------
- Pre‑moderation increases safety at the cost of delivery latency; suitable for high‑risk contexts.
- Post‑moderation favors low latency and user experience but exposes users to potential short‑lived harm.
- Hybrid approaches allow low latency for most messages and more strict checks for flagged users/content.
