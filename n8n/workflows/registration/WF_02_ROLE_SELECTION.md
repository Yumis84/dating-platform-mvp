# WF_02: Role Selection

Trigger: Telegram Trigger / Callback Query

Overview
--------
This workflow handles the user's role selection after the initial registration welcome message. It updates the user's role and status in the database and creates an audit event.

Flow summary
------------
1. User clicks a role button (either reply keyboard or callback data).
2. Extract telegram_id and selected role from the incoming Telegram update.
3. Query users table to find the user by telegram_id.
4. Update users.role and users.status (role -> MAN/WOMAN; status -> ACTIVE).
5. Insert an audit_event with event_type `role_selected_man` or `role_selected_woman` and event_data containing the selected role.
6. Send a confirmation message to the user:
   - If MAN:
     "Отлично.\nТеперь вы можете просматривать анкеты и общаться."
   - If WOMAN:
     "Отлично.\nНачинаем создание вашей анкеты.\nAI-помощник задаст несколько вопросов."
7. Route to next workflows (not implemented here):
   - MAN -> WF_03_CATALOG
   - WOMAN -> WF_03_AI_PROFILE

Notes
-----
- Do NOT create profiles or catalogs in this workflow.
- Do NOT connect to AI here.
- Use placeholders for credentials in exported JSON.
