from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.stage7.stage7_dataset import (
    GENERATED_DIR,
    DEFAULT_RANDOM_SEED,
    generate_dataset,
    load_tree_specs,
    summarize_dataset,
    write_dataset,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Stage7 synthetic dataset from curated seed manifests.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=GENERATED_DIR,
        help="Directory where CSV files should be written.",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help="Deterministic random seed for synthetic expansion.",
    )
    args = parser.parse_args()

    specs = load_tree_specs()
    dataset = generate_dataset(specs=specs, random_seed=args.random_seed)
    write_dataset(dataset, args.output_dir)
    summary = summarize_dataset(dataset)

    print("Generated Stage7 dataset:")
    for table_name, count in summary.items():
        print(f"  - {table_name}: {count}")
    print(f"CSV output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
