# Stage7 Benchmark Report: tree_id=7003

- keyword: `朱`
- ancestor_member_id: `1018001`

## Search Before `idx_member_name_trgm`
```sql
Bitmap Heap Scan on member  (cost=144.63..2220.58 rows=1473 width=17) (actual time=1.347..9.508 rows=12000 loops=1)
  Recheck Cond: (tree_id = '7003'::smallint)
  Filter: ((name)::text ~~* '%朱%'::text)
  Heap Blocks: exact=226
  ->  Bitmap Index Scan on idx_member_tree_generation  (cost=0.00..144.26 rows=12263 width=0) (actual time=1.187..1.187 rows=12000 loops=1)
        Index Cond: (tree_id = '7003'::smallint)
Planning Time: 1.918 ms
Execution Time: 10.128 ms
```

## Search After `idx_member_name_trgm`
```sql
Bitmap Heap Scan on member  (cost=144.63..2220.58 rows=1473 width=17) (actual time=0.197..4.663 rows=12000 loops=1)
  Recheck Cond: (tree_id = '7003'::smallint)
  Filter: ((name)::text ~~* '%朱%'::text)
  Heap Blocks: exact=226
  ->  Bitmap Index Scan on idx_member_tree_generation  (cost=0.00..144.26 rows=12263 width=0) (actual time=0.168..0.169 rows=12000 loops=1)
        Index Cond: (tree_id = '7003'::smallint)
Planning Time: 0.223 ms
Execution Time: 5.034 ms
```

## Four-Generation Before `idx_parent_child_tree_parent`
```sql
CTE Scan on descendants  (cost=184.33..184.57 rows=1 width=28) (actual time=0.215..0.375 rows=105 loops=1)
  Filter: (depth = 4)
  Rows Removed by Filter: 62
  CTE descendants
    ->  Recursive Union  (cost=0.42..184.33 rows=11 width=28) (actual time=0.085..0.323 rows=167 loops=1)
          ->  Index Only Scan using pk_parent_child on parent_child  (cost=0.42..8.44 rows=1 width=28) (actual time=0.084..0.085 rows=5 loops=1)
                Index Cond: ((tree_id = '7003'::smallint) AND (parent_member_id = 1018001))
                Heap Fetches: 0
          ->  Nested Loop  (cost=0.42..17.58 rows=1 width=28) (actual time=0.005..0.051 rows=40 loops=4)
                ->  WorkTable Scan on descendants d  (cost=0.00..0.22 rows=3 width=20) (actual time=0.002..0.003 rows=16 loops=4)
                      Filter: (depth < 4)
                      Rows Removed by Filter: 26
                ->  Index Only Scan using pk_parent_child on parent_child pc  (cost=0.42..5.77 rows=1 width=24) (actual time=0.002..0.002 rows=3 loops=62)
                      Index Cond: ((tree_id = d.tree_id) AND (parent_member_id = d.child_member_id))
                      Heap Fetches: 0
Planning Time: 0.505 ms
Execution Time: 0.427 ms
```

## Four-Generation After `idx_parent_child_tree_parent`
```sql
CTE Scan on descendants  (cost=184.33..184.57 rows=1 width=28) (actual time=0.470..0.575 rows=105 loops=1)
  Filter: (depth = 4)
  Rows Removed by Filter: 62
  CTE descendants
    ->  Recursive Union  (cost=0.42..184.33 rows=11 width=28) (actual time=0.372..0.540 rows=167 loops=1)
          ->  Index Scan using idx_parent_child_tree_parent on parent_child  (cost=0.42..8.44 rows=1 width=28) (actual time=0.369..0.373 rows=5 loops=1)
                Index Cond: ((tree_id = '7003'::smallint) AND (parent_member_id = 1018001))
          ->  Nested Loop  (cost=0.42..17.58 rows=1 width=28) (actual time=0.008..0.036 rows=40 loops=4)
                ->  WorkTable Scan on descendants d  (cost=0.00..0.22 rows=3 width=20) (actual time=0.001..0.002 rows=16 loops=4)
                      Filter: (depth < 4)
                      Rows Removed by Filter: 26
                ->  Index Only Scan using pk_parent_child on parent_child pc  (cost=0.42..5.77 rows=1 width=24) (actual time=0.002..0.002 rows=3 loops=62)
                      Index Cond: ((tree_id = d.tree_id) AND (parent_member_id = d.child_member_id))
                      Heap Fetches: 0
Planning Time: 0.337 ms
Execution Time: 0.604 ms
```
