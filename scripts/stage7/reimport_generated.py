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


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if database_url.startswith("postgresql+psycopg://"):
        return database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    return database_url


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


def _table_exists(connection: psycopg.Connection, table_name: str) -> bool:
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass(%s)", (table_name,))
        return cursor.fetchone()[0] is not None


def _delete_stage7_rows(connection: psycopg.Connection) -> None:
    statements = [
        ("marriage", "DELETE FROM marriage WHERE tree_id BETWEEN 7001 AND 7010"),
        ("parent_child", "DELETE FROM parent_child WHERE tree_id BETWEEN 7001 AND 7010"),
        ("member_provenance", "DELETE FROM member_provenance WHERE tree_id BETWEEN 7001 AND 7010"),
        ("member", "DELETE FROM member WHERE tree_id BETWEEN 7001 AND 7010"),
        ("tree_collaborator", "DELETE FROM tree_collaborator WHERE tree_id BETWEEN 7001 AND 7010"),
        ("family_tree", "DELETE FROM family_tree WHERE tree_id BETWEEN 7001 AND 7010"),
        ("user_account", "DELETE FROM user_account WHERE user_id IN (7000001, 7000002, 7000003)"),
    ]
    with connection.cursor() as cursor:
        for table_name, statement in statements:
            if not _table_exists(connection, table_name):
                print(f"Skipping cleanup for missing table: {table_name}")
                continue
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


def _set_replication_role(connection: psycopg.Connection, role: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(f"SET session_replication_role = {role}")
    connection.commit()


def _analyze_stage7_tables(connection: psycopg.Connection) -> None:
    table_names = ["user_account", "family_tree", "tree_collaborator", "member", "parent_child", "marriage"]
    with connection.cursor() as cursor:
        for table_name in table_names:
            if not _table_exists(connection, table_name):
                continue
            cursor.execute(f"ANALYZE {table_name}")
    connection.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Reimport Stage7 generated CSV files into PostgreSQL.")
    parser.add_argument("--input-dir", type=Path, default=GENERATED_DIR)
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    parser.add_argument("--redis-url", default=os.environ.get("REDIS_URL"))
    parser.add_argument("--skip-redis-clear", action="store_true")
    args = parser.parse_args()

    if not args.database_url:
        raise SystemExit("DATABASE_URL is required via --database-url or environment variable.")

    normalized_database_url = _normalize_database_url(args.database_url)

    with psycopg.connect(normalized_database_url) as connection:
        print("Deleting existing Stage7 rows...")
        _delete_stage7_rows(connection)

        replication_role_enabled = False
        try:
            try:
                _set_replication_role(connection, "replica")
                replication_role_enabled = True
                print("Enabled session_replication_role=replica for faster Stage7 import.")
            except Exception:
                connection.rollback()
                print("Could not enable session_replication_role=replica; continuing with normal constraints.")

            for table_name in IMPORT_ORDER:
                if not _table_exists(connection, table_name):
                    print(f"Skipping import for missing table: {table_name}")
                    continue
                csv_path = args.input_dir / f"{table_name}.csv"
                if not csv_path.exists():
                    raise FileNotFoundError(f"Missing CSV file for import: {csv_path}")
                _copy_table(connection, csv_path, table_name)
                connection.commit()
                print(f"Imported {table_name} from {csv_path}")
        finally:
            if replication_role_enabled:
                _set_replication_role(connection, "origin")
                print("Restored session_replication_role=origin.")

        _analyze_stage7_tables(connection)
        print("Analyzed Stage7 tables after import.")

    if not args.skip_redis_clear:
        _clear_redis_cache(args.redis_url)

    print("Stage7 CSV reimport completed.")


if __name__ == "__main__":
    main()
