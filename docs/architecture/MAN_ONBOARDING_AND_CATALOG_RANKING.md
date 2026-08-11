# MAN onboarding and catalog ranking

Status: canonical product decision and implementation contract. Repository drafts only; no production deployment is implied.

## Required flow

```text
role:man
-> resolve/confirm name
-> city
-> [Настроить предпочтения] / [Смотреть анкеты]
```

`name` and `city` are the only required MAN onboarding values. `male_search_context` may hold an incomplete `IN_PROGRESS` row so the flow can resume; `COMPLETED` requires both values. A MAN never receives a public `profiles` row.

### Name confirmation

If Telegram provides `first_name`, show:

```text
Ваше имя: Дмитрий
[Оставить] [Изменить]
```

`Leave` stores the Telegram value as an explicitly confirmed value. `Change`, or a missing Telegram `first_name`, asks for manual input. The selected value is persisted in `male_search_context`; Telegram is not a permanent source of truth.

### City

Store both the confirmed display value and `normalize_city_name(value)`. MVP normalization trims leading/trailing whitespace, collapses internal whitespace, lowercases, and maps `ё` to `е`.

Catalog equality is:

```text
MAN male_search_context.city_normalized
== WOMAN profiles.city_normalized
```

The design permits a future nullable `city_id` migration without changing product semantics.

## Optional preferences

Every preference is nullable. NULL means `не важно` and:

- does not increase score;
- does not reduce score;
- does not exclude a candidate.

Only structured fields present in the WOMAN schema may be exposed as MAN preferences. MVP fields are age, district, height, weight, numeric breast size, price range, and meeting-place type.

Preferences can be skipped during onboarding and edited later. Absence of a `male_search_preferences` row is equivalent to all NULL values.

## WOMAN field formats used by ranking

### breast_size

Canonical format: `NUMERIC(3,1)` representing a numeric size explicitly confirmed by the WOMAN user. The AI may normalize `третий размер` to `3.0`. Cup letters or body measurements are not silently converted; the agent asks a clarification question.

### prices

One profile has ordered `profile_prices` rows. Each row contains a service label, non-negative amount, ISO currency, optional duration, and optional description. MAN price matching succeeds when at least one active row falls in the configured range.

### meeting_places

One profile has ordered `profile_meeting_places` rows. MVP normalized types are:

- `HER_PLACE`;
- `HIS_PLACE`;
- `HOTEL`;
- `PUBLIC_PLACE`;
- `OTHER`.

`label`, `district`, and `description` preserve user-facing detail. MAN matching uses type overlap only in MVP.

## Catalog invariants

The only candidate filters are:

1. profile status is `ACTIVE`;
2. profile owner role is `WOMAN`;
3. normalized cities are equal.

All optional preferences are calculated in the SELECT/scoring layer, never in the candidate WHERE clause.

For each candidate:

```text
considered_preferences = count of preferences actually configured by MAN
matched_preferences = count of those preferences satisfied by the candidate
match_score = matched_preferences / considered_preferences
```

If `considered_preferences = 0`, `match_score = 0` and all WOMAN profiles in the city remain visible.

MVP uses equal weights. Stable ordering:

```text
match_score DESC,
matched_preferences DESC,
p.created_at DESC,
p.id
```

## Ownership

- WF_01 routes roles and MAN onboarding events.
- WF_03 owns WOMAN profile creation only.
- WF_05 loads persisted MAN context/preferences and returns ranked WOMAN profiles.
- `profile_search_events` is analytics; it is not preference storage.
