# WF_10: Chat Block & Report

Trigger: Webhook when a user files a report or presses Block in UI

Purpose
-------
Handle blocking and reporting actions: create chat_blocks records, optionally close the chat_session, create chat_reports, notify moderation channel, and log audit events.

Flow summary
------------
1. Receive request with reporter_user_id, chat_id, action (BLOCK | REPORT), optional reason/comment.
2. Validate chat exists and reporter is participant.
3. For BLOCK: insert chat_blocks record, set chat_sessions.status = 'BLOCKED', record audit_event, notify the other participant with a minimal message that they were blocked (optional), and prevent further messages.
4. For REPORT: insert chat_reports with status = OPEN, attach recent context (optionally last N messages via SQL), create audit_event and notify moderation channel (placeholder).

Notes
-----
- Ensure REPORT includes enough context for moderators but avoid exposing sensitive platform identifiers in notifications.
- All notifications use placeholders and must be wired to real Telegram/notification credentials in n8n UI.
