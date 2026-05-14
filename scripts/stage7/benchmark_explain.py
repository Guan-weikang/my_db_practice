from __future__ import annotations

import argparse
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

ROOT_DIR = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT_DIR / "data" / "stage7" / "reports"

SEARCH_EXPLAIN_SQL = """
EXPLAIN ANALYZE
SELECT member_id, name
FROM member
WHERE tree_id = %(tree_id)s
  AND name ILIKE '%%' || %(keyword)s || '%%';
"""

FOUR_GEN_EXPLAIN_SQL = """
EXPLAIN ANALYZE
WITH RECURSIVE descendants AS (
    SELECT tree_id, parent_member_id, child_member_id, 1 AS depth
    FROM parent_child
    WHERE tree_id = %(tree_id)s
      AND parent_member_id = %(ancestor_member_id)s

    UNION ALL

    SELECT pc.tree_id, pc.parent_member_id, pc.child_member_id, d.depth + 1
    FROM descendants d
    JOIN parent_child pc
      ON pc.tree_id = d.tree_id
     AND pc.parent_member_id = d.child_member_id
    WHERE d.depth < 4
)
SELECT *
FROM descendants
WHERE depth = 4;
"""

INDEX_SQL = {
    "drop_name_trgm": "DROP INDEX IF EXISTS idx_member_name_trgm;",
    "create_name_trgm": "CREATE INDEX IF NOT EXISTS idx_member_name_trgm ON member USING gin (name gin_trgm_ops);",
    "drop_parent_idx": "DROP INDEX IF EXISTS idx_parent_child_tree_parent;",
    "create_parent_idx": "CREATE INDEX IF NOT EXISTS idx_parent_child_tree_parent ON parent_child(tree_id, parent_member_id);",
}


def _run_explain(cursor: psycopg.Cursor, sql: str, params: dict) -> str:
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    return "\n".join(next(iter(row.values())) for row in rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Stage7 EXPLAIN ANALYZE benchmarks.")
    parser.add_argument("--tree-id", type=int, required=True)
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--ancestor-member-id", type=int, required=True)
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="PostgreSQL connection string. Defaults to DATABASE_URL env var.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPORT_DIR,
        help="Directory where benchmark report files should be written.",
    )
    args = parser.parse_args()

    if not args.database_url:
        raise SystemExit("DATABASE_URL is required via --database-url or environment variable.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.output_dir / f"benchmark_tree_{args.tree_id}.md"

    with psycopg.connect(args.database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            connection.commit()

            cursor.execute(INDEX_SQL["drop_name_trgm"])
            connection.commit()
            search_before = _run_explain(cursor, SEARCH_EXPLAIN_SQL, {"tree_id": args.tree_id, "keyword": args.keyword})

            cursor.execute(INDEX_SQL["create_name_trgm"])
            connection.commit()
            search_after = _run_explain(cursor, SEARCH_EXPLAIN_SQL, {"tree_id": args.tree_id, "keyword": args.keyword})

            cursor.execute(INDEX_SQL["drop_parent_idx"])
            connection.commit()
            branch_before = _run_explain(
                cursor,
                FOUR_GEN_EXPLAIN_SQL,
                {"tree_id": args.tree_id, "ancestor_member_id": args.ancestor_member_id},
            )

            cursor.execute(INDEX_SQL["create_parent_idx"])
            connection.commit()
            branch_after = _run_explain(
                cursor,
                FOUR_GEN_EXPLAIN_SQL,
                {"tree_id": args.tree_id, "ancestor_member_id": args.ancestor_member_id},
            )

    report_path.write_text(
        "\n".join(
            [
                f"# Stage7 Benchmark Report: tree_id={args.tree_id}",
                "",
                f"- keyword: `{args.keyword}`",
                f"- ancestor_member_id: `{args.ancestor_member_id}`",
                "",
                "## Search Before `idx_member_name_trgm`",
                "```sql",
                search_before,
                "```",
                "",
                "## Search After `idx_member_name_trgm`",
                "```sql",
                search_after,
                "```",
                "",
                "## Four-Generation Before `idx_parent_child_tree_parent`",
                "```sql",
                branch_before,
                "```",
                "",
                "## Four-Generation After `idx_parent_child_tree_parent`",
                "```sql",
                branch_after,
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Wrote benchmark report to: {report_path}")


if __name__ == "__main__":
    main()
