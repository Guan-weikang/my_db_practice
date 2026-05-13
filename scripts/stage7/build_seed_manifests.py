from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.stage7.stage7_dataset import SEEDS_DIR, load_tree_specs, write_manifest_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Stage7 synthetic tree profile index.")
    parser.add_argument(
        "--output",
        type=Path,
        default=SEEDS_DIR / "manifest_index.json",
        help="Output path for synthetic tree profile index JSON.",
    )
    args = parser.parse_args()

    specs = load_tree_specs()
    write_manifest_index(args.output, specs)
    print(f"Built synthetic profile index for {len(specs)} trees.")
    print(f"Wrote profile index to: {args.output}")


if __name__ == "__main__":
    main()
