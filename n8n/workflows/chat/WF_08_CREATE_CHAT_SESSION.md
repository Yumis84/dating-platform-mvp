# WF_08: Create Chat Session

Trigger: Webhook / Telegram callback when user presses "Начать чат"

Purpose
-------
Create or resume an anonymous chat session between the initiating user (usually a man) and the owner of a female profile. Ensure idempotency and prevent multiple active sessions for the same (initiator, profile) pair. Respect block lists and profile availability.

Flow summary
------------
1. Receive request with initiator_user_id and profile_id.
2. Validate profile exists and status = 'ACTIVE'.
3. Check whether initiator is blocked from contacting this profile (chat_blocks or user-level bans).
4. Check for an existing OPEN chat_session between initiator_user_id and profile_id — if exists, return existing chat_id (idempotent).
5. Create new chat_session (profile_id, initiator_user_id, respondent_user_id = profile.user_id) and set status = OPEN.
6. Insert audit_event recording session creation.
7. Notify initiating user with confirmation and send a notification to the respondent (placeholder node).

Notes
-----
- Prevent creating a second active chat for the same initiator/profile combination.
- Use Postgres credential placeholder in JSON export — bind proper credentials in n8n UI.
- Do not leak Telegram IDs in responses; return only chat_id and minimal metadata.
