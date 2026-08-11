# Role-separated onboarding

This document supersedes the role-agnostic generic questionnaire previously designed for WF_01.

## MAN

```text
role:man -> confirm Telegram first_name or enter name -> city -> catalog choice
```

State is `male_search_context`, not `profile_ai_sessions`. Preferences are optional and live in `male_search_preferences`. WF_01 must never create a MAN public `profiles` row.

## WOMAN

WF_01 routes WOMAN to WF_03. WF_03 follows TZ #2 and computes its next missing block from validated content:

```text
name, age, city, district, height, weight, breast_size,
description, photos, prices, meeting_places
```

`current_step` is a derived cursor. One free-text answer may complete multiple fields.

## Duplicate protection

- one `male_search_context` per MAN (`user_id` primary key);
- one active WOMAN profile session per user (partial unique constraint remains a separate hardening task);
- one public WOMAN profile per user for MVP after duplicate preflight;
- idempotent child rows, finalization, audit, and moderation.
