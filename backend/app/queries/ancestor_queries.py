ANCESTOR_QUERY = """
WITH RECURSIVE ancestor_cte AS (
    SELECT tree_id, child_member_id, parent_member_id, parent_role, 1 AS level
    FROM parent_child
    WHERE tree_id = :tree_id AND child_member_id = :member_id
    UNION ALL
    SELECT pc.tree_id, a.child_member_id, pc.parent_member_id, pc.parent_role, a.level + 1
    FROM ancestor_cte a
    JOIN parent_child pc
      ON pc.tree_id = a.tree_id
     AND pc.child_member_id = a.parent_member_id
)
SELECT * FROM ancestor_cte;
"""

