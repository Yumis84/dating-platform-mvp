# WF_03: AI Profile Agent

Trigger: Webhook when WF_02 triggers profile creation or when the user continues the AI dialog.

Purpose
-------
Drive an AI‑assisted dialog to build a user profile. The workflow is resumable and idempotent: it will continue an existing profile_ai_session if present, or create a new session. After collecting mandatory fields it persists the profile (status = PENDING_MODERATION), creates an audit event and triggers WF_04 for moderation.

Interaction model
-----------------
- The workflow accepts a small webhook payload with: user_id (required), session_id (optional), user_answer (optional), photo_file_id (optional).
- If session_id is not provided, the workflow creates a new profile_ai_session and asks the first question.
- If user_answer is provided, the workflow saves it into session.ai_context, increments current_step and asks the next question.
- The workflow supports photo metadata: Telegram file_id is saved in profile_photos with metadata only.

Mandatory fields/questions (order)
1. name
2. age
3. city
4. description
5. interests
6. purpose (goal of dating)

Optional fields
- hobbies
- job
- education
- communication_style

Resumption and idempotency
-------------------------
- The workflow always loads the latest IN_PROGRESS profile_ai_session for the user if session_id isn't given.
- If a completed profile exists for the user, the workflow will not create duplicates.

Placeholders & credentials
--------------------------
- Postgres credential uses POSTGRES_PLACEHOLDER and must be bound in n8n UI.
- AI provider is called via HTTP using AI_API_URL and AI_API_KEY from environment.
- WF_04_TRIGGER_URL environment variable should point to the internal webhook for WF_04 AI moderation.

Error handling
--------------
- Each DB and HTTP node should surface errors to the n8n execution UI. Nodes can be set to continueOnFail where appropriate.
- If the AI provider fails, the workflow returns a friendly error message and keeps the session IN_PROGRESS for retry.
