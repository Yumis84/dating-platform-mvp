# WF_12: AI Message Moderation

Trigger: Webhook or Manual invocation with message_id

Purpose
-------
Send message content to an AI moderation model, record the verdict and take actions depending on the outcome (APPROVED, REVIEW, BLOCKED).

Flow summary
------------
1. Receive input: message_id (UUID).
2. Load message (content, chat_id, sender_id) from messages table.
3. Send message text (and safe metadata) to AI moderation API (HTTP Request node placeholder).
4. Parse AI response into { verdict, score, flags, reason }.
5. Insert / update message_moderation_queue row with results and timestamps.
6. If BLOCKED:
   - Do not forward message to delivery queue.
   - Create chat_reports entry (reporter = system), set status OPEN.
   - Create audit_event.
   - Optionally set chat_sessions.status = 'BLOCKED' for severe cases.
7. If REVIEW:
   - Notify moderation channel with context (last N messages) and keep moderation row in REVIEW state.
8. If APPROVED:
   - Insert a row into message_delivery_queue (PENDING) for WF_11 to pick up (if pre‑moderation is used).

Notes
-----
- Use placeholders for AI credentials in exported JSON; bind credentials in n8n UI.
- Ensure minimal PII in payload sent to AI (strip phone numbers/emails if policy demands), or use a hardened moderation model with redaction.
