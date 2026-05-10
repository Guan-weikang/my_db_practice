DESCENDANT_QUERY = """
WITH RECURSIVE descendant_cte AS (
    SELECT tree_id, parent_member_id, child_member_id, 1 AS level
    FROM parent_child
    WHERE tree_id = :tree_id AND parent_member_id = :member_id
    UNION ALL
    SELECT pc.tree_id, pc.parent_member_id, pc.child_member_id, d.level + 1
    FROM descendant_cte d
    JOIN parent_child pc
      ON pc.tree_id = d.tree_id
     AND pc.parent_member_id = d.child_member_id
)
SELECT * FROM descendant_cte;
"""

