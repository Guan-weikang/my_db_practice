ANCESTOR_QUERY = """
WITH RECURSIVE ancestor_cte AS (
    SELECT
        pc.tree_id,
        pc.child_member_id,
        pc.parent_member_id,
        pc.parent_role,
        1 AS depth,
        ARRAY[:member_id, pc.parent_member_id]::bigint[] AS path_member_ids
    FROM parent_child pc
    WHERE pc.tree_id = :tree_id
      AND pc.child_member_id = :member_id

    UNION ALL
    SELECT
        pc.tree_id,
        pc.child_member_id,
        pc.parent_member_id,
        pc.parent_role,
        ancestor_cte.depth + 1,
        ancestor_cte.path_member_ids || pc.parent_member_id
    FROM ancestor_cte
    JOIN parent_child pc
      ON pc.tree_id = ancestor_cte.tree_id
     AND pc.child_member_id = ancestor_cte.parent_member_id
    WHERE ancestor_cte.depth < :max_depth
      AND NOT pc.parent_member_id = ANY(ancestor_cte.path_member_ids)
)
SELECT
    ancestor_cte.parent_member_id AS member_id,
    ancestor_cte.tree_id,
    m.name,
    m.gender,
    m.birth_date,
    m.death_date,
    m.is_alive,
    m.generation_no,
    m.generation_name,
    ancestor_cte.depth,
    ancestor_cte.child_member_id,
    ancestor_cte.parent_role,
    ancestor_cte.path_member_ids
FROM ancestor_cte
JOIN member m
  ON m.tree_id = ancestor_cte.tree_id
 AND m.member_id = ancestor_cte.parent_member_id
ORDER BY ancestor_cte.path_member_ids;
"""
