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


BRANCH_TREE_QUERY = """
WITH RECURSIVE branch_nodes AS (
    SELECT
        m.member_id,
        m.tree_id,
        0 AS depth,
        NULL::bigint AS parent_member_id,
        NULL::text AS incoming_parent_role,
        ARRAY[m.member_id]::bigint[] AS path_member_ids
    FROM member m
    WHERE m.tree_id = :tree_id
      AND m.member_id = :root_member_id

    UNION ALL

    SELECT
        child.member_id,
        child.tree_id,
        branch_nodes.depth + 1 AS depth,
        pc.parent_member_id,
        pc.parent_role AS incoming_parent_role,
        branch_nodes.path_member_ids || child.member_id
    FROM branch_nodes
    JOIN parent_child pc
      ON pc.tree_id = branch_nodes.tree_id
     AND pc.parent_member_id = branch_nodes.member_id
    JOIN member child
      ON child.tree_id = pc.tree_id
     AND child.member_id = pc.child_member_id
    WHERE branch_nodes.depth < :max_depth
      AND NOT child.member_id = ANY(branch_nodes.path_member_ids)
)
SELECT
    branch_nodes.member_id,
    branch_nodes.tree_id,
    m.name,
    m.gender,
    m.birth_date,
    m.death_date,
    m.is_alive,
    m.generation_no,
    m.generation_name,
    branch_nodes.depth,
    branch_nodes.parent_member_id,
    branch_nodes.incoming_parent_role,
    branch_nodes.path_member_ids
FROM branch_nodes
JOIN member m
  ON m.tree_id = branch_nodes.tree_id
 AND m.member_id = branch_nodes.member_id
ORDER BY branch_nodes.path_member_ids;
"""
