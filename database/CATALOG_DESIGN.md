# Catalog design

PostgreSQL is the source of truth. The catalog returns public WOMAN profiles only.

## Storage

- `male_search_context`: private confirmed MAN name and required normalized city.
- `male_search_preferences`: optional nullable ranking inputs.
- `profiles`: WOMAN public profiles only in this product flow.
- `profile_prices`, `profile_meeting_places`, `profile_photos`: structured WOMAN child records.
- `profile_search_events`: analytics, never persistent preferences.

## Candidate set

The candidate WHERE clause contains only `ACTIVE`, WOMAN owner, and normalized-city equality. The MAN context must be `COMPLETED`. Optional preferences must not appear as excluding predicates.

City is stored twice: display text plus `city_normalized`. The normalization contract is shared by MAN and WOMAN persistence. A future `city_id` may replace the comparison key without redesigning the catalog.

## Ranking

Every configured preference contributes one considered dimension and at most one matched dimension. Equal weights are used in MVP.

```text
match_score = considered > 0 ? matched / considered : 0
```

No preference row means all city candidates are returned. See `database/queries/man_catalog_ranking_prototype.sql`.

## Performance

The WOMAN schema draft adds a partial `(city_normalized, created_at)` index for ACTIVE profiles. Child-table indexes support price and meeting-place existence checks. Validate query plans on staging before production approval.

## Privacy

Catalog responses expose profile IDs and public content only. MAN name/preferences, Telegram identifiers, owner user IDs, audit data, and moderation internals are not returned.
