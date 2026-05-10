DASHBOARD_QUERY = """
SELECT
    COUNT(*) AS total_members,
    COUNT(*) FILTER (WHERE gender = 'male') AS male_count,
    COUNT(*) FILTER (WHERE gender = 'female') AS female_count
FROM member
WHERE tree_id = :tree_id;
"""

