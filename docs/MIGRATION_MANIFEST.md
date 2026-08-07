# MIGRATION_MANIFEST — canonical manifest in PR #2

This branch intentionally does not contain the canonical migration manifest. The canonical MIGRATION_MANIFEST is provided in Pull Request #2 and should be used as the source of truth for migration ordering and reconciliation guidance.

Please refer to: https://github.com/Yumis84/dating-platform-mvp/pull/2

Reasoning
---------
- To avoid divergence and duplicate authoritative manifests in multiple branches, this branch points to the canonical manifest in PR #2.
- The canonical manifest in PR #2 already documents the migration order, conflict resolution for `001_*`, and audit_events plan.

If you need to view or update the canonical manifest, please review PR #2 and make changes there.
