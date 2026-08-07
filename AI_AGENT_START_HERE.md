# AI_AGENT_START_HERE.md

## Dating Platform MVP — AI Agent Continuation Guide

This file is the first document an AI agent should read when continuing work in this repository.

## Reading order

1. `docs/README.md` — documentation index
2. `AI_CONTEXT.md` — current project context and handover
3. `PROJECT_STATUS.md` — current implementation status
4. `docs/PROJECT_CONTEXT.md` — architecture and decisions
5. `docs/PROJECT_CONSISTENCY_REPORT.md` — known duplicates and conflicts
6. `docs/MIGRATION_MANIFEST.md` — canonical database migration order
7. `database/MIGRATION_POLICY.md` — migration safety rules
8. `docs/IMPLEMENTATION_CHECKLIST.md` — pre-run checklist

## Current repository rules

- Do not modify SQL migrations without explicit approval.
- Do not change n8n workflows without checking architecture documents first.
- Do not modify Docker/infrastructure unless the task explicitly requires it.
- Documentation changes should preserve source-of-truth structure.

## Current architecture state

Project: Dating Platform MVP

Main components:
- PostgreSQL database
- n8n workflows
- AI agents
- Web application layer

## Database status

Canonical migration sequence is documented in:

`docs/MIGRATION_MANIFEST.md`

Migration policy:

`database/MIGRATION_POLICY.md`

Important:

`audit_events` is NOT created by canonical migrations 001–007.

Current status:

- users: exists
- telegram_accounts: exists
- audit_events: missing until reconciliation migration

Do not mark audit_events as completed unless a reconciliation migration is created and verified.

## Working protocol for AI agents

Before making changes:

1. Inspect current repository state.
2. Read relevant documentation.
3. Explain planned changes.
4. Make the smallest possible change.
5. Verify affected areas.
6. Report:

```
[AI AGENT REPORT]
Branch:
HEAD:
Changed files:
SQL:
n8n:
Docker:
Code:
Docs:
Problems:
```

## Multi-agent workflow

When several agents work on the project:

- One agent proposes changes.
- Another agent reviews consistency.
- A final agent verifies before merge.

Never trust assumptions without checking repository state.

## Current development direction

After documentation synchronization, continue MVP development according to:

`PROJECT_STATUS.md`

Priority order:

1. Resolve required database/runtime gaps.
2. Implement approved MVP stages.
3. Add tests and verification.
4. Update documentation after significant changes.

## Final rule

Preserve project history. Prefer improving existing architecture over creating parallel solutions.
