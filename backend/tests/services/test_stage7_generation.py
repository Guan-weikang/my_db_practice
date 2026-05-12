from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.stage7.stage7_dataset import (
    TreeSpec,
    build_manifest_index,
    generate_dataset,
    load_seed_manifests,
    summarize_dataset,
    validate_seed_manifests,
)


def test_stage7_seed_manifests_are_valid():
    manifests = load_seed_manifests()
    validate_seed_manifests(manifests)
    index = build_manifest_index(manifests)

    assert index["tree_count"] == 5
    assert {item["tree_code"] for item in index["trees"]} == {
        "han_liu",
        "tang_li",
        "ming_zhu",
        "wuyue_qian",
        "kong_clan",
    }


def test_stage7_generator_can_build_small_dataset():
    manifests = load_seed_manifests()
    specs = (
        TreeSpec("han_liu", "汉朝刘氏", "刘", 120, 12, "small test tree"),
        TreeSpec("kong_clan", "孔氏", "孔", 180, 15, "small test tree"),
        TreeSpec("chen_synthetic", "合成陈氏", "陈", 90, 10, "small test tree"),
    )

    dataset = generate_dataset(manifests, specs=specs, random_seed=42)
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
