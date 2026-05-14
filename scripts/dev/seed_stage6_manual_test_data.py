import asyncio
from datetime import date

from seed_stage5_manual_test_data import (
    AsyncSessionLocal,
    FamilyTree,
    UserAccount,
    ensure_marriage,
    ensure_member,
    get_or_create_tree,
    main as seed_stage5_main,
    select,
    touch_tree,
)


async def _get_user_by_username(session, username: str) -> UserAccount:
    result = await session.execute(select(UserAccount).where(UserAccount.username == username))
    return result.scalar_one()


async def _get_tree_by_creator_and_name(session, creator_user_id: int, tree_name: str) -> FamilyTree:
    return await get_or_create_tree(
        session,
        creator_user_id=creator_user_id,
        tree_name=tree_name,
        surname="Chen" if "Analytics" in tree_name else "Li",
        description="Stage6 analytics manual testing tree.",
    )


async def main() -> None:
    await seed_stage5_main()

    async with AsyncSessionLocal() as session:
        creator = await _get_user_by_username(session, "stage3_creator")
        viewer = await _get_user_by_username(session, "stage3_viewer")

        empty_tree = await _get_tree_by_creator_and_name(session, creator.user_id, "Stage6 Empty Analytics Tree")
        unknown_tree = await _get_tree_by_creator_and_name(session, viewer.user_id, "Stage6 Unknown Analytics Tree")
        analytics_tree = await _get_tree_by_creator_and_name(session, creator.user_id, "Stage6 Analytics Study Tree")

        await touch_tree(empty_tree)
        await touch_tree(unknown_tree)
        await touch_tree(analytics_tree)

        await ensure_member(
            session,
            tree_id=unknown_tree.tree_id,
            name="Stage6 Unknown Gender Sample A",
            gender="unknown",
            birth_date=date(1988, 2, 12),
            generation_no=2,
            generation_name="安",
            biography="Unknown-gender sample for dashboard ratio empty-state validation.",
        )
        await ensure_member(
            session,
            tree_id=unknown_tree.tree_id,
            name="Stage6 Unknown Gender Sample B",
            gender="unknown",
            birth_date=date(1992, 6, 8),
            generation_no=3,
            generation_name="宁",
            biography="Unknown-gender sample for dashboard ratio empty-state validation.",
        )

        gen1_a = await ensure_member(
            session,
            tree_id=analytics_tree.tree_id,
            name="Stage6 Gen1 Long Life A",
            gender="male",
            birth_date=date(1940, 1, 1),
            death_date=date(2000, 1, 1),
            is_alive=False,
            generation_no=1,
            generation_name="德",
            biography="Used to produce a stable 60-year average lifespan for generation 1.",
        )
        gen1_b = await ensure_member(
            session,
            tree_id=analytics_tree.tree_id,
            name="Stage6 Gen1 Long Life B",
            gender="female",
            birth_date=date(1942, 1, 1),
            death_date=date(2002, 1, 1),
            is_alive=False,
            generation_no=1,
            generation_name="德",
            biography="Used to produce a stable 60-year average lifespan for generation 1.",
        )
        gen2_c = await ensure_member(
            session,
            tree_id=analytics_tree.tree_id,
            name="Stage6 Gen2 Shorter Life",
            gender="male",
            birth_date=date(1970, 1, 1),
            death_date=date(2025, 1, 1),
            is_alive=False,
            generation_no=2,
            generation_name="仁",
            biography="Used to ensure generation 2 does not overtake generation 1 in lifespan stats.",
        )
        unmarried_elder = await ensure_member(
            session,
            tree_id=analytics_tree.tree_id,
            name="Stage6 Eligible Elder",
            gender="male",
            birth_date=date(1960, 1, 1),
            generation_no=2,
            generation_name="仁",
            biography="Should appear in older-than-50 unmarried male stats.",
        )
        ended_elder = await ensure_member(
            session,
            tree_id=analytics_tree.tree_id,
            name="Stage6 Ended Marriage Elder",
            gender="male",
            birth_date=date(1958, 1, 1),
            generation_no=2,
            generation_name="仁",
            biography="Should be excluded from unmarried stats because an ended marriage still exists.",
        )
        ended_spouse = await ensure_member(
            session,
            tree_id=analytics_tree.tree_id,
            name="Stage6 Ended Marriage Spouse",
            gender="female",
            birth_date=date(1960, 1, 1),
            generation_no=2,
            generation_name="仁",
            biography="Pair for ended-marriage exclusion sample.",
        )
        early_gen3 = await ensure_member(
            session,
            tree_id=analytics_tree.tree_id,
            name="Stage6 Early Gen3",
            gender="female",
            birth_date=date(1980, 1, 1),
            generation_no=3,
            generation_name="孝",
            biography="Should appear in birth-year-below-generation-average stats.",
        )
        mid_gen3 = await ensure_member(
            session,
            tree_id=analytics_tree.tree_id,
            name="Stage6 Mid Gen3",
            gender="male",
            birth_date=date(1990, 1, 1),
            generation_no=3,
            generation_name="孝",
            biography="Used to set generation 3 average birth year.",
        )
        late_gen3 = await ensure_member(
            session,
            tree_id=analytics_tree.tree_id,
            name="Stage6 Late Gen3",
            gender="male",
            birth_date=date(2000, 1, 1),
            generation_no=3,
            generation_name="孝",
            biography="Used to set generation 3 average birth year.",
        )
        unknown_gen = await ensure_member(
            session,
            tree_id=analytics_tree.tree_id,
            name="Stage6 Missing Birth Sample",
            gender="unknown",
            generation_no=4,
            generation_name="信",
            biography="Should be ignored by lifespan and birth-year analytics that require birth_date.",
        )

        await ensure_marriage(
            session,
            tree_id=analytics_tree.tree_id,
            member_id_1=ended_elder.member_id,
            member_id_2=ended_spouse.member_id,
            married_at=date(1985, 5, 1),
            ended_at=date(2020, 1, 1),
            status="ended",
        )

        await session.commit()

    print("Seeded stage6 manual test data.")
    print("Reused trees:")
    print("  - Stage3 Managed Tree")
    print("  - Stage3 Public Read Tree")
    print("Added trees:")
    print("  - Stage6 Empty Analytics Tree")
    print("  - Stage6 Unknown Analytics Tree")
    print("  - Stage6 Analytics Study Tree")
    print("Stage6 analytics samples:")
    print("  - Unknown-only gender samples for ratio empty-state")
    print("  - Generation lifespan samples with stable generation-1 win")
    print("  - One older-than-50 unmarried male sample")
    print("  - One older-than-50 ended-marriage exclusion sample")
    print("  - One generation-3 early-birth sample for average birth-year comparison")


if __name__ == "__main__":
    asyncio.run(main())
