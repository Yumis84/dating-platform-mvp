# AI Agent Context & Continuation Guide

## Purpose
This file is the persistent handover document for any future AI agent (Copilot, Claude, ChatGPT, Grok, etc.) working on this repository.

## Project
Repository: Yumis84/dating-platform-mvp

## Working rules
- Always inspect current repository state before making changes.
- Documentation changes must not silently modify SQL, n8n, Docker, infrastructure, or application code.
- Before any merge, verify changed files and compare against main.
- Keep one source of truth for important architecture decisions.

## Recent completed work
### Documentation synchronization
Completed:
- Migration documentation cleanup.
- Canonical migration manifest established at `docs/MIGRATION_MANIFEST.md`.
- Migration policy established at `database/MIGRATION_POLICY.md`.
- Developer checklist established at `docs/IMPLEMENTATION_CHECKLIST.md`.
- `audit_events` documentation corrected: canonical migrations do NOT guarantee the table exists; reconciliation migration is required.

## Important migration rules
- `docs/MIGRATION_MANIFEST.md` is the canonical migration order document.
- `database/MIGRATION_POLICY.md` defines safety rules.
- Never create duplicate manifests in other paths.
- Do not claim `audit_events` exists unless the reconciliation migration has been applied.

## AI workflow protocol
When receiving a task:
1. Read this file.
2. Read `docs/README.md`.
3. Check `PROJECT_STATUS.md` for current state.
4. Check related canonical documents before editing.
5. Report work in a structured format:

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

## Previous multi-agent workflow
Multiple agents were used for verification:
- Copilot: implementation and repository operations.
- Grok: independent review, consistency checks, and architecture validation.

Future agents should continue this pattern: one agent performs changes, another validates.

## Current priority
Continue development only after confirming documentation, migration safety, and architecture consistency.
