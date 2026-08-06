# WF_09: Message Router

Trigger: Telegram webhook or WebApp webhook when user sends a message

Purpose
-------
Route messages between chat participants via the platform, ensuring session validity, block/rate checks, persistence, and delivery. This router is the central message processing workflow.

Flow summary
------------
1. Receive incoming message (sender_user_id, chat_id or profile_id plus context, content, optional media metadata).
2. Resolve chat_session if chat_id not provided (e.g., active session lookup by initiator/profile).
3. Verify chat_session.status = OPEN.
4. Check chat_blocks for blocker records involving sender/recipient.
5. Enforce rate limits (simple count of recent messages by sender across sessions or for this session).
6. Persist message in messages table (content, content_type, metadata).
7. Forward message to recipient via Telegram bot (or WebApp), using platform relay (do not expose raw Telegram IDs to other party).
8. Record audit_event for message delivery.

Notes
-----
- Do not return or forward counterpart Telegram IDs or internal UUIDs in delivered payloads.
- Keep operations idempotent where possible (use message dedup keys from Telegram updates).
