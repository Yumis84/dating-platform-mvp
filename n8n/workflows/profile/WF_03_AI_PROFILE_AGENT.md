# WF_03: AI Profile Agent (Telegram -> n8n -> AI -> Postgres)

Trigger: Telegram Trigger (message or callback after role selection)

Overview
--------
This workflow runs the AI-assisted profile creation conversation for users with role WOMAN. It orchestrates the dialog between the Telegram user and the AI Agent, persists interim state to profile_ai_sessions, stores profile data to profiles/profile_photos, and creates audit events on completion.

High-level responsibilities
- Start/resume AI conversation when user chooses role WOMAN or requests to edit/create profile.
- Collect structured fields (display_name, age, city, district, description, additional info).
- Receive and store photos (Telegram file_id) in profile_photos and reference avatar_file_id on profiles.
- Persist AI conversation context and current step to profile_ai_sessions (JSONB).
- On finish, set profiles.status = PENDING_MODERATION and create audit_events (profile_created).
- Support pausing and resuming conversations (user may return later).
- Handle errors and record them in audit_events.

Conversation structure (example)
1. Greeting
   - "Создадим вашу анкету. Я задам несколько вопросов."
2. Ask for display_name
3. Ask for age
4. Ask for city
5. Ask for district
6. Ask for description (open-ended, AI can rephrase/suggest)
7. Ask for additional info (optional)
8. Ask for photos (receive photo message(s))
9. Confirm summary with user
10. Persist profile (profiles.status = DRAFT during creation, then move to PENDING_MODERATION on user confirmation)

Persistence and resume logic
- profile_ai_sessions stores: user_id, session_status, current_step, ai_context (JSONB), created_at, updated_at.
- Before asking a question, the workflow writes current ai_context and current_step to profile_ai_sessions.
- When the user returns, the workflow loads profile_ai_sessions for the user and resumes from current_step.

Handling photos
- When user sends photos, store Telegram file_id in profile_photos (profile_id reference). The first photo can be saved as avatar_file_id on profiles if user confirms.
- Do NOT store binary blobs; store only Telegram file_id and metadata.

Error handling and pauses
- If user is inactive for a prolonged period, session_status stays IN_PROGRESS and last context is kept. Optionally set a TTL to eventually cancel stale sessions.
- On any error (AI or DB), create an audit_events record with event_type = 'ai_profile_error' and event_data describing the error.
- Provide user-friendly messages on failure and option to retry or contact support.

Security and privacy
- Do NOT ask for contact details, emails, or PII in the AI flow.
- Keep ai_context minimal and avoid logging sensitive user-provided PII. Store only what is necessary for resuming.

Notes for implementers
- AI credential must be created in n8n credentials (e.g., OPENAI_PLACEHOLDER) — do not hardcode API keys in the workflow export.
- Use parameterized SQL queries in Postgres nodes and avoid string interpolation where possible.
- This workflow is a design/template and should be extended with additional business rules and validation.

