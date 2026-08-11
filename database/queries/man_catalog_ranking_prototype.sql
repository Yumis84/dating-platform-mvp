-- Prototype only. $1 = MAN user UUID, $2 = limit, $3 = offset.
-- The only candidate filters are ACTIVE, WOMAN owner, and normalized city.

WITH viewer AS (
  SELECT
    context.user_id,
    context.city_normalized,
    preferences.*
  FROM male_search_context context
  LEFT JOIN male_search_preferences preferences USING (user_id)
  WHERE context.user_id = $1::uuid
    AND context.onboarding_state = 'COMPLETED'
),
candidates AS (
  SELECT p.*
  FROM profiles p
  JOIN users owner ON owner.id = p.user_id
  CROSS JOIN viewer
  WHERE p.status = 'ACTIVE'
    AND lower(owner.role) = 'woman'
    AND p.city_normalized = viewer.city_normalized
),
scored AS (
  SELECT
    candidate.*,
    metrics.matched_preferences,
    metrics.considered_preferences,
    CASE
      WHEN metrics.considered_preferences = 0 THEN 0::numeric
      ELSE metrics.matched_preferences::numeric / metrics.considered_preferences
    END AS match_score
  FROM candidates candidate
  CROSS JOIN viewer
  CROSS JOIN LATERAL (
    SELECT
      (
        CASE WHEN (viewer.age_from IS NOT NULL OR viewer.age_to IS NOT NULL)
          AND (viewer.age_from IS NULL OR candidate.age >= viewer.age_from)
          AND (viewer.age_to IS NULL OR candidate.age <= viewer.age_to) THEN 1 ELSE 0 END +
        CASE WHEN cardinality(viewer.districts) > 0
          AND candidate.district = ANY(viewer.districts) THEN 1 ELSE 0 END +
        CASE WHEN (viewer.height_from_cm IS NOT NULL OR viewer.height_to_cm IS NOT NULL)
          AND (viewer.height_from_cm IS NULL OR candidate.height_cm >= viewer.height_from_cm)
          AND (viewer.height_to_cm IS NULL OR candidate.height_cm <= viewer.height_to_cm) THEN 1 ELSE 0 END +
        CASE WHEN (viewer.weight_from_kg IS NOT NULL OR viewer.weight_to_kg IS NOT NULL)
          AND (viewer.weight_from_kg IS NULL OR candidate.weight_kg >= viewer.weight_from_kg)
          AND (viewer.weight_to_kg IS NULL OR candidate.weight_kg <= viewer.weight_to_kg) THEN 1 ELSE 0 END +
        CASE WHEN (viewer.breast_size_from IS NOT NULL OR viewer.breast_size_to IS NOT NULL)
          AND (viewer.breast_size_from IS NULL OR candidate.breast_size >= viewer.breast_size_from)
          AND (viewer.breast_size_to IS NULL OR candidate.breast_size <= viewer.breast_size_to) THEN 1 ELSE 0 END +
        CASE WHEN (viewer.price_from IS NOT NULL OR viewer.price_to IS NOT NULL)
          AND EXISTS (
            SELECT 1 FROM profile_prices price
            WHERE price.profile_id = candidate.id AND price.is_active
              AND (viewer.price_from IS NULL OR price.amount >= viewer.price_from)
              AND (viewer.price_to IS NULL OR price.amount <= viewer.price_to)
          ) THEN 1 ELSE 0 END +
        CASE WHEN cardinality(viewer.meeting_place_types) > 0
          AND EXISTS (
            SELECT 1 FROM profile_meeting_places place
            WHERE place.profile_id = candidate.id AND place.is_active
              AND place.place_type = ANY(viewer.meeting_place_types)
          ) THEN 1 ELSE 0 END
      )::integer AS matched_preferences,
      (
        CASE WHEN viewer.age_from IS NOT NULL OR viewer.age_to IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN cardinality(viewer.districts) > 0 THEN 1 ELSE 0 END +
        CASE WHEN viewer.height_from_cm IS NOT NULL OR viewer.height_to_cm IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN viewer.weight_from_kg IS NOT NULL OR viewer.weight_to_kg IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN viewer.breast_size_from IS NOT NULL OR viewer.breast_size_to IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN viewer.price_from IS NOT NULL OR viewer.price_to IS NOT NULL THEN 1 ELSE 0 END +
        CASE WHEN cardinality(viewer.meeting_place_types) > 0 THEN 1 ELSE 0 END
      )::integer AS considered_preferences
  ) metrics
)
SELECT
  scored.*,
  count(*) OVER () AS total
FROM scored
ORDER BY
  match_score DESC,
  matched_preferences DESC,
  created_at DESC,
  id
LIMIT LEAST(GREATEST($2::integer, 1), 50)
OFFSET GREATEST($3::integer, 0);
