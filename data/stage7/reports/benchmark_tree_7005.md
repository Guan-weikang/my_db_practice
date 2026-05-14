# Stage7 Benchmark Report: tree_id=7005

- keyword: `孔承`
- ancestor_member_id: `1040510`

## Search Before `idx_member_name_trgm`
```sql
Bitmap Heap Scan on member  (cost=577.85..3148.50 rows=919 width=17) (actual time=1.107..19.488 rows=2004 loops=1)
  Recheck Cond: (tree_id = '7005'::smallint)
  Filter: ((name)::text ~~* '%孔承%'::text)
  Rows Removed by Filter: 47996
  Heap Blocks: exact=865
  ->  Bitmap Index Scan on idx_member_tree_generation  (cost=0.00..577.62 rows=50310 width=0) (actual time=0.866..0.867 rows=50000 loops=1)
        Index Cond: (tree_id = '7005'::smallint)
Planning Time: 0.453 ms
Execution Time: 19.574 ms
```

## Search After `idx_member_name_trgm`
```sql
Bitmap Heap Scan on member  (cost=577.85..3148.50 rows=919 width=17) (actual time=0.905..17.670 rows=2004 loops=1)
  Recheck Cond: (tree_id = '7005'::smallint)
  Filter: ((name)::text ~~* '%孔承%'::text)
  Rows Removed by Filter: 47996
  Heap Blocks: exact=865
  ->  Bitmap Index Scan on idx_member_tree_generation  (cost=0.00..577.62 rows=50310 width=0) (actual time=0.721..0.722 rows=50000 loops=1)
        Index Cond: (tree_id = '7005'::smallint)
Planning Time: 0.218 ms
Execution Time: 17.738 ms
```

## Four-Generation Before `idx_parent_child_tree_parent`
```sql
CTE Scan on descendants  (cost=184.33..184.57 rows=1 width=28) (actual time=0.155..0.285 rows=32 loops=1)
  Filter: (depth = 4)
  Rows Removed by Filter: 25
  CTE descendants
    ->  Recursive Union  (cost=0.42..184.33 rows=11 width=28) (actual time=0.029..0.266 rows=57 loops=1)
          ->  Index Only Scan using pk_parent_child on parent_child  (cost=0.42..8.44 rows=1 width=28) (actual time=0.028..0.029 rows=3 loops=1)
                Index Cond: ((tree_id = '7005'::smallint) AND (parent_member_id = 1040510))
                Heap Fetches: 0
          ->  Nested Loop  (cost=0.42..17.58 rows=1 width=28) (actual time=0.013..0.056 rows=14 loops=4)
                ->  WorkTable Scan on descendants d  (cost=0.00..0.22 rows=3 width=20) (actual time=0.001..0.001 rows=6 loops=4)
                      Filter: (depth < 4)
                      Rows Removed by Filter: 8
                ->  Index Only Scan using pk_parent_child on parent_child pc  (cost=0.42..5.77 rows=1 width=24) (actual time=0.008..0.008 rows=2 loops=25)
                      Index Cond: ((tree_id = d.tree_id) AND (parent_member_id = d.child_member_id))
                      Heap Fetches: 0
Planning Time: 0.345 ms
Execution Time: 0.312 ms
```

## Four-Generation After `idx_parent_child_tree_parent`
```sql
CTE Scan on descendants  (cost=184.33..184.57 rows=1 width=28) (actual time=0.080..0.125 rows=32 loops=1)
  Filter: (depth = 4)
  Rows Removed by Filter: 25
  CTE descendants
    ->  Recursive Union  (cost=0.42..184.33 rows=11 width=28) (actual time=0.025..0.111 rows=57 loops=1)
          ->  Index Scan using idx_parent_child_tree_parent on parent_child  (cost=0.42..8.44 rows=1 width=28) (actual time=0.024..0.026 rows=3 loops=1)
                Index Cond: ((tree_id = '7005'::smallint) AND (parent_member_id = 1040510))
          ->  Nested Loop  (cost=0.42..17.58 rows=1 width=28) (actual time=0.005..0.019 rows=14 loops=4)
                ->  WorkTable Scan on descendants d  (cost=0.00..0.22 rows=3 width=20) (actual time=0.001..0.001 rows=6 loops=4)
                      Filter: (depth < 4)
                      Rows Removed by Filter: 8
                ->  Index Only Scan using pk_parent_child on parent_child pc  (cost=0.42..5.77 rows=1 width=24) (actual time=0.002..0.002 rows=2 loops=25)
                      Index Cond: ((tree_id = d.tree_id) AND (parent_member_id = d.child_member_id))
                      Heap Fetches: 0
Planning Time: 0.228 ms
Execution Time: 0.145 ms
```
