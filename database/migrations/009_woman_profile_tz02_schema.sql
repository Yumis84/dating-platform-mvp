-- DRAFT ONLY. Do not apply without a separate approval and a data preflight.
-- Adds the structured WOMAN profile fields required by TZ #2.

BEGIN;

CREATE OR REPLACE FUNCTION normalize_city_name(value TEXT)
RETURNS TEXT
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
  SELECT regexp_replace(
    replace(lower(btrim(value)), 'ё', 'е'),
    '\s+',
    ' ',
    'g'
  );
$$;

ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS city_normalized TEXT,
  ADD COLUMN IF NOT EXISTS district TEXT,
  ADD COLUMN IF NOT EXISTS height_cm SMALLINT,
  ADD COLUMN IF NOT EXISTS weight_kg NUMERIC(5,2),
  ADD COLUMN IF NOT EXISTS breast_size NUMERIC(3,1);

UPDATE profiles
SET city_normalized = normalize_city_name(city)
WHERE city IS NOT NULL
  AND NULLIF(btrim(city), '') IS NOT NULL
  AND city_normalized IS NULL;

ALTER TABLE profiles
  ADD CONSTRAINT profiles_height_cm_check
    CHECK (height_cm IS NULL OR height_cm BETWEEN 100 AND 250),
  ADD CONSTRAINT profiles_weight_kg_check
    CHECK (weight_kg IS NULL OR weight_kg BETWEEN 30 AND 300),
  ADD CONSTRAINT profiles_breast_size_check
    CHECK (breast_size IS NULL OR breast_size BETWEEN 0 AND 20);

COMMENT ON COLUMN profiles.city IS
  'User-facing city value as confirmed by the WOMAN profile owner.';
COMMENT ON COLUMN profiles.city_normalized IS
  'Normalized city key used for equality matching. A future migration may add city_id.';
COMMENT ON COLUMN profiles.breast_size IS
  'Normalized numeric breast size. Ambiguous cup/measurement input must be clarified before persistence.';

CREATE INDEX IF NOT EXISTS idx_profiles_active_city_normalized
  ON profiles(city_normalized, created_at DESC)
  WHERE status = 'ACTIVE';

CREATE TABLE IF NOT EXISTS profile_prices (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  service_name TEXT NOT NULL,
  amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
  currency CHAR(3) NOT NULL DEFAULT 'RUB',
  duration_minutes INTEGER CHECK (duration_minutes IS NULL OR duration_minutes > 0),
  description TEXT,
  position INTEGER NOT NULL DEFAULT 0 CHECK (position >= 0),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  CONSTRAINT uniq_profile_price_position UNIQUE (profile_id, position)
);

CREATE INDEX IF NOT EXISTS idx_profile_prices_profile_active_amount
  ON profile_prices(profile_id, is_active, amount);

CREATE TABLE IF NOT EXISTS profile_meeting_places (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  place_type TEXT NOT NULL CHECK (
    place_type IN ('HER_PLACE', 'HIS_PLACE', 'HOTEL', 'PUBLIC_PLACE', 'OTHER')
  ),
  label TEXT NOT NULL,
  district TEXT,
  description TEXT,
  position INTEGER NOT NULL DEFAULT 0 CHECK (position >= 0),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  CONSTRAINT uniq_profile_meeting_place_position UNIQUE (profile_id, position)
);

CREATE INDEX IF NOT EXISTS idx_profile_meeting_places_profile_type
  ON profile_meeting_places(profile_id, is_active, place_type);

-- These indexes intentionally fail if legacy duplicates exist. Run a read-only
-- duplicate audit before this draft is ever approved for a shared database.
CREATE UNIQUE INDEX IF NOT EXISTS uniq_profile_photo_file
  ON profile_photos(profile_id, telegram_file_id)
  WHERE profile_id IS NOT NULL AND telegram_file_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uniq_profile_photo_position
  ON profile_photos(profile_id, position)
  WHERE profile_id IS NOT NULL;

COMMIT;
