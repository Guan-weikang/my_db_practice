KINSHIP_PATH_QUERY = """
WITH RECURSIVE relation_edges AS (
    SELECT
        pc.tree_id,
        pc.parent_member_id AS from_member,
        pc.child_member_id AS to_member
    FROM parent_child pc
    WHERE pc.tree_id = :tree_id

    UNION ALL

    SELECT
        pc.tree_id,
        pc.child_member_id AS from_member,
        pc.parent_member_id AS to_member
    FROM parent_child pc
    WHERE pc.tree_id = :tree_id

    UNION ALL

    SELECT
        mg.tree_id,
        mg.member_id_1 AS from_member,
        mg.member_id_2 AS to_member
    FROM marriage mg
    WHERE mg.tree_id = :tree_id
      AND (:include_ended_marriages OR mg.status = 'active')

    UNION ALL

    SELECT
        mg.tree_id,
        mg.member_id_2 AS from_member,
        mg.member_id_1 AS to_member
    FROM marriage mg
    WHERE mg.tree_id = :tree_id
      AND (:include_ended_marriages OR mg.status = 'active')
),
path_search AS (
    SELECT
        :tree_id AS tree_id,
        CAST(:member_a AS bigint) AS current_member,
        ARRAY[:member_a]::bigint[] AS path_member_ids

    UNION ALL

    SELECT
        relation_edges.tree_id,
        relation_edges.to_member,
        path_search.path_member_ids || relation_edges.to_member
    FROM path_search
    JOIN relation_edges
      ON relation_edges.tree_id = path_search.tree_id
     AND relation_edges.from_member = path_search.current_member
    WHERE array_length(path_search.path_member_ids, 1) - 1 < :max_depth
      AND NOT relation_edges.to_member = ANY(path_search.path_member_ids)
)
SELECT path_member_ids
FROM path_search
WHERE current_member = :member_b
ORDER BY array_length(path_member_ids, 1), path_member_ids
LIMIT 1;
"""


KINSHIP_PATH_NODE_DETAILS_QUERY = """
SELECT
    ids.member_id,
    m.tree_id,
    m.name,
    m.gender,
    m.birth_date,
    m.death_date,
    m.is_alive,
    m.generation_no,
    m.generation_name
FROM unnest(CAST(:path_member_ids AS bigint[])) WITH ORDINALITY AS ids(member_id, ord)
JOIN member m
  ON m.tree_id = :tree_id
 AND m.member_id = ids.member_id
ORDER BY ids.ord;
"""


KINSHIP_PATH_EDGE_DETAILS_QUERY = """
WITH path_members AS (
    SELECT member_id, ord
    FROM unnest(CAST(:path_member_ids AS bigint[])) WITH ORDINALITY AS ids(member_id, ord)
),
path_edges AS (
    SELECT
        current_node.member_id AS from_member_id,
        next_node.member_id AS to_member_id,
        current_node.ord
    FROM path_members current_node
    JOIN path_members next_node
      ON next_node.ord = current_node.ord + 1
)
SELECT
    path_edges.from_member_id,
    path_edges.to_member_id,
    CASE
        WHEN parent_forward.parent_member_id IS NOT NULL THEN 'parent'
        WHEN parent_reverse.parent_member_id IS NOT NULL THEN 'child'
        ELSE 'spouse'
    END AS relation_type,
    COALESCE(parent_forward.parent_role, parent_reverse.parent_role) AS parent_role,
    marriage.status AS marriage_status
FROM path_edges
LEFT JOIN parent_child parent_forward
  ON parent_forward.tree_id = :tree_id
 AND parent_forward.parent_member_id = path_edges.from_member_id
 AND parent_forward.child_member_id = path_edges.to_member_id
LEFT JOIN parent_child parent_reverse
  ON parent_reverse.tree_id = :tree_id
 AND parent_reverse.parent_member_id = path_edges.to_member_id
 AND parent_reverse.child_member_id = path_edges.from_member_id
LEFT JOIN marriage
  ON marriage.tree_id = :tree_id
 AND marriage.member_id_1 = LEAST(path_edges.from_member_id, path_edges.to_member_id)
 AND marriage.member_id_2 = GREATEST(path_edges.from_member_id, path_edges.to_member_id)
 AND (:include_ended_marriages OR marriage.status = 'active')
ORDER BY path_edges.ord;
"""
