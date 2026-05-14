from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

import psycopg
from redis import Redis
from redis.exceptions import RedisError

ROOT_DIR = Path(__file__).resolve().parents[2]
GENERATED_DIR = ROOT_DIR / "data" / "stage7" / "generated"

IMPORT_ORDER = [
    "user_account",
    "family_tree",
    "tree_collaborator",
    "member",
    "parent_child",
    "marriage",
]


def _table_columns(csv_path: Path) -> list[str]:
    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        return next(reader)


def _copy_table(connection: psycopg.Connection, csv_path: Path, table_name: str) -> None:
    columns = _table_columns(csv_path)
    sql = f"COPY {table_name} ({', '.join(columns)}) FROM STDIN WITH (FORMAT csv, HEADER true)"
    with csv_path.open("r", encoding="utf-8") as handle:
        with connection.cursor() as cursor:
            with cursor.copy(sql) as copy:
                while chunk := handle.read(1024 * 1024):
                    copy.write(chunk)


def _delete_stage7_rows(connection: psycopg.Connection) -> None:
    statements = [
        "DELETE FROM marriage WHERE tree_id BETWEEN 7001 AND 7010",
        "DELETE FROM parent_child WHERE tree_id BETWEEN 7001 AND 7010",
        "DELETE FROM member_provenance WHERE tree_id BETWEEN 7001 AND 7010",
        "DELETE FROM member WHERE tree_id BETWEEN 7001 AND 7010",
        "DELETE FROM tree_collaborator WHERE tree_id BETWEEN 7001 AND 7010",
        "DELETE FROM family_tree WHERE tree_id BETWEEN 7001 AND 7010",
        "DELETE FROM user_account WHERE user_id IN (7000001, 7000002, 7000003)",
    ]
    with connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)
    connection.commit()


def _clear_redis_cache(redis_url: str | None) -> None:
    if not redis_url:
        return
    try:
        client = Redis.from_url(redis_url, decode_responses=True)
        keys = list(client.scan_iter("cache:v1:*"))
        if keys:
            client.delete(*keys)
        client.close()
        print(f"Cleared Redis cache keys: {len(keys)}")
    except RedisError as exc:
        print(f"Could not clear Redis cache; continuing. error={exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reimport Stage7 generated CSV files into PostgreSQL.")
    parser.add_argument("--input-dir", type=Path, default=GENERATED_DIR)
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    parser.add_argument("--redis-url", default=os.environ.get("REDIS_URL"))
    parser.add_argument("--skip-redis-clear", action="store_true")
    args = parser.parse_args()

    if not args.database_url:
        raise SystemExit("DATABASE_URL is required via --database-url or environment variable.")

    with psycopg.connect(args.database_url) as connection:
        print("Deleting existing Stage7 rows...")
        _delete_stage7_rows(connection)

        for table_name in IMPORT_ORDER:
            csv_path = args.input_dir / f"{table_name}.csv"
            if not csv_path.exists():
                raise FileNotFoundError(f"Missing CSV file for import: {csv_path}")
            _copy_table(connection, csv_path, table_name)
            connection.commit()
            print(f"Imported {table_name} from {csv_path}")

    if not args.skip_redis_clear:
        _clear_redis_cache(args.redis_url)

    print("Stage7 CSV reimport completed.")


if __name__ == "__main__":
    main()
