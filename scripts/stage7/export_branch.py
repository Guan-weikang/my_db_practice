from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

ROOT_DIR = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT_DIR / "data" / "stage7" / "exports"

BRANCH_MEMBERS_QUERY = """
WITH RECURSIVE branch_nodes AS (
    SELECT
        m.tree_id,
        m.member_id
    FROM member m
    WHERE m.tree_id = %(tree_id)s
      AND m.member_id = %(root_member_id)s

    UNION

    SELECT
        pc.tree_id,
        pc.child_member_id
    FROM branch_nodes bn
    JOIN parent_child pc
      ON pc.tree_id = bn.tree_id
     AND pc.parent_member_id = bn.member_id
)
SELECT DISTINCT member_id
FROM branch_nodes
ORDER BY member_id;
"""

MEMBER_EXPORT_QUERY = """
SELECT
    member_id,
    tree_id,
    name,
    gender,
    birth_date,
    death_date,
    generation_no,
    generation_name,
    biography,
    is_alive
FROM member
WHERE tree_id = %(tree_id)s
  AND member_id = ANY(%(member_ids)s)
ORDER BY member_id;
"""

PARENT_CHILD_EXPORT_QUERY = """
SELECT
    tree_id,
    parent_member_id,
    child_member_id,
    parent_role
FROM parent_child
WHERE tree_id = %(tree_id)s
  AND parent_member_id = ANY(%(member_ids)s)
  AND child_member_id = ANY(%(member_ids)s)
ORDER BY parent_member_id, child_member_id, parent_role;
"""

MARRIAGE_EXPORT_QUERY = """
SELECT
    tree_id,
    member_id_1,
    member_id_2,
    married_at,
    ended_at,
    status
FROM marriage
WHERE tree_id = %(tree_id)s
  AND member_id_1 = ANY(%(member_ids)s)
  AND member_id_2 = ANY(%(member_ids)s)
ORDER BY member_id_1, member_id_2;
"""


def _write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
      path.write_text("", encoding="utf-8")
      return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a branch closure as CSV files.")
    parser.add_argument("--tree-id", type=int, required=True)
    parser.add_argument("--root-member-id", type=int, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=EXPORT_DIR,
        help="Directory where branch CSV files should be written.",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="PostgreSQL connection string. Defaults to DATABASE_URL env var.",
    )
    args = parser.parse_args()

    if not args.database_url:
        raise SystemExit("DATABASE_URL is required via --database-url or environment variable.")

    branch_dir = args.output_dir / f"tree_{args.tree_id}_root_{args.root_member_id}"
    params = {"tree_id": args.tree_id, "root_member_id": args.root_member_id}

    with psycopg.connect(args.database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(BRANCH_MEMBERS_QUERY, params)
            member_ids = [row["member_id"] for row in cursor.fetchall()]

            export_params = {"tree_id": args.tree_id, "member_ids": member_ids}

            cursor.execute(MEMBER_EXPORT_QUERY, export_params)
            member_rows = cursor.fetchall()

            cursor.execute(PARENT_CHILD_EXPORT_QUERY, export_params)
            parent_child_rows = cursor.fetchall()

            cursor.execute(MARRIAGE_EXPORT_QUERY, export_params)
            marriage_rows = cursor.fetchall()

    _write_rows(branch_dir / "member.csv", member_rows)
    _write_rows(branch_dir / "parent_child.csv", parent_child_rows)
    _write_rows(branch_dir / "marriage.csv", marriage_rows)

    print(f"Exported branch for tree_id={args.tree_id}, root_member_id={args.root_member_id}")
    print(f"Members: {len(member_rows)}")
    print(f"Parent-child rows: {len(parent_child_rows)}")
    print(f"Marriage rows: {len(marriage_rows)}")
    print(f"Output directory: {branch_dir}")


if __name__ == "__main__":
    main()
