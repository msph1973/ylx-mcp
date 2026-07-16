import os
import httpx

VERCEL_TOKEN = os.environ.get("VERCEL_TOKEN", "")
VERCEL_TEAM_ID = os.environ.get("VERCEL_TEAM_ID", "")
VERCEL_PROJECT_ID = os.environ.get("VERCEL_PROJECT_ID", "ylx-msph")
VERCEL_API = "https://api.vercel.com"


def _headers() -> dict[str, str]:
    h = {"Authorization": f"Bearer {VERCEL_TOKEN}"} if VERCEL_TOKEN else {}
    return h


def _team_params() -> dict[str, str]:
    return {"teamId": VERCEL_TEAM_ID} if VERCEL_TEAM_ID else {}


async def list_deployments(limit: int = 5) -> list[dict]:
    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{VERCEL_API}/v13/deployments",
            headers=_headers(),
            params={**_team_params(), "projectId": VERCEL_PROJECT_ID, "limit": limit},
            timeout=30,
        )
        r.raise_for_status()
        return r.json().get("deployments", [])


async def get_deployment(deployment_id: str) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{VERCEL_API}/v13/deployments/{deployment_id}",
            headers=_headers(),
            timeout=30,
        )
        r.raise_for_status()
        return r.json()


async def get_project() -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{VERCEL_API}/v9/projects/{VERCEL_PROJECT_ID}",
            headers=_headers(),
            params=_team_params(),
            timeout=30,
        )
        r.raise_for_status()
        return r.json()
