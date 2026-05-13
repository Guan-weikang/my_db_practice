from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.stage7.stage7_dataset import build_manifest_index, generate_dataset, load_tree_specs, summarize_dataset


def test_stage7_tree_profiles_are_valid():
    specs = load_tree_specs()
    index = build_manifest_index(specs)

    assert index["tree_count"] == 10
    assert index["mode"] == "fully_synthetic"
    kong = next(item for item in index["trees"] if item["tree_code"] == "kong_clan")
    assert kong["target_members"] == 55000
    assert {item["tree_code"] for item in index["trees"]} == {
        "han_liu",
        "tang_li",
        "ming_zhu",
        "wuyue_qian",
        "kong_clan",
        "chen_synthetic",
        "wang_synthetic",
        "zhang_synthetic",
        "lin_synthetic",
        "zhao_synthetic",
    }


def test_stage7_generator_can_build_small_dataset_with_life_rules():
    specs = (
        load_tree_specs()[0],
        load_tree_specs()[4],
        load_tree_specs()[5],
    )
    specs = tuple(
        spec.__class__(
            spec.tree_code,
            spec.display_name,
            spec.surname,
            120 if index == 0 else 180 if index == 1 else 90,
            12 if index == 0 else 15 if index == 1 else 10,
            "small test tree",
            spec.latest_generation_birth_year,
            spec.generation_gap,
            spec.duplicate_rate,
        )
        for index, spec in enumerate(specs)
    )

    dataset = generate_dataset(specs=specs, random_seed=42)
    summary = summarize_dataset(dataset)

    assert summary["family_tree"] == 3
    assert summary["member"] == 390
    assert summary["user_account"] == 2
    assert summary["tree_collaborator"] == 3
    assert summary["parent_child"] > 0
    assert summary["marriage"] > 0
    assert summary["member_provenance"] == summary["member"]

    member_ids = {row["member_id"] for row in dataset["member"]}
    tree_ids = {row["tree_id"] for row in dataset["family_tree"]}
    assert len(member_ids) == summary["member"]
    assert len(tree_ids) == 3

    alive_over_90 = 0
    dead_count = 0
    for row in dataset["member"]:
        birth_year = int(row["birth_date"][:4])
        assert row["birth_date"]
        age_2026 = 2026 - birth_year
        if row["is_alive"] == "true":
            assert row["death_date"] == ""
            assert age_2026 <= 110
            if age_2026 >= 90:
                alive_over_90 += 1
        else:
            dead_count += 1
            assert row["death_date"]
            death_year = int(row["death_date"][:4])
            assert death_year >= birth_year
            assert death_year <= 2025

    assert dead_count > summary["member"] // 2
    assert alive_over_90 <= 2

    gen1_per_tree: dict[int, int] = {}
    for row in dataset["member"]:
        if row["generation_no"] == 1:
            gen1_per_tree[row["tree_id"]] = gen1_per_tree.get(row["tree_id"], 0) + 1
    assert set(gen1_per_tree.values()) == {2}

    for row in dataset["parent_child"]:
        assert row["tree_id"] in tree_ids
        assert row["parent_member_id"] in member_ids
        assert row["child_member_id"] in member_ids
        assert row["parent_member_id"] != row["child_member_id"]
        assert row["parent_role"] in {"father", "mother"}

    for row in dataset["marriage"]:
        assert row["tree_id"] in tree_ids
        assert row["member_id_1"] in member_ids
        assert row["member_id_2"] in member_ids
        assert row["member_id_1"] < row["member_id_2"]
        assert row["married_at"]
        if row["status"] == "ended":
            assert row["ended_at"]
