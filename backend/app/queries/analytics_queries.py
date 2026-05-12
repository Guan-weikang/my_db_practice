DASHBOARD_QUERY = """
SELECT
    CAST(:tree_id AS bigint) AS tree_id,
    COUNT(*) AS total_members,
    COUNT(*) FILTER (WHERE gender = 'male') AS male_count,
    COUNT(*) FILTER (WHERE gender = 'female') AS female_count,
    COUNT(*) FILTER (WHERE gender = 'unknown') AS unknown_count,
    ROUND(
        COUNT(*) FILTER (WHERE gender = 'male')::numeric
        / NULLIF(COUNT(*), 0),
        4
    ) AS male_ratio,
    ROUND(
        COUNT(*) FILTER (WHERE gender = 'female')::numeric
        / NULLIF(COUNT(*), 0),
        4
    ) AS female_ratio
FROM member
WHERE tree_id = :tree_id;
"""


MAX_AVERAGE_LIFESPAN_QUERY = """
WITH generation_life AS (
    SELECT
        m.generation_no,
        AVG(EXTRACT(YEAR FROM age(COALESCE(m.death_date, CURRENT_DATE), m.birth_date))) AS avg_lifespan_years
    FROM member m
    WHERE m.tree_id = :tree_id
      AND m.generation_no IS NOT NULL
      AND m.birth_date IS NOT NULL
    GROUP BY m.generation_no
)
SELECT
    CAST(:tree_id AS bigint) AS tree_id,
    generation_no,
    ROUND(avg_lifespan_years::numeric, 4) AS avg_lifespan_years
FROM generation_life
ORDER BY avg_lifespan_years DESC, generation_no ASC
LIMIT 1;
"""


OLDER_THAN_50_UNMARRIED_MALE_QUERY = """
SELECT
    CAST(:tree_id AS bigint) AS tree_id,
    m.member_id,
    m.name,
    m.birth_date,
    EXTRACT(YEAR FROM age(CURRENT_DATE, m.birth_date))::int AS age_years,
    m.generation_no,
    m.generation_name
FROM member m
WHERE m.tree_id = :tree_id
  AND m.gender = 'male'
  AND m.birth_date IS NOT NULL
  AND EXTRACT(YEAR FROM age(CURRENT_DATE, m.birth_date)) > 50
  AND NOT EXISTS (
      SELECT 1
      FROM marriage mg
      WHERE mg.tree_id = m.tree_id
        AND (mg.member_id_1 = m.member_id OR mg.member_id_2 = m.member_id)
  )
ORDER BY m.birth_date ASC, m.member_id ASC;
"""


BEFORE_GENERATION_AVERAGE_BIRTH_YEAR_QUERY = """
WITH generation_birth_avg AS (
    SELECT
        m.generation_no,
        AVG(EXTRACT(YEAR FROM m.birth_date)) AS avg_birth_year
    FROM member m
    WHERE m.tree_id = :tree_id
      AND m.generation_no IS NOT NULL
      AND m.birth_date IS NOT NULL
    GROUP BY m.generation_no
)
SELECT
    CAST(:tree_id AS bigint) AS tree_id,
    m.member_id,
    m.name,
    m.generation_no,
    m.generation_name,
    EXTRACT(YEAR FROM m.birth_date)::int AS birth_year,
    ROUND(g.avg_birth_year::numeric, 4) AS avg_birth_year
FROM member m
JOIN generation_birth_avg g
  ON g.generation_no = m.generation_no
WHERE m.tree_id = :tree_id
  AND m.generation_no IS NOT NULL
  AND m.birth_date IS NOT NULL
  AND EXTRACT(YEAR FROM m.birth_date) < g.avg_birth_year
ORDER BY m.generation_no ASC, birth_year ASC, m.member_id ASC;
"""
