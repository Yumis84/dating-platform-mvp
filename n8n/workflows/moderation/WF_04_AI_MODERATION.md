# WF_04: AI Moderation

Trigger: Webhook / Internal n8n Trigger (on profile_created event)

Overview
--------
This workflow receives a profile_created event (profile_id), loads profile data and related photos and AI session context, sends them to the AI Agent for automated moderation, and takes action based on the AI result:
- APPROVED -> activate profile
- REJECTED -> block profile
- REVIEW -> set profile to pending moderation and notify admin

Design goals
------------
- Keep checks automated and auditable.
- Do NOT store or forward raw images; only reference Telegram file_ids for AI image analysis if needed (or offload image checks to a separate service).
- Record moderation decisions in profile_moderation and moderation_history, and log an audit_event for traceability.

Flow summary
------------
1. Trigger: receives profile_created with profile_id
2. Load profile (profiles), photos (profile_photos), and last AI session (profile_ai_sessions)
3. Build payload and call AI Agent (credential placeholder)
4. Parse AI response JSON: {status: APPROVED|REJECTED|REVIEW, score: 0-100, flags: [], reason: ""}
5. Branch based on status:
   - APPROVED: set profiles.status = 'ACTIVE'; create profile_moderation (AI, APPROVED), moderation_history and audit_event
   - REJECTED: set profiles.status = 'BLOCKED'; create profile_moderation (AI, REJECTED), moderation_history and audit_event
   - REVIEW: set profiles.status = 'PENDING_MODERATION'; create profile_moderation (AI, PENDING/REVIEW), moderation_history and audit_event; notify admin (placeholder)

Notes
-----
- AI analysis should not receive raw image binaries in this workflow. If image analysis is required, supply only telegram_file_id and a separate image-scanning service should fetch and analyze images (out of scope).
- All DB operations use parameterized queries via Postgres credential in n8n.
- Workflow export does not include credentials; create credentials in n8n UI and bind them after import.

