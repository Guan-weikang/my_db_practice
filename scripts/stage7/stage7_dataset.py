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
DEFAULT_COLLABORATOR_USER_ID = 7000003
DEFAULT_TREE_ID_START = 7001
DEFAULT_MEMBER_ID_START = 1000001
DEFAULT_RANDOM_SEED = 20260513
CURRENT_YEAR = 2026
PASSWORD123_HASH = "$argon2id$v=19$m=65536,t=3,p=4$TvtS/znYf4UUnty9hmDdPQ$KYQ+1IAxobgmLJvo46lOfQR1kpp9HRkuUlClDLA9tRU"

MALE_GIVEN_PARTS = ["伟", "强", "明", "国", "文", "成", "德", "世", "承", "宗", "景", "安"]
FEMALE_GIVEN_PARTS = ["丽", "芳", "敏", "兰", "梅", "华", "玉", "宁", "安", "慧", "清", "雅"]
DUPLICATE_NAME_POOL = ["伟", "敏", "明", "丽", "强", "华"]
GENERATION_TOKENS = list("德仁孝礼义信忠和景承安宁文武昌隆绍启盛延")


@dataclass(frozen=True)
class TreeSpec:
    tree_code: str
    display_name: str
    surname: str
    target_members: int
    target_generations: int
    description: str
    latest_generation_birth_year: int
    generation_gap: int
    duplicate_rate: float = 0.12


DEFAULT_TREE_SPECS: tuple[TreeSpec, ...] = (
    TreeSpec("han_liu", "汉朝刘氏", "刘", 8000, 32, "Fully synthetic Han-Liu themed tree.", 2008, 22),
    TreeSpec("tang_li", "唐朝李氏", "李", 10000, 32, "Fully synthetic Tang-Li themed tree.", 2006, 22),
    TreeSpec("ming_zhu", "明朝朱氏", "朱", 12000, 33, "Fully synthetic Ming-Zhu themed tree.", 2005, 22),
    TreeSpec("wuyue_qian", "吴越钱氏", "钱", 5000, 30, "Fully synthetic Wuyue-Qian themed tree.", 2007, 21),
    TreeSpec("kong_clan", "孔氏", "孔", 55000, 40, "Fully synthetic Kong-themed large benchmark tree.", 2003, 22),
    TreeSpec("chen_synthetic", "合成陈氏", "陈", 4000, 30, "Fully synthetic Chen tree.", 2010, 21),
    TreeSpec("wang_synthetic", "合成王氏", "王", 3500, 30, "Fully synthetic Wang tree.", 2011, 21),
    TreeSpec("zhang_synthetic", "合成张氏", "张", 3000, 30, "Fully synthetic Zhang tree.", 2010, 21),
    TreeSpec("lin_synthetic", "合成林氏", "林", 2500, 30, "Fully synthetic Lin tree.", 2012, 21),
    TreeSpec("zhao_synthetic", "合成赵氏", "赵", 2000, 30, "Fully synthetic Zhao tree.", 2011, 21),
)


def load_tree_specs() -> tuple[TreeSpec, ...]:
    return DEFAULT_TREE_SPECS


def build_manifest_index(specs: tuple[TreeSpec, ...] = DEFAULT_TREE_SPECS) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "mode": "fully_synthetic",
        "tree_count": len(specs),
        "trees": [
            {
                "tree_code": spec.tree_code,
                "display_name": spec.display_name,
                "surname": spec.surname,
                "target_members": spec.target_members,
                "target_generations": spec.target_generations,
                "latest_generation_birth_year": spec.latest_generation_birth_year,
                "generation_gap": spec.generation_gap,
                "duplicate_rate": spec.duplicate_rate,
            }
            for spec in specs
        ],
    }


