from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.stage7.stage7_dataset import SEEDS_DIR, load_seed_manifests, validate_seed_manifests, write_manifest_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Stage7 seed manifests and build manifest index.")
    parser.add_argument(
        "--seeds-dir",
        type=Path,
        default=SEEDS_DIR,
        help="Directory containing per-tree seed manifest JSON files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=SEEDS_DIR / "manifest_index.json",
        help="Output path for manifest index JSON.",
    )
    args = parser.parse_args()

    manifests = load_seed_manifests(args.seeds_dir)
    validate_seed_manifests(manifests)
    write_manifest_index(args.output, manifests)
    print(f"Validated {len(manifests)} seed manifests.")
    print(f"Wrote manifest index to: {args.output}")


if __name__ == "__main__":
    main()
