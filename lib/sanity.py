import os
import httpx

SANITY_PROJECT_ID = os.environ.get("SANITY_PROJECT_ID", "741sif2l")
SANITY_DATASET = os.environ.get("SANITY_DATASET", "production")
SANITY_API_TOKEN = os.environ.get("SANITY_API_TOKEN", "")
SANITY_API = f"https://{SANITY_PROJECT_ID}.api.sanity.io/v2024-01-01/data/query/{SANITY_DATASET}"


async def query(groq: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.get(
            SANITY_API,
            params={"query": groq, **(params or {})},
            headers={"Authorization": f"Bearer {SANITY_API_TOKEN}"} if SANITY_API_TOKEN else {},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()


async def get_albums() -> list[dict]:
    result = await query('*[_type == "album"]{_id, title, slug, status, _createdAt}')
    return result.get("result", [])


async def get_schemas() -> list[dict]:
    result = await query('*[_type == "sanity.schemaGroup"]')
    return result.get("result", [])
