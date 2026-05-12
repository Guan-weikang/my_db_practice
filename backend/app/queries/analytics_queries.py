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
