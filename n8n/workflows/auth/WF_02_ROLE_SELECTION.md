# WF_02: Role Selection

Trigger: Webhook when user selects a role choice (MAN or WOMAN)

Purpose
-------
Update users.role and route the user to the next step:
- WOMAN -> start WF_03 AI_PROFILE_AGENT (invoked via internal webhook placeholder)
- MAN -> direct the user to the profile catalog (future flow)

Flow summary
------------
1. Receive webhook with user_id and role.
2. Validate role is one of MAN or WOMAN.
3. Update users table set role.
4. Create audit_event for role selection.
5. If WOMAN -> make HTTP call to WF_03 trigger URL (placeholder).
6. Respond to webhook with next step instructions.

Placeholders
------------
- WF_03_TRIGGER_URL should be set to the internal webhook that starts WF_03.
