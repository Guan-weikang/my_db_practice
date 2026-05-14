import asyncio
from datetime import date

from seed_stage4_manual_test_data import (
    AsyncSessionLocal,
    Member,
    USERS,
    ensure_marriage,
    ensure_member,
    ensure_parent_child,
    get_or_create_tree,
    main as seed_stage4_main,
    select,
    touch_tree,
    UserAccount,
    FamilyTree,
)


async def _get_user_by_username(session, username: str) -> UserAccount:
    result = await session.execute(select(UserAccount).where(UserAccount.username == username))
    return result.scalar_one()


async def _get_tree_by_creator_and_name(session, creator_user_id: int, tree_name: str) -> FamilyTree:
    tree = await get_or_create_tree(
        session,
        creator_user_id=creator_user_id,
        tree_name=tree_name,
        surname="Chen" if "Managed" in tree_name or "Empty" in tree_name else "Li",
        description="Stage5 query manual testing tree.",
    )
    return tree


async def _ensure_duplicate_name_member(
    session,
    *,
    tree_id: int,
    name: str,
    gender: str,
    birth_date: date,
    generation_no: int,
    generation_name: str,
    biography: str,
) -> Member:
    result = await session.execute(
        select(Member).where(
            Member.tree_id == tree_id,
            Member.name == name,
            Member.birth_date == birth_date,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        member = Member(
            tree_id=tree_id,
            name=name,
            gender=gender,
            birth_date=birth_date,
            is_alive=True,
            generation_no=generation_no,
            generation_name=generation_name,
            biography=biography,
        )
        session.add(member)
    else:
        member.gender = gender
        member.birth_date = birth_date
        member.is_alive = True
        member.generation_no = generation_no
        member.generation_name = generation_name
        member.biography = biography
    await session.flush()
    return member


async def main() -> None:
    await seed_stage4_main()

    async with AsyncSessionLocal() as session:
        creator = await _get_user_by_username(session, "stage3_creator")
        viewer = await _get_user_by_username(session, "stage3_viewer")

        managed_tree = await _get_tree_by_creator_and_name(session, creator.user_id, "Stage3 Managed Tree")
        public_tree = await _get_tree_by_creator_and_name(session, viewer.user_id, "Stage3 Public Read Tree")

        await touch_tree(managed_tree)
        await touch_tree(public_tree)

        root = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage4 Root Patriarch",
            gender="male",
            birth_date=date(1938, 3, 12),
            death_date=date(2012, 5, 20),
            is_alive=False,
            generation_no=1,
            generation_name="德",
            biography="Three-generation root sample for stage4 and stage5 testing.",
        )
        matriarch = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage4 Root Matriarch",
            gender="female",
            birth_date=date(1942, 7, 1),
            is_alive=True,
            generation_no=1,
            generation_name="德",
            biography="Root matriarch sample for spouse and parent relationships.",
        )
        branch_son = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage4 Branch Son",
            gender="male",
            birth_date=date(1968, 6, 6),
            is_alive=True,
            generation_no=2,
            generation_name="仁",
            biography="Second generation branch sample.",
        )
        daughter_in_law = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage4 Daughter In Law",
            gender="female",
            birth_date=date(1970, 8, 18),
            is_alive=True,
            generation_no=2,
            generation_name="仁",
            biography="Spouse sample for active marriage testing.",
        )
        grandson = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage4 Grandson",
            gender="male",
            birth_date=date(1996, 4, 9),
            is_alive=True,
            generation_no=3,
            generation_name="孝",
            biography="Third generation sample for parent-child testing.",
        )
        ended_husband = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage4 Ended Husband",
            gender="male",
            birth_date=date(1975, 9, 3),
            is_alive=True,
            generation_no=2,
            generation_name="仁",
            biography="Ended marriage sample linked into stage5 query graph.",
        )
        ended_wife = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage4 Ended Wife",
            gender="female",
            birth_date=date(1978, 12, 22),
            is_alive=True,
            generation_no=2,
            generation_name="仁",
            biography="Ended marriage sample linked into stage5 query graph.",
        )

        branch_daughter = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage5 Branch Daughter",
            gender="female",
            birth_date=date(1972, 1, 16),
            is_alive=True,
            generation_no=2,
            generation_name="仁",
            biography="Second generation branch created for descendant convergence testing.",
        )
        cousin_bride = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage5 Cousin Bride",
            gender="female",
            birth_date=date(1997, 9, 8),
            is_alive=True,
            generation_no=3,
            generation_name="孝",
            biography="Third generation branch node used for descendant convergence testing.",
        )
        merge_child = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage5 Merge Child",
            gender="male",
            birth_date=date(2020, 5, 6),
            is_alive=True,
            generation_no=4,
            generation_name="信",
            biography="Reachable from the same root through father and mother descendant lines.",
        )
        merge_child_spouse = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage5 Merge Child Spouse",
            gender="female",
            birth_date=date(2021, 2, 11),
            is_alive=True,
            generation_no=4,
            generation_name="信",
            biography="Used to extend the stage5 ancestor chain.",
        )
        great_grandchild = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage5 Great Grandchild",
            gender="female",
            birth_date=date(2042, 3, 15),
            is_alive=True,
            generation_no=5,
            generation_name="礼",
            biography="Used for long ancestor-chain and descendant-tree testing.",
        )
        great_grandchild_spouse = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage5 Great Grandchild Spouse",
            gender="male",
            birth_date=date(2040, 10, 4),
            is_alive=True,
            generation_no=5,
            generation_name="礼",
            biography="Used to create a sixth-generation descendant sample.",
        )
        great_great_grandchild = await ensure_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage5 Great Great Grandchild",
            gender="male",
            birth_date=date(2064, 7, 19),
            is_alive=True,
            generation_no=6,
            generation_name="智",
            biography="Deep-chain sample for stage5 ancestor recursion testing.",
        )
        duplicate_main = await _ensure_duplicate_name_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage5 Duplicate Ming",
            gender="male",
            birth_date=date(2001, 1, 3),
            generation_no=3,
            generation_name="孝",
            biography="Duplicate-name sample under the main branch.",
        )
        duplicate_ended = await _ensure_duplicate_name_member(
            session,
            tree_id=managed_tree.tree_id,
            name="Stage5 Duplicate Ming",
            gender="male",
            birth_date=date(2002, 8, 27),
            generation_no=3,
            generation_name="孝",
            biography="Duplicate-name sample under the ended-marriage branch.",
        )
        public_duplicate = await ensure_member(
            session,
            tree_id=public_tree.tree_id,
            name="Stage5 Public Search Sample",
            gender="female",
            birth_date=date(1988, 12, 1),
            is_alive=True,
            generation_no=2,
            generation_name="安",
            biography="Cross-tree readable search sample for stage5 manual QA.",
        )

        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=root.member_id,
            child_member_id=branch_daughter.member_id,
            parent_role="father",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=matriarch.member_id,
            child_member_id=branch_daughter.member_id,
            parent_role="mother",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=root.member_id,
            child_member_id=ended_husband.member_id,
            parent_role="father",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=matriarch.member_id,
            child_member_id=ended_husband.member_id,
            parent_role="mother",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=branch_daughter.member_id,
            child_member_id=cousin_bride.member_id,
            parent_role="mother",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=grandson.member_id,
            child_member_id=merge_child.member_id,
            parent_role="father",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=cousin_bride.member_id,
            child_member_id=merge_child.member_id,
            parent_role="mother",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=merge_child.member_id,
            child_member_id=great_grandchild.member_id,
            parent_role="father",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=merge_child_spouse.member_id,
            child_member_id=great_grandchild.member_id,
            parent_role="mother",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=great_grandchild_spouse.member_id,
            child_member_id=great_great_grandchild.member_id,
            parent_role="father",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=great_grandchild.member_id,
            child_member_id=great_great_grandchild.member_id,
            parent_role="mother",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=branch_son.member_id,
            child_member_id=duplicate_main.member_id,
            parent_role="father",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=daughter_in_law.member_id,
            child_member_id=duplicate_main.member_id,
            parent_role="mother",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=ended_husband.member_id,
            child_member_id=duplicate_ended.member_id,
            parent_role="father",
        )
        await ensure_parent_child(
            session,
            tree_id=managed_tree.tree_id,
            parent_member_id=ended_wife.member_id,
            child_member_id=duplicate_ended.member_id,
            parent_role="mother",
        )

        await ensure_marriage(
            session,
            tree_id=managed_tree.tree_id,
            member_id_1=grandson.member_id,
            member_id_2=cousin_bride.member_id,
            married_at=date(2019, 10, 1),
            status="active",
        )
        await ensure_marriage(
            session,
            tree_id=managed_tree.tree_id,
            member_id_1=merge_child.member_id,
            member_id_2=merge_child_spouse.member_id,
            married_at=date(2040, 9, 1),
            status="active",
        )
        await ensure_marriage(
            session,
            tree_id=managed_tree.tree_id,
            member_id_1=great_grandchild.member_id,
            member_id_2=great_grandchild_spouse.member_id,
            married_at=date(2060, 4, 16),
            status="active",
        )

        await session.commit()

    print("Seeded stage5 manual test data.")
    print("Users:")
    for user_config in USERS:
        print(f"  - {user_config['username']} / {user_config['password']}")
    print("Stage5 additions in Stage3 Managed Tree:")
    print("  - Stage5 Branch Daughter")
    print("  - Stage5 Cousin Bride")
    print("  - Stage5 Merge Child")
    print("  - Stage5 Merge Child Spouse")
    print("  - Stage5 Great Grandchild")
    print("  - Stage5 Great Grandchild Spouse")
    print("  - Stage5 Great Great Grandchild")
    print("  - Stage5 Duplicate Ming (main branch)")
    print("  - Stage5 Duplicate Ming (ended branch)")
    print("  - Stage4 Ended Husband linked into main tree")
    print("Stage5 additions in Stage3 Public Read Tree:")
    print("  - Stage5 Public Search Sample")


if __name__ == "__main__":
    asyncio.run(main())
