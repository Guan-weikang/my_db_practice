from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
SEEDS_DIR = ROOT_DIR / "data" / "stage7" / "seeds"
GENERATED_DIR = ROOT_DIR / "data" / "stage7" / "generated"

DEFAULT_CREATOR_USER_ID = 7000001
DEFAULT_READER_USER_ID = 7000002
DEFAULT_TREE_ID_START = 7001
DEFAULT_MEMBER_ID_START = 1000001
DEFAULT_RANDOM_SEED = 20260513

MALE_GIVEN_PARTS = ["伟", "强", "明", "国", "文", "成", "德", "世", "承", "宗", "景", "安"]
FEMALE_GIVEN_PARTS = ["丽", "芳", "敏", "兰", "梅", "华", "玉", "宁", "安", "慧", "清", "雅"]
DUPLICATE_NAME_POOL = ["伟", "敏", "明", "丽", "强", "华"]
GENERATION_TOKENS = list("德仁孝礼义信忠和景承安宁文武昌隆")


@dataclass(frozen=True)
class TreeSpec:
    tree_code: str
    display_name: str
    surname: str
    target_members: int
    target_generations: int
    description: str


DEFAULT_TREE_SPECS: tuple[TreeSpec, ...] = (
    TreeSpec("han_liu", "汉朝刘氏", "刘", 8000, 32, "Historical Han Liu seed tree with synthetic expansion."),
    TreeSpec("tang_li", "唐朝李氏", "李", 10000, 32, "Historical Tang Li seed tree with synthetic expansion."),
    TreeSpec("ming_zhu", "明朝朱氏", "朱", 12000, 33, "Historical Ming Zhu seed tree with synthetic expansion."),
    TreeSpec("wuyue_qian", "吴越钱氏", "钱", 5000, 30, "Historical Wuyue Qian seed tree with synthetic expansion."),
    TreeSpec("kong_clan", "孔氏", "孔", 50000, 40, "Historical Kong seed tree with synthetic expansion."),
    TreeSpec("chen_synthetic", "合成陈氏", "陈", 4000, 30, "Fully synthetic tree for Stage 7 scale padding."),
    TreeSpec("wang_synthetic", "合成王氏", "王", 3500, 30, "Fully synthetic tree for Stage 7 scale padding."),
    TreeSpec("zhang_synthetic", "合成张氏", "张", 3000, 30, "Fully synthetic tree for Stage 7 scale padding."),
    TreeSpec("lin_synthetic", "合成林氏", "林", 2500, 30, "Fully synthetic tree for Stage 7 scale padding."),
    TreeSpec("zhao_synthetic", "合成赵氏", "赵", 2000, 30, "Fully synthetic tree for Stage 7 scale padding."),
)


def load_seed_manifests(seeds_dir: Path = SEEDS_DIR) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    for path in sorted(seeds_dir.glob("*.json")):
        if path.name == "manifest_index.json":
            continue
        manifests.append(json.loads(path.read_text(encoding="utf-8")))
    return manifests


def validate_seed_manifests(manifests: list[dict[str, Any]]) -> None:
    seen_tree_codes: set[str] = set()
    for manifest in manifests:
        tree_code = manifest["tree_code"]
        if tree_code in seen_tree_codes:
            raise ValueError(f"Duplicate tree_code in manifests: {tree_code}")
        seen_tree_codes.add(tree_code)

        member_ids = {member["member_code"] for member in manifest["members"]}
        if len(member_ids) != len(manifest["members"]):
            raise ValueError(f"Duplicate member_code in manifest: {tree_code}")

        for relation in manifest.get("parent_child", []):
            if relation["parent_member_code"] not in member_ids:
                raise ValueError(f"Unknown parent_member_code in {tree_code}: {relation['parent_member_code']}")
            if relation["child_member_code"] not in member_ids:
                raise ValueError(f"Unknown child_member_code in {tree_code}: {relation['child_member_code']}")
            if relation["parent_role"] not in {"father", "mother"}:
                raise ValueError(f"Invalid parent_role in {tree_code}: {relation['parent_role']}")

        for marriage in manifest.get("marriages", []):
            if marriage["member_code_1"] not in member_ids or marriage["member_code_2"] not in member_ids:
                raise ValueError(f"Unknown member_code in marriage of {tree_code}")


