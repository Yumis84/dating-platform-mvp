-- DRAFT ONLY. Depends on 009_woman_profile_tz02_schema.sql.
-- Stores private MAN onboarding/search state. It does not create public profiles.

BEGIN;

CREATE TABLE IF NOT EXISTS male_search_context (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  name TEXT CHECK (name IS NULL OR NULLIF(btrim(name), '') IS NOT NULL),
  name_source TEXT CHECK (name_source IS NULL OR name_source IN ('TELEGRAM_CONFIRMED', 'MANUAL')),
  name_confirmed_at TIMESTAMP WITH TIME ZONE,
  city TEXT CHECK (city IS NULL OR NULLIF(btrim(city), '') IS NOT NULL),
  city_normalized TEXT CHECK (city_normalized IS NULL OR NULLIF(btrim(city_normalized), '') IS NOT NULL),
  onboarding_state TEXT NOT NULL DEFAULT 'AWAITING_MANUAL_NAME'
    CHECK (onboarding_state IN (
      'AWAITING_NAME_CONFIRMATION',
      'AWAITING_MANUAL_NAME',
      'AWAITING_CITY',
      'COMPLETED'
    )),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  CHECK (
    onboarding_state <> 'COMPLETED' OR (
      name IS NOT NULL AND name_source IS NOT NULL AND name_confirmed_at IS NOT NULL
      AND city IS NOT NULL AND city_normalized IS NOT NULL
    )
  )
);

COMMENT ON TABLE male_search_context IS
  'Private resumable MAN onboarding state machine. COMPLETED requires confirmed name and hard-filter catalog city.';
COMMENT ON COLUMN male_search_context.onboarding_state IS
  'Expected next MAN event. Arbitrary text is persisted only in AWAITING_MANUAL_NAME or AWAITING_CITY.';
COMMENT ON COLUMN male_search_context.city IS
  'User-facing city value confirmed by the MAN user.';
COMMENT ON COLUMN male_search_context.city_normalized IS
  'Normalized hard-filter key. A future migration may add city_id without changing catalog semantics.';

CREATE INDEX IF NOT EXISTS idx_male_search_context_city_normalized
  ON male_search_context(city_normalized);

CREATE TABLE IF NOT EXISTS male_search_preferences (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  age_from SMALLINT,
  age_to SMALLINT,
  districts TEXT[],
  height_from_cm SMALLINT,
  height_to_cm SMALLINT,
  weight_from_kg NUMERIC(5,2),
  weight_to_kg NUMERIC(5,2),
  breast_size_from NUMERIC(3,1),
  breast_size_to NUMERIC(3,1),
  price_from NUMERIC(12,2),
  price_to NUMERIC(12,2),
  meeting_place_types TEXT[],
  schema_version SMALLINT NOT NULL DEFAULT 1,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  CHECK (age_from IS NULL OR age_from BETWEEN 18 AND 100),
  CHECK (age_to IS NULL OR age_to BETWEEN 18 AND 100),
  CHECK (age_from IS NULL OR age_to IS NULL OR age_from <= age_to),
  CHECK (height_from_cm IS NULL OR height_from_cm BETWEEN 100 AND 250),
  CHECK (height_to_cm IS NULL OR height_to_cm BETWEEN 100 AND 250),
  CHECK (height_from_cm IS NULL OR height_to_cm IS NULL OR height_from_cm <= height_to_cm),
  CHECK (weight_from_kg IS NULL OR weight_from_kg BETWEEN 30 AND 300),
  CHECK (weight_to_kg IS NULL OR weight_to_kg BETWEEN 30 AND 300),
  CHECK (weight_from_kg IS NULL OR weight_to_kg IS NULL OR weight_from_kg <= weight_to_kg),
  CHECK (breast_size_from IS NULL OR breast_size_from BETWEEN 0 AND 20),
  CHECK (breast_size_to IS NULL OR breast_size_to BETWEEN 0 AND 20),
  CHECK (breast_size_from IS NULL OR breast_size_to IS NULL OR breast_size_from <= breast_size_to),
  CHECK (price_from IS NULL OR price_from >= 0),
  CHECK (price_to IS NULL OR price_to >= 0),
  CHECK (price_from IS NULL OR price_to IS NULL OR price_from <= price_to),
  CHECK (
    meeting_place_types IS NULL OR
    meeting_place_types <@ ARRAY['HER_PLACE', 'HIS_PLACE', 'HOTEL', 'PUBLIC_PLACE', 'OTHER']::TEXT[]
  )
);

COMMENT ON TABLE male_search_preferences IS
  'Optional MAN ranking preferences. NULL means not important and never filters a candidate.';

COMMIT;
