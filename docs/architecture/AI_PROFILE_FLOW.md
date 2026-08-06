# AI Profile Flow

Sequence diagram (high level):

Telegram Client (user)
        ↓
Telegram Bot (receives role selection / start profile)
        ↓
n8n workflow WF_03_AI_PROFILE_AGENT
        ↓
AI Agent (OpenAI / other model)
        ↓
profile_ai_sessions (store context, current_step)
        ↓
profiles / profile_photos (store profile draft and photos)
        ↓
Moderation (profiles moved to PENDING_MODERATION)

Notes:
- The AI Agent is called through n8n using credentials stored in the n8n Credentials store.
- profile_ai_sessions allows resuming the conversation when the user returns.
- Profiles are created as DRAFT and moved to PENDING_MODERATION on user confirmation.
