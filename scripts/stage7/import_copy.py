from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

import psycopg

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Stage7 generated CSV files into PostgreSQL using COPY.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=GENERATED_DIR,
        help="Directory containing generated Stage7 CSV files.",
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="PostgreSQL connection string. Defaults to DATABASE_URL env var.",
    )
    args = parser.parse_args()

    if not args.database_url:
        raise SystemExit("DATABASE_URL is required via --database-url or environment variable.")

    with psycopg.connect(args.database_url) as connection:
        for table_name in IMPORT_ORDER:
            csv_path = args.input_dir / f"{table_name}.csv"
            if not csv_path.exists():
                raise FileNotFoundError(f"Missing CSV file for import: {csv_path}")
            _copy_table(connection, csv_path, table_name)
            connection.commit()
            print(f"Imported {table_name} from {csv_path}")


if __name__ == "__main__":
    main()
