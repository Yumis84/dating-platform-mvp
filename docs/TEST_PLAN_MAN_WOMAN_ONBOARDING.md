# Test plan: role-separated onboarding and ranked catalog

Status: repository/static test plan. Live execution requires separate approval.

## MAN onboarding

1. `role:man` with Telegram `first_name`: show the name and `Оставить` / `Изменить`.
2. `man_name:keep`: persist the value with `TELEGRAM_CONFIRMED`, then ask city.
3. `man_name:change`: ask manual name; persist with `MANUAL`.
4. Missing Telegram `first_name`: ask manual name immediately.
5. City input with case, `ё`, and repeated spaces: preserve display text and store canonical normalized text.
6. After city: mark context COMPLETED and show preferences/catalog buttons.
7. Open catalog with no preferences: all ACTIVE WOMAN profiles in normalized city are visible.
8. Verify no MAN `profiles` or `profile_ai_sessions` row is created.
9. Repeat callbacks/messages: no duplicate context.

## WOMAN onboarding

1. `role:woman`: create/reuse one DRAFT profile and IN_PROGRESS session.
2. One free-text message containing name, age, and city fills all three.
3. Missing/ambiguous values produce clarification without invented values.
4. Ambiguous cup/measurement breast input is not silently converted.
5. Photo stores a Telegram file ID linked to DRAFT profile with deterministic unique position.
6. Structured price rows validate amount/currency/duration.
7. Meeting places validate type and non-empty label.
8. `current_step` equals the first missing required block.
9. Completion requires scalar fields plus at least one photo, price, and meeting place.
10. Repeated finalization produces one profile transition, audit event, and pending moderation record.

## Catalog and ranking

1. Profiles from another city never appear.
2. Non-ACTIVE and non-WOMAN profiles never appear.
3. NULL preference does not change matched, considered, score, or candidate set.
4. Two of two configured matches produce score 1.0 even when all other preferences are NULL.
5. One of two produces score 0.5.
6. Zero considered produces score 0 and still returns all city candidates.
7. Price matches when any active price row is in range.
8. Meeting place matches on normalized type overlap.
9. Ordering is stable: score, matched count, created time, profile ID.
10. Client-supplied city cannot override stored MAN city.

## Automated repository checks

```powershell
python -m unittest discover -s tests -v
git diff --check
```

Additionally parse migration drafts, ranking SQL, and Postgres node queries with a PostgreSQL parser. Disposable-DB execution remains required before migration approval.
