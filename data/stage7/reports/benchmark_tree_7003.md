# Stage7 Benchmark Report: tree_id=7003

- keyword: `朱德`
- ancestor_member_id: `1018001`

## Search Before `idx_member_name_trgm`
```sql
Bitmap Heap Scan on member  (cost=138.37..2134.47 rows=98 width=17) (actual time=0.273..5.897 rows=484 loops=1)
  Recheck Cond: (tree_id = '7003'::smallint)
  Filter: ((name)::text ~~* '%朱德%'::text)
  Rows Removed by Filter: 11516
  Heap Blocks: exact=214
  ->  Bitmap Index Scan on idx_member_tree_generation  (cost=0.00..138.34 rows=12007 width=0) (actual time=0.231..0.232 rows=12000 loops=1)
        Index Cond: (tree_id = '7003'::smallint)
Planning Time: 1.000 ms
Execution Time: 5.942 ms
```

## Search After `idx_member_name_trgm`
```sql
Bitmap Heap Scan on member  (cost=138.37..2134.47 rows=98 width=17) (actual time=0.181..4.229 rows=484 loops=1)
  Recheck Cond: (tree_id = '7003'::smallint)
  Filter: ((name)::text ~~* '%朱德%'::text)
  Rows Removed by Filter: 11516
  Heap Blocks: exact=214
  ->  Bitmap Index Scan on idx_member_tree_generation  (cost=0.00..138.34 rows=12007 width=0) (actual time=0.156..0.157 rows=12000 loops=1)
        Index Cond: (tree_id = '7003'::smallint)
Planning Time: 0.215 ms
Execution Time: 4.254 ms
```

## Four-Generation Before `idx_parent_child_tree_parent`
```sql
CTE Scan on descendants  (cost=184.33..184.57 rows=1 width=28) (actual time=0.089..0.170 rows=80 loops=1)
  Filter: (depth = 4)
  Rows Removed by Filter: 48
  CTE descendants
    ->  Recursive Union  (cost=0.42..184.33 rows=11 width=28) (actual time=0.026..0.144 rows=128 loops=1)
          ->  Index Only Scan using pk_parent_child on parent_child  (cost=0.42..8.44 rows=1 width=28) (actual time=0.025..0.026 rows=4 loops=1)
                Index Cond: ((tree_id = '7003'::smallint) AND (parent_member_id = 1018001))
                Heap Fetches: 0
          ->  Nested Loop  (cost=0.42..17.58 rows=1 width=28) (actual time=0.003..0.026 rows=31 loops=4)
                ->  WorkTable Scan on descendants d  (cost=0.00..0.22 rows=3 width=20) (actual time=0.001..0.002 rows=12 loops=4)
                      Filter: (depth < 4)
                      Rows Removed by Filter: 20
                ->  Index Only Scan using pk_parent_child on parent_child pc  (cost=0.42..5.77 rows=1 width=24) (actual time=0.001..0.002 rows=3 loops=48)
                      Index Cond: ((tree_id = d.tree_id) AND (parent_member_id = d.child_member_id))
                      Heap Fetches: 0
Planning Time: 0.387 ms
Execution Time: 0.193 ms
```

## Four-Generation After `idx_parent_child_tree_parent`
```sql
CTE Scan on descendants  (cost=184.33..184.57 rows=1 width=28) (actual time=0.093..0.171 rows=80 loops=1)
  Filter: (depth = 4)
  Rows Removed by Filter: 48
  CTE descendants
    ->  Recursive Union  (cost=0.42..184.33 rows=11 width=28) (actual time=0.023..0.145 rows=128 loops=1)
          ->  Index Scan using idx_parent_child_tree_parent on parent_child  (cost=0.42..8.44 rows=1 width=28) (actual time=0.022..0.025 rows=4 loops=1)
                Index Cond: ((tree_id = '7003'::smallint) AND (parent_member_id = 1018001))
          ->  Nested Loop  (cost=0.42..17.58 rows=1 width=28) (actual time=0.005..0.026 rows=31 loops=4)
                ->  WorkTable Scan on descendants d  (cost=0.00..0.22 rows=3 width=20) (actual time=0.001..0.002 rows=12 loops=4)
                      Filter: (depth < 4)
                      Rows Removed by Filter: 20
                ->  Index Only Scan using pk_parent_child on parent_child pc  (cost=0.42..5.77 rows=1 width=24) (actual time=0.001..0.002 rows=3 loops=48)
                      Index Cond: ((tree_id = d.tree_id) AND (parent_member_id = d.child_member_id))
                      Heap Fetches: 0
Planning Time: 0.235 ms
Execution Time: 0.194 ms
```
