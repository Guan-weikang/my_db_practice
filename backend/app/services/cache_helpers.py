from __future__ import annotations

from pydantic import BaseModel

from app.core.cache import ResponseCache


async def get_or_set_model(
    cache: ResponseCache | None,
    *,
    key: str,
    ttl_seconds: int,
    model_type: type[BaseModel],
    loader,
):
    if cache is not None:
        cached = await cache.get_json(key)
        if cached is not None:
            return model_type.model_validate_json(cached)

    value = await loader()
    if cache is not None:
        await cache.set_json(key, value.model_dump_json(), ttl_seconds=ttl_seconds)
    return value


async def invalidate_tree_cache(cache: ResponseCache | None, tree_id: int) -> None:
    if cache is None:
        return
    await cache.delete_pattern(f"tree:{tree_id}:*")
    await cache.delete_pattern("family-trees:*")
