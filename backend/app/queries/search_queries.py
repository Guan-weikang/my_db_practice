MEMBER_SEARCH_QUERY = """
SELECT member_id, name, gender, generation_no, generation_name
FROM member
WHERE tree_id = :tree_id
  AND name ILIKE '%' || :keyword || '%'
ORDER BY generation_no NULLS LAST, name, member_id
LIMIT 50;
"""

