MEMBER_SEARCH_QUERY = """
WITH matched_members AS (
    SELECT
        m.member_id,
        m.tree_id,
        m.name,
        m.gender,
        m.birth_date,
        m.death_date,
        m.is_alive,
        m.generation_no,
        m.generation_name,
        MAX(CASE WHEN pc.parent_role = 'father' THEN p.name END) AS father_name,
        MAX(CASE WHEN pc.parent_role = 'mother' THEN p.name END) AS mother_name,
        CASE
            WHEN LOWER(m.name) = LOWER(:keyword) THEN 0
            WHEN LOWER(m.name) LIKE LOWER(:keyword_prefix) THEN 1
            ELSE 2
        END AS match_priority
    FROM member m
    LEFT JOIN parent_child pc
      ON pc.tree_id = m.tree_id
     AND pc.child_member_id = m.member_id
    LEFT JOIN member p
      ON p.tree_id = pc.tree_id
     AND p.member_id = pc.parent_member_id
    WHERE m.tree_id = :tree_id
      AND m.name ILIKE '%' || :keyword || '%'
    GROUP BY
        m.member_id,
        m.tree_id,
        m.name,
        m.gender,
        m.birth_date,
        m.death_date,
        m.is_alive,
        m.generation_no,
        m.generation_name
)
SELECT
    member_id,
    tree_id,
    name,
    gender,
    birth_date,
    death_date,
    is_alive,
    generation_no,
    generation_name,
    father_name,
    mother_name,
    COUNT(*) OVER() AS total_count
FROM matched_members
ORDER BY
    match_priority ASC,
    generation_no ASC NULLS LAST,
    birth_date ASC NULLS LAST,
    member_id ASC
OFFSET :offset
LIMIT :limit;
"""
