# WOMAN AI profile flow

WF_03 is exclusively a WOMAN public-profile workflow.

```text
name -> age -> city -> district -> height -> weight -> breast_size
-> description -> photos -> prices -> meeting_places -> confirmation
-> PENDING_MODERATION
```

Free text may fill several fields. The AI returns strict structured JSON; application validation and parameterized SQL decide what is persisted. `current_step` is a derived conversational cursor, not the sole source of truth.

A DRAFT `profiles` row is created before media collection. Photos, prices, and meeting places always reference that profile and never use orphan `profile_id = NULL` production rows.

Completion requires validated scalar fields plus at least one photo, price, and meeting place. One transaction changes the profile to `PENDING_MODERATION`, session to `COMPLETED`, creates an idempotent audit event, and queues moderation.

The AI never generates SQL, invents missing values, or silently converts ambiguous breast-size formats.