def write_manifest_index(output_path: Path, specs: tuple[TreeSpec, ...] = DEFAULT_TREE_SPECS) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(build_manifest_index(specs), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize_marriage_members(member_id_1: int, member_id_2: int) -> tuple[int, int]:
    if member_id_1 < member_id_2:
        return member_id_1, member_id_2
    return member_id_2, member_id_1


def _format_date(year: int, month: int = 1, day: int = 1) -> str:
    year = min(max(year, 1), 9999)
    return f"{year:04d}-{month:02d}-{day:02d}"


def _generation_token(generation_no: int) -> str:
    return GENERATION_TOKENS[(generation_no - 1) % len(GENERATION_TOKENS)]


def _generated_name(rng: random.Random, surname: str, gender: str, generation_no: int, duplicate_rate: float) -> str:
    if rng.random() < duplicate_rate:
        return surname + rng.choice(DUPLICATE_NAME_POOL)
    given_parts = MALE_GIVEN_PARTS if gender == "male" else FEMALE_GIVEN_PARTS
    if rng.random() < 0.65:
        return surname + _generation_token(generation_no) + rng.choice(given_parts)
    return surname + rng.choice(given_parts) + rng.choice(given_parts)


def _default_generation_targets(total_members: int, generations: int) -> list[int]:
    if generations < 1:
        raise ValueError("generations must be positive")
    weights = [max(1, min(index + 1, generations - index)) for index in range(1, generations)]
    total_weight = sum(weights) if weights else 1
    counts = [1] * generations
    counts[0] = 2
    remaining = total_members - (generations + 1)
    for offset, weight in enumerate(weights, start=1):
        if remaining <= 0:
            break
        share = (remaining * weight) // total_weight
        counts[offset] += share
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


def _generation_birth_year(spec: TreeSpec, generation_no: int, rng: random.Random) -> int:
    year = spec.latest_generation_birth_year - (spec.target_generations - generation_no) * spec.generation_gap
    return year + rng.randint(-3, 3)


def _life_profile(birth_year: int, rng: random.Random, current_year: int = CURRENT_YEAR) -> tuple[bool, str]:
    current_age = current_year - birth_year
    if current_age >= 96:
        alive = False
    elif current_age >= 91:
        alive = rng.random() < 0.02
    elif current_age >= 81:
        alive = rng.random() < 0.12
    elif current_age >= 71:
        alive = rng.random() < 0.35
    elif current_age >= 61:
        alive = rng.random() < 0.72
    else:
        alive = rng.random() < 0.96

    if alive:
        return True, ""

    max_age = min(max(current_age - 1, 18), 109)
    mode_age = 68 if birth_year < 1800 else 74 if birth_year < 1950 else 79
    mode_age = min(mode_age, max_age)
    death_age = int(round(rng.triangular(18, max_age, mode_age)))
    death_age = max(18, min(max_age, death_age))
    death_year = min(current_year - 1, birth_year + death_age)
    return False, _format_date(death_year, 12, 31)


def _make_user_rows() -> list[dict[str, Any]]:
    return [
        {
            "user_id": DEFAULT_CREATOR_USER_ID,
            "username": "stage7_importer",
            "password_hash": PASSWORD123_HASH,
            "display_name": "Stage7 Importer",
            "email": "stage7_importer@example.com",
            "status": "active",
        },
        {
            "user_id": DEFAULT_READER_USER_ID,
            "username": "stage7_reader",
            "password_hash": PASSWORD123_HASH,
            "display_name": "Stage7 Reader",
            "email": "stage7_reader@example.com",
            "status": "active",
        },
        {
            "user_id": DEFAULT_COLLABORATOR_USER_ID,
            "username": "stage7_collaborator",
            "password_hash": PASSWORD123_HASH,
            "display_name": "Stage7 Collaborator",
            "email": "stage7_collaborator@example.com",
            "status": "active",
        },
    ]


def generate_dataset(
    *,
    specs: tuple[TreeSpec, ...] = DEFAULT_TREE_SPECS,
    random_seed: int = DEFAULT_RANDOM_SEED,
    tree_id_start: int = DEFAULT_TREE_ID_START,
    member_id_start: int = DEFAULT_MEMBER_ID_START,
    current_year: int = CURRENT_YEAR,
) -> dict[str, list[dict[str, Any]]]:
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
        dataset["tree_collaborator"].append(
            {
                "tree_id": tree_id,
                "user_id": DEFAULT_COLLABORATOR_USER_ID,
                "access_role": "collaborator",
                "invited_by": DEFAULT_CREATOR_USER_ID,
                "status": "active",
            }
        )

        members_by_generation: dict[int, list[dict[str, Any]]] = {generation_no: [] for generation_no in range(1, spec.target_generations + 1)}
        target_counts = _default_generation_targets(spec.target_members, spec.target_generations)
        marriage_pairs: set[tuple[int, int]] = set()

        for generation_no, target in enumerate(target_counts, start=1):
            for member_index in range(target):
                gender = "male" if member_index % 2 == 0 else "female"
                member_id = next_member_id
                next_member_id += 1
                birth_year = _generation_birth_year(spec, generation_no, rng)
                is_alive, death_date = _life_profile(birth_year, rng, current_year=current_year)
                row = {
                    "member_id": member_id,
                    "tree_id": tree_id,
                    "name": _generated_name(rng, spec.surname, gender, generation_no, duplicate_rate=spec.duplicate_rate),
                    "gender": gender,
                    "birth_date": _format_date(birth_year, 1, 1),
                    "death_date": death_date,
                    "generation_no": generation_no,
                    "generation_name": _generation_token(generation_no),
                    "biography": f"Rule-generated Stage7 member for {spec.display_name}.",
                    "is_alive": "true" if is_alive else "false",
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
                        "rule_profile": "stage7_synthetic_v2",
                        "latest_generation_birth_year": spec.latest_generation_birth_year,
                        "generation_gap": spec.generation_gap,
                    }
                )

        for generation_no in range(1, spec.target_generations):
            fathers = [row for row in members_by_generation[generation_no] if row["gender"] == "male"]
            mothers = [row for row in members_by_generation[generation_no] if row["gender"] == "female"]
            children = members_by_generation[generation_no + 1]

            if not fathers or not mothers:
                raise ValueError(f"Generation {generation_no} in {spec.tree_code} does not have both genders")

            father_pointer = 0
            mother_pointer = 0
            for child in children:
                father = fathers[father_pointer % len(fathers)]
                mother = mothers[mother_pointer % len(mothers)]
                father_pointer += 1
                mother_pointer += 1

                dataset["parent_child"].append(
                    {
                        "tree_id": tree_id,
                        "parent_member_id": father["member_id"],
                        "child_member_id": child["member_id"],
                        "parent_role": "father",
                    }
                )
                dataset["parent_child"].append(
                    {
                        "tree_id": tree_id,
                        "parent_member_id": mother["member_id"],
                        "child_member_id": child["member_id"],
                        "parent_role": "mother",
                    }
                )

                ordered_marriage = _normalize_marriage_members(father["member_id"], mother["member_id"])
                if ordered_marriage not in marriage_pairs:
                    marriage_pairs.add(ordered_marriage)
                    father_birth_year = int(father["birth_date"][:4])
                    mother_birth_year = int(mother["birth_date"][:4])
                    child_birth_year = int(child["birth_date"][:4])
                    married_year = min(child_birth_year - 1, max(father_birth_year, mother_birth_year) + 18 + rng.randint(0, 8))

                    father_death_year = int(father["death_date"][:4]) if father["death_date"] else None
                    mother_death_year = int(mother["death_date"][:4]) if mother["death_date"] else None
                    ended_year_candidates = [year for year in [father_death_year, mother_death_year] if year is not None]
                    if ended_year_candidates:
                        ended_year = max(married_year, min(ended_year_candidates))
                        status = "ended"
                        ended_at = _format_date(ended_year, 12, 31)
                    else:
                        status = "active"
                        ended_at = ""

                    dataset["marriage"].append(
                        {
                            "tree_id": tree_id,
                            "member_id_1": ordered_marriage[0],
                            "member_id_2": ordered_marriage[1],
                            "married_at": _format_date(married_year, 1, 1),
                            "ended_at": ended_at,
                            "status": status,
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
