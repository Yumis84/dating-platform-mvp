# AI Agent History

## Purpose

This file is a permanent decision log for future AI agents (Copilot, Claude, ChatGPT, Grok and others) working on this repository.

Goal: preserve not only current state, but also the reasoning behind architectural and documentation decisions.

---

## Project: dating-platform-mvp

Repository: Yumis84/dating-platform-mvp

## Agent workflow principle

- One agent may implement changes.
- Another independent agent should review changes.
- Every agent must report:

```
[AGENT REPORT]
Agent:
Branch:
HEAD SHA:
Changed files:
Checks:
SQL:
n8n:
Docker:
Code:
Problems:
Next step:
```

---

# Completed milestones

## Documentation synchronization phase

### Goal
Create a reliable documentation source of truth before changing database, workflows or application code.

### Completed

- Added migration documentation structure.
- Established `docs/MIGRATION_MANIFEST.md` as canonical migration reference.
- Added `database/MIGRATION_POLICY.md` for migration safety rules.
- Added `docs/IMPLEMENTATION_CHECKLIST.md` for operational checks.
- Removed duplicate manifest pointer files.
- Fixed documentation conflicts around migrations.

---

# Important architectural decisions

## Migration manifest

Canonical location:

```
docs/MIGRATION_MANIFEST.md
```

Do not create alternative manifests.

---

## audit_events decision

Important:

`audit_events` is NOT considered available from canonical migrations 001-007.

The legacy migration `001_initial_users_schema.sql` conflicts with the canonical migration path.

Any workflow depending on audit logging must wait for reconciliation migration or explicit approved schema creation.

Do not mark `audit_events` as completed without a real migration.

---

# Rules for future agents

Before modifying anything:

1. Read:
   - `docs/AI_AGENT_CONTEXT.md`
   - `docs/AI_AGENT_HISTORY.md`
   - `docs/MIGRATION_MANIFEST.md`
   - `database/MIGRATION_POLICY.md`

2. Do not modify:
   - SQL migrations
   - n8n workflows
   - Docker/infrastructure
   - application code

without explicit approval.

3. Prefer documentation-only PRs when resolving inconsistencies.

4. Never remove large documentation sections without comparing against main.

---

# History format

Future entries should include:

## YYYY-MM-DD — Change title

Agent:

Branch:

Commit:

Changed:

Reason:

Review result:

Lessons learned:

---

# Current status

Documentation synchronization completed.

Next development phases must continue from the canonical documentation state.
