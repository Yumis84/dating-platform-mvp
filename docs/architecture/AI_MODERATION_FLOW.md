# AI Moderation Flow

Sequence diagram (high level):

profile_created
    ↓
n8n WF_04_AI_MODERATION
    ↓
AI Agent (moderation model)
    ↓
profile_moderation
    ↓
ACTIVE / BLOCKED / REVIEW (PENDING_MODERATION)

Notes:
- The workflow triggers on profile_created and sends profile text and metadata to AI Agent.
- Images are not stored or forwarded in raw form; only telegram_file_id references are used for optional separate analysis.
- AI returns a JSON verdict; the workflow updates profiles, creates moderation records and history, and notifies admin if REVIEW is required.
