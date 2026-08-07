# AI Work Log

## Dating Platform MVP

This file stores important project decisions so new AI agents can continue work without relying on previous conversations.

---

## 2026-08-07 — Transition to MVP development

Completed documentation synchronization phase:

- Migration manifest finalized.
- Migration policy finalized.
- Implementation checklist finalized.
- Documentation consistency issues resolved.
- `audit_events` conflict documented.

Current database understanding:

- Canonical migrations 001–007 do NOT create `audit_events`.
- `audit_events` requires a reconciliation migration or approved alternative.
- Never assume audit infrastructure exists from documentation alone.

---

## Current development stage

Moving from documentation stabilization to working MVP.

First implementation target:

## WF_01_USER_REGISTRATION

Goal:

Telegram user → n8n workflow → PostgreSQL user creation.

Expected flow:

1. Telegram `/start` received.
2. n8n identifies Telegram user.
3. Check existing account.
4. Create user if missing.
5. Create telegram account relation.
6. Return registration menu.

---

## Agent rules

Before every implementation:

- Read `AI_AGENT_START_HERE.md`.
- Check current docs.
- Inspect existing workflows.
- Avoid duplicate implementations.
- Do not modify SQL/n8n/infrastructure outside task scope.

After work provide:

```
[AI REPORT]
HEAD:
Branch:
Changed files:
SQL:
n8n:
Docker:
Code:
Docs:
Problems:
Next step:
```

---

## Multi-agent process

Recommended workflow:

1. Builder agent implements.
2. Review agent checks architecture.
3. Verification agent checks repository state.

Documentation is not the final goal. Documentation exists to protect implementation quality.
