# WF_01 registration and role routing

Canonical product routing:

```text
/start -> user/account registration -> role callback
MAN -> confirm or enter name -> normalized city -> preferences/catalog choice
WOMAN -> create/resume DRAFT profile session -> WF_03
```

WF_01 must preserve callback acknowledgement, unknown-callback protection, duplicate registration protection, parameterized SQL, and audit logging.

MAN state is private `male_search_context`; optional settings are `male_search_preferences`. WF_01 must not create a MAN public profile or send MAN through WOMAN `profile_ai_sessions` questions.

The repository file `WF_01_USER_REGISTRATION_MAN_WOMAN_DEV.json` is an inactive architecture draft. It is not a production export and must not be imported or published without separate verification and approval.
