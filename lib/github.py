import os
import httpx

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "msph1973/ylx")
GITHUB_API = "https://api.github.com"


def _headers() -> dict[str, str]:
    h = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


async def get_pr(number: int) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{GITHUB_API}/repos/{GITHUB_REPO}/pulls/{number}",
            headers=_headers(),
            timeout=30,
        )
        r.raise_for_status()
        return r.json()


async def get_pr_files(number: int) -> list[dict]:
    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{GITHUB_API}/repos/{GITHUB_REPO}/pulls/{number}/files",
            headers=_headers(),
            params={"per_page": 100},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()


async def get_pr_diff(number: int) -> str:
    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{GITHUB_API}/repos/{GITHUB_REPO}/pulls/{number}",
            headers={**_headers(), "Accept": "application/vnd.github.v3.diff"},
            timeout=30,
        )
        r.raise_for_status()
        return r.text


async def list_open_prs() -> list[dict]:
    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{GITHUB_API}/repos/{GITHUB_REPO}/pulls",
            headers=_headers(),
            params={"state": "open", "per_page": 20},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()


async def get_file_content(path: str, ref: str = "master") -> str | None:
    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{path}",
            headers=_headers(),
            params={"ref": ref},
            timeout=30,
        )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        import base64
        data = r.json()
        return base64.b64decode(data["content"]).decode("utf-8")


async def get_repo_tree(ref: str = "master") -> list[dict]:
    async with httpx.AsyncClient() as c:
        r = await c.get(
            f"{GITHUB_API}/repos/{GITHUB_REPO}/git/trees/{ref}",
            headers=_headers(),
            params={"recursive": "1"},
            timeout=30,
        )
        r.raise_for_status()
        return r.json().get("tree", [])
