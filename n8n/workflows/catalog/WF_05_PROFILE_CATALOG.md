# WF_05: ranked WOMAN catalog (inactive DEV)

Input contains only authenticated MAN `user_id`, limit, and offset. City and preferences are loaded from PostgreSQL.

The candidate WHERE clause is restricted to ACTIVE, WOMAN owner, and normalized city equality. Optional preferences contribute to `matched_preferences`, `considered_preferences`, and `match_score`; they never remove candidates.

The repository JSON and `database/queries/man_catalog_ranking_prototype.sql` are DEV drafts and have not been imported into n8n.
