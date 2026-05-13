from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.stage7.stage7_dataset import TreeSpec, generate_dataset, load_seed_manifests, write_dataset


def test_stage7_dataset_can_be_written_as_csv(tmp_path):
    manifests = load_seed_manifests()
    specs = (
        TreeSpec("han_liu", "汉朝刘氏", "刘", 60, 8, "pipeline test"),
        TreeSpec("chen_synthetic", "合成陈氏", "陈", 40, 6, "pipeline test"),
    )

    dataset = generate_dataset(manifests, specs=specs, random_seed=7)
    write_dataset(dataset, tmp_path)

    expected_files = {
        "user_account.csv",
        "family_tree.csv",
        "tree_collaborator.csv",
        "member.csv",
        "parent_child.csv",
        "marriage.csv",
        "member_provenance.csv",
    }
    assert {path.name for path in tmp_path.iterdir()} == expected_files
    assert (tmp_path / "member.csv").read_text(encoding="utf-8").startswith("member_id,tree_id,name,gender")


def test_stage7_export_closure_expectation_from_generated_dataset():
    manifests = load_seed_manifests()
    specs = (TreeSpec("han_liu", "汉朝刘氏", "刘", 120, 10, "closure test"),)
    dataset = generate_dataset(manifests, specs=specs, random_seed=9)

    member_ids = {row["member_id"] for row in dataset["member"]}
    for relation in dataset["parent_child"]:
        assert relation["parent_member_id"] in member_ids
        assert relation["child_member_id"] in member_ids
    for marriage in dataset["marriage"]:
        assert marriage["member_id_1"] in member_ids
        assert marriage["member_id_2"] in member_ids