def build_manifest_index(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    validate_seed_manifests(manifests)
    return {
        "schema_version": 1,
        "tree_count": len(manifests),
        "trees": [
            {
                "tree_code": manifest["tree_code"],
                "display_name": manifest["display_name"],
                "surname": manifest["surname"],
                "seed_member_count": len(manifest["members"]),
                "parent_child_count": len(manifest.get("parent_child", [])),
                "marriage_count": len(manifest.get("marriages", [])),
                "historical_basis": manifest["historical_basis"],
            }
            for manifest in manifests
        ],
    }


def write_manifest_index(output_path: Path, manifests: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(build_manifest_index(manifests), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _tree_spec_map(specs: tuple[TreeSpec, ...]) -> dict[str, TreeSpec]:
    return {spec.tree_code: spec for spec in specs}


def _normalize_marriage_members(member_id_1: int, member_id_2: int) -> tuple[int, int]:
    if member_id_1 < member_id_2:
        return member_id_1, member_id_2
    return member_id_2, member_id_1


def _format_birth_date(year: int | None) -> str:
    if year is None or year <= 0 or year > 9999:
        return ""
    return f"{year:04d}-01-01"


def _format_death_date(year: int | None) -> str:
    if year is None or year <= 0 or year > 9999:
        return ""
    return f"{year:04d}-12-31"


def _generation_token(generation_no: int) -> str:
    return GENERATION_TOKENS[(generation_no - 1) % len(GENERATION_TOKENS)]


def _generated_name(rng: random.Random, surname: str, gender: str, generation_no: int, duplicate_rate: float) -> str:
    if rng.random() < duplicate_rate:
        return surname + rng.choice(DUPLICATE_NAME_POOL)
    given_parts = MALE_GIVEN_PARTS if gender == "male" else FEMALE_GIVEN_PARTS
    if rng.random() < 0.6:
        return surname + _generation_token(generation_no) + rng.choice(given_parts)
    return surname + rng.choice(given_parts) + rng.choice(given_parts)


def _default_generation_targets(total_members: int, generations: int) -> list[int]:
    weights = [max(1, min(index + 1, generations - index)) for index in range(generations)]
    total_weight = sum(weights)
    counts = [1] * generations
    remaining = total_members - generations
    for index, weight in enumerate(weights):
        if remaining <= 0:
            break
        share = (remaining * weight) // total_weight
        counts[index] += share
    assigned = sum(counts)
    pointer = generations - 1
    while assigned < total_members:
        counts[pointer] += 1
        assigned += 1
        pointer = max(0, pointer - 1)
    while assigned > total_members:
        if counts[pointer] > 1:
            counts[pointer] -= 1
            assigned -= 1
        pointer = (pointer - 1) % generations
    return counts


def _make_user_rows() -> list[dict[str, Any]]:
    return [
        {
            "user_id": DEFAULT_CREATOR_USER_ID,
            "username": "stage7_importer",
            "password_hash": "stage7-import-only",
            "display_name": "Stage7 Importer",
            "email": "stage7_importer@example.com",
            "status": "active",
        },
        {
            "user_id": DEFAULT_READER_USER_ID,
            "username": "stage7_reader",
            "password_hash": "stage7-read-only",
            "display_name": "Stage7 Reader",
            "email": "stage7_reader@example.com",
            "status": "active",
        },
    ]


def generate_dataset(
    manifests: list[dict[str, Any]],
    *,
    specs: tuple[TreeSpec, ...] = DEFAULT_TREE_SPECS,
    random_seed: int = DEFAULT_RANDOM_SEED,
    tree_id_start: int = DEFAULT_TREE_ID_START,
    member_id_start: int = DEFAULT_MEMBER_ID_START,
) -> dict[str, list[dict[str, Any]]]:
    validate_seed_manifests(manifests)
    manifest_map = {manifest["tree_code"]: manifest for manifest in manifests}
    spec_map = _tree_spec_map(specs)
    rng = random.Random(random_seed)

    dataset = {
        "user_account": _make_user_rows(),
        "family_tree": [],
        "tree_collaborator": [],
        "member": [],
        "parent_child": [],
        "marriage": [],
        "member_provenance": [],
    }

    next_tree_id = tree_id_start
    next_member_id = member_id_start

    for spec in specs:
        tree_id = next_tree_id
        next_tree_id += 1
        dataset["family_tree"].append(
            {
                "tree_id": tree_id,
                "tree_name": spec.display_name,
                "surname": spec.surname,
                "compiled_at": date(2026, 5, 13).isoformat(),
                "creator_user_id": DEFAULT_CREATOR_USER_ID,
                "description": spec.description,
            }
        )
        dataset["tree_collaborator"].append(
            {
                "tree_id": tree_id,
                "user_id": DEFAULT_READER_USER_ID,
                "access_role": "reader",
                "invited_by": DEFAULT_CREATOR_USER_ID,
                "status": "active",
            }
        )

        members_by_generation: dict[int, list[dict[str, Any]]] = {}
        marriage_pairs: set[tuple[int, int]] = set()
        member_code_to_id: dict[str, int] = {}
        existing_parent_roles: dict[int, set[str]] = {}
        manifest = manifest_map.get(spec.tree_code)

        if manifest is not None:
            for member in manifest["members"]:
                member_id = next_member_id
                next_member_id += 1
                generation_no = int(member.get("generation_no") or 1)
                row = {
                    "member_id": member_id,
                    "tree_id": tree_id,
                    "name": member["name"],
                    "gender": member["gender"],
                    "birth_date": _format_birth_date(member.get("birth_year")),
                    "death_date": _format_death_date(member.get("death_year")),
                    "generation_no": generation_no,
                    "generation_name": member.get("generation_name") or "",
                    "biography": f"Historical seed node for {spec.display_name}.",
                    "is_alive": "false" if member.get("death_year") else "true",
                }
                dataset["member"].append(row)
                members_by_generation.setdefault(generation_no, []).append(row)
                member_code_to_id[member["member_code"]] = member_id
                dataset["member_provenance"].append(
                    {
                        "member_id": member_id,
                        "tree_id": tree_id,
                        "tree_code": spec.tree_code,
                        "node_type": "seed",
                        "historical_real": "true",
                        "seed_member_code": member["member_code"],
                        "source_system": member.get("source_system", ""),
                        "source_url": member.get("source_url", ""),
                        "confidence": member.get("confidence", ""),
                    }
                )

            for relation in manifest.get("parent_child", []):
                child_member_id = member_code_to_id[relation["child_member_code"]]
                dataset["parent_child"].append(
                    {
                        "tree_id": tree_id,
                        "parent_member_id": member_code_to_id[relation["parent_member_code"]],
                        "child_member_id": child_member_id,
                        "parent_role": relation["parent_role"],
                    }
                )
                existing_parent_roles.setdefault(child_member_id, set()).add(relation["parent_role"])

            for marriage in manifest.get("marriages", []):
                member_id_1, member_id_2 = _normalize_marriage_members(
                    member_code_to_id[marriage["member_code_1"]],
                    member_code_to_id[marriage["member_code_2"]],
                )
                marriage_pairs.add((member_id_1, member_id_2))
                dataset["marriage"].append(
                    {
                        "tree_id": tree_id,
                        "member_id_1": member_id_1,
                        "member_id_2": member_id_2,
                        "married_at": marriage.get("married_at", ""),
                        "ended_at": marriage.get("ended_at", ""),
                        "status": marriage.get("status", "active"),
                    }
                )

        target_counts = _default_generation_targets(spec.target_members, spec.target_generations)
        for generation_no in range(1, spec.target_generations + 1):
            members_by_generation.setdefault(generation_no, [])

        for generation_no, target in enumerate(target_counts, start=1):
            while len(members_by_generation[generation_no]) < target:
                gender = "male" if len(members_by_generation[generation_no]) % 2 == 0 else "female"
                member_id = next_member_id
                next_member_id += 1
                birth_year = 1200 + generation_no * 18 + rng.randint(-4, 4)
                row = {
                    "member_id": member_id,
                    "tree_id": tree_id,
                    "name": _generated_name(rng, spec.surname, gender, generation_no, duplicate_rate=0.12),
                    "gender": gender,
                    "birth_date": _format_birth_date(birth_year),
                    "death_date": "",
                    "generation_no": generation_no,
                    "generation_name": "",
                    "biography": f"Generated descendant for Stage7 dataset: {spec.display_name}.",
                    "is_alive": "true",
                }
                dataset["member"].append(row)
                members_by_generation[generation_no].append(row)
                dataset["member_provenance"].append(
                    {
                        "member_id": member_id,
                        "tree_id": tree_id,
                        "tree_code": spec.tree_code,
                        "node_type": "generated",
                        "historical_real": "false",
                        "seed_member_code": "",
                        "source_system": "synthetic_generator",
                        "source_url": "",
                        "confidence": "generated",
                    }
                )

        for generation_no in range(1, spec.target_generations):
            fathers = [row for row in members_by_generation[generation_no] if row["gender"] == "male"]
            mothers = [row for row in members_by_generation[generation_no] if row["gender"] == "female"]
            if not fathers:
                raise ValueError(f"Generation {generation_no} in {spec.tree_code} has no male members")
            if not mothers:
                raise ValueError(f"Generation {generation_no} in {spec.tree_code} has no female members")

            father_pointer = 0
            mother_pointer = 0
            for child in members_by_generation[generation_no + 1]:
                father = fathers[father_pointer % len(fathers)]
                mother = mothers[mother_pointer % len(mothers)]
                father_pointer += 1
                mother_pointer += 1

                child_roles = existing_parent_roles.setdefault(child["member_id"], set())
                if "father" not in child_roles:
                    dataset["parent_child"].append(
                        {
                            "tree_id": tree_id,
                            "parent_member_id": father["member_id"],
                            "child_member_id": child["member_id"],
                            "parent_role": "father",
                        }
                    )
                    child_roles.add("father")
                if "mother" not in child_roles:
                    dataset["parent_child"].append(
                        {
                            "tree_id": tree_id,
                            "parent_member_id": mother["member_id"],
                            "child_member_id": child["member_id"],
                            "parent_role": "mother",
                        }
                    )
                    child_roles.add("mother")

                ordered_marriage = _normalize_marriage_members(father["member_id"], mother["member_id"])
                if ordered_marriage not in marriage_pairs:
                    marriage_pairs.add(ordered_marriage)
                    married_year = max(1, 1200 + generation_no * 18 + 18)
                    dataset["marriage"].append(
                        {
                            "tree_id": tree_id,
                            "member_id_1": ordered_marriage[0],
                            "member_id_2": ordered_marriage[1],
                            "married_at": _format_birth_date(married_year),
                            "ended_at": "",
                            "status": "active",
                        }
                    )

    return dataset


def write_dataset(dataset: dict[str, list[dict[str, Any]]], output_dir: Path = GENERATED_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for table_name, rows in dataset.items():
        path = output_dir / f"{table_name}.csv"
        if not rows:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)


def summarize_dataset(dataset: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    return {table_name: len(rows) for table_name, rows in dataset.items()}
