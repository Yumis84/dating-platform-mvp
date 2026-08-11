# Catalog API design

## POST `/webhook/profile-catalog`

Input:

```json
{
  "user_id": "MAN user UUID",
  "limit": 25,
  "offset": 0
}
```

The client does not send authoritative city or hard filters. WF_05 loads the confirmed city and optional preferences from PostgreSQL.

Response:

```json
{
  "items": [
    {
      "id": "profile UUID",
      "name": "Public WOMAN name",
      "age": 30,
      "city": "Калининград",
      "matched_preferences": 2,
      "considered_preferences": 3,
      "match_score": 0.6667
    }
  ],
  "total": 42,
  "limit": 25,
  "offset": 0
}
```

Rules:

- verify the viewer exists and has MAN role;
- require completed `male_search_context`;
- return only ACTIVE WOMAN profiles from the normalized city;
- rank but never filter by optional preferences;
- default limit 25, maximum 50;
- log effective considered preference keys in `profile_search_events` without copying private values unnecessarily.

Preferences are managed through a separate settings endpoint/workflow. Empty arrays are normalized to NULL. City changes use the same normalization function and remain non-null.
