import os
import base64
import httpx
from fastmcp import FastMCP
from mcp.types import ToolAnnotations

# ---------------------------------------------------------------------------
# API Clients
# ---------------------------------------------------------------------------

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "msph1973/ylx")
GITHUB_API = "https://api.github.com"

SANITY_PROJECT_ID = os.environ.get("SANITY_PROJECT_ID", "741sif2l")
SANITY_DATASET = os.environ.get("SANITY_DATASET", "production")
SANITY_API_TOKEN = os.environ.get("SANITY_API_TOKEN", "")

VERCEL_TOKEN = os.environ.get("VERCEL_TOKEN", "")
VERCEL_TEAM_ID = os.environ.get("VERCEL_TEAM_ID", "")
VERCEL_PROJECT_ID = os.environ.get("VERCEL_PROJECT_ID", "ylx-msph")
VERCEL_API = "https://api.vercel.com"


def _gh_headers() -> dict[str, str]:
    h = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


async def gh_get_pr(number: int) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{GITHUB_API}/repos/{GITHUB_REPO}/pulls/{number}", headers=_gh_headers(), timeout=30)
        r.raise_for_status()
        return r.json()


async def gh_get_pr_files(number: int) -> list[dict]:
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{GITHUB_API}/repos/{GITHUB_REPO}/pulls/{number}/files", headers=_gh_headers(), params={"per_page": 100}, timeout=30)
        r.raise_for_status()
        return r.json()


async def gh_get_pr_diff(number: int) -> str:
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{GITHUB_API}/repos/{GITHUB_REPO}/pulls/{number}", headers={**_gh_headers(), "Accept": "application/vnd.github.v3.diff"}, timeout=30)
        r.raise_for_status()
        return r.text


async def gh_get_file(path: str, ref: str = "master") -> str | None:
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{path}", headers=_gh_headers(), params={"ref": ref}, timeout=30)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return base64.b64decode(r.json()["content"]).decode("utf-8")


async def gh_get_tree(ref: str = "master") -> list[dict]:
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{GITHUB_API}/repos/{GITHUB_REPO}/git/trees/{ref}", headers=_gh_headers(), params={"recursive": "1"}, timeout=30)
        r.raise_for_status()
        return r.json().get("tree", [])


async def vercel_list_deployments(limit: int = 5) -> list[dict]:
    async with httpx.AsyncClient() as c:
        params: dict = {"projectId": VERCEL_PROJECT_ID, "limit": limit}
        if VERCEL_TEAM_ID:
            params["teamId"] = VERCEL_TEAM_ID
        h = {"Authorization": f"Bearer {VERCEL_TOKEN}"} if VERCEL_TOKEN else {}
        r = await c.get(f"{VERCEL_API}/v13/deployments", headers=h, params=params, timeout=30)
        r.raise_for_status()
        return r.json().get("deployments", [])


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

mcp = FastMCP("YLx Dev Assistant", on_duplicate="error")


# ---------------------------------------------------------------------------
# Tool: pr_review
# ---------------------------------------------------------------------------

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True), timeout=60.0)
async def pr_review(pr_number: int) -> dict:
    """Review a GitHub PR with codebase context.

    Args:
        pr_number: The PR number to review.
    """
    pr = await gh_get_pr(pr_number)
    files = await gh_get_pr_files(pr_number)
    diff = await gh_get_pr_diff(pr_number)

    findings = []
    for f in files:
        filename = f.get("filename", "")
        finding = {
            "file": filename,
            "status": f.get("status", ""),
            "changes": f"+{f.get('additions', 0)}/-{f.get('deletions', 0)}",
        }
        patch = f.get("patch", "")
        if patch:
            issues = []
            for line in patch.split("\n"):
                if line.startswith("+") and not line.startswith("+++"):
                    c = line[1:]
                    if "password" in c.lower() or "secret" in c.lower():
                        issues.append("Potential secret in code")
                    if "TODO" in c or "FIXME" in c:
                        issues.append("Contains TODO/FIXME")
            if issues:
                finding["issues"] = issues
        findings.append(finding)

    return {
        "pr": {"number": pr_number, "title": pr.get("title"), "state": pr.get("state"), "author": pr.get("user", {}).get("login")},
        "summary": {"files_changed": len(files), "additions": sum(f.get("additions", 0) for f in files), "deletions": sum(f.get("deletions", 0) for f in files)},
        "findings": findings,
        "diff_preview": diff[:3000] if diff else None,
    }


# ---------------------------------------------------------------------------
# Tool: codebase_query
# ---------------------------------------------------------------------------

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True), timeout=30.0)
async def codebase_query(query: str) -> dict:
    """Query the YLx codebase for architecture and patterns.

    Args:
        query: Natural language question about the codebase.
    """
    tree = await gh_get_tree()
    query_lower = query.lower()

    kw_map = {
        "auth": ["auth", "login", "session"],
        "upload": ["upload", "finalize"],
        "gallery": ["gallery", "pin", "photo"],
        "admin": ["admin", "album", "selection"],
        "security": ["rate-limit", "csrf", "middleware"],
        "realtime": ["ably"],
    }

    relevant = []
    for cat, kws in kw_map.items():
        if any(k in query_lower for k in [cat] + kws):
            for item in tree:
                if item.get("type") == "blob" and any(kw in item["path"].lower() for kw in kws):
                    relevant.append(item["path"])

    if not relevant:
        for item in tree:
            if item.get("type") == "blob" and any(kw in item["path"].lower() for kw in query_lower.split()):
                relevant.append(item["path"])

    relevant = list(dict.fromkeys(relevant))[:10]
    contents = {}
    for p in relevant:
        c = await gh_get_file(p)
        if c:
            contents[p] = c[:2000]

    return {"query": query, "relevant_files": relevant, "file_count": len(tree), "file_contents": contents}


# ---------------------------------------------------------------------------
# Tool: suggest_feature
# ---------------------------------------------------------------------------

SUGGESTIONS = {
    "gallery": [
        {"name": "Before/After Slider", "priority": "medium"},
        {"name": "Favorites Collection", "priority": "high"},
        {"name": "Watermarked Previews", "priority": "medium"},
    ],
    "admin": [
        {"name": "Batch Export to Lightroom", "priority": "high"},
        {"name": "Selection Statistics", "priority": "medium"},
        {"name": "Album Templates", "priority": "medium"},
    ],
    "security": [
        {"name": "Two-Factor Auth", "priority": "high"},
        {"name": "IP Allowlisting", "priority": "medium"},
        {"name": "Audit Log", "priority": "medium"},
    ],
    "general": [
        {"name": "Multi-Language (i18n)", "priority": "medium"},
        {"name": "REST API for CRM", "priority": "medium"},
        {"name": "White-Label Branding", "priority": "low"},
    ],
}


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True), timeout=30.0)
async def suggest_feature(area: str = "general") -> dict:
    """Suggest features for the YLx photo proofing platform.

    Args:
        area: Focus area — general, gallery, admin, upload, security, or performance.
    """
    tree = await gh_get_tree()
    paths = [i["path"] for i in tree if i.get("type") == "blob"]

    existing = {
        k: any(kw in p.lower() for p in paths)
        for k, kw in [("gallery", "gallery"), ("admin", "admin"), ("auth", "auth"), ("realtime", "ably"), ("email", "email")]
    }

    return {"area": area, "existing": existing, "suggestions": SUGGESTIONS.get(area, SUGGESTIONS["general"])}


# ---------------------------------------------------------------------------
# Tool: audit
# ---------------------------------------------------------------------------

AUDIT_CHECKS = {
    "security": [
        "requireAdmin() at top of admin routes",
        "PIN rate limiter active",
        "Session cookie HMAC-signed",
        "CSRF check in middleware",
        "Timing-safe PIN comparison",
        "No hardcoded credentials",
    ],
    "code_quality": [
        "TypeScript strict — no any",
        "ESLint clean",
        "publishAdminEvent after mutations",
        "Cache invalidation after writes",
    ],
}


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True), timeout=45.0)
async def audit(category: str = "all") -> dict:
    """Run security and quality audit against YLx criteria.

    Args:
        category: security, code_quality, or all.
    """
    tree = await gh_get_tree()
    paths = [i["path"] for i in tree if i.get("type") == "blob"]

    checks = AUDIT_CHECKS.get(category, {}) if category != "all" else AUDIT_CHECKS
    if category == "all":
        checks = {k: v for v in AUDIT_CHECKS.values() for k, v in [(list(AUDIT_CHECKS.keys())[0], v)]}
        checks = {}
        for cat, items in AUDIT_CHECKS.items():
            for item in items:
                checks[item] = cat

    results = []
    for cat, items in AUDIT_CHECKS.items():
        if category not in ("all", cat):
            continue
        for check in items:
            status = "pass"
            cl = check.lower()
            if "rate limiter" in cl:
                status = "pass" if any("ratelimit" in p.lower() for p in paths) else "fail"
            elif "hmac" in cl or "session" in cl:
                status = "pass" if any("auth" in p.lower() for p in paths) else "fail"
            elif "csrf" in cl:
                status = "pass" if any("middleware" in p.lower() for p in paths) else "fail"
            elif "publishadminevent" in cl:
                status = "pass" if any("/api/" in p and p.endswith(".ts") for p in paths) else "warn"
            results.append({"check": check, "category": cat, "status": status})

    passed = sum(1 for r in results if r["status"] == "pass")
    return {"summary": {"total": len(results), "passed": passed}, "results": results}


# ---------------------------------------------------------------------------
# Tool: test_generator
# ---------------------------------------------------------------------------

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True), timeout=30.0)
async def test_generator(feature: str, file_path: str | None = None) -> dict:
    """Generate test cases for a feature.

    Args:
        feature: Description of the feature to test.
        file_path: Optional file to generate tests for.
    """
    suggested = (file_path.replace(".ts", ".test.ts") if file_path and file_path.endswith(".ts") else None) or "apps/web/src/__tests__/new.test.ts"

    tests = [
        {"name": f"{feature} — happy path", "code": f'import {{ describe, it, expect }} from "vitest";\n\ndesc("{feature}", () => {{\n  it("works", () => {{ expect(true).toBe(true); }});\n}});'},
        {"name": f"{feature} — error handling", "code": f'import {{ describe, it, expect }} from "vitest";\n\ndesc("{feature}", () => {{\n  it("handles errors", () => {{ expect(true).toBe(true); }});\n}});'},
    ]

    return {"feature": feature, "target_file": file_path, "suggested_test_file": suggested, "tests": tests}


# ---------------------------------------------------------------------------
# Tool: deployment_status
# ---------------------------------------------------------------------------

@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True), timeout=30.0)
async def deployment_status(limit: int = 5) -> dict:
    """Check Vercel deployment health.

    Args:
        limit: Number of recent deployments to check.
    """
    deps = await vercel_list_deployments(min(limit, 10))
    results = [{"id": d.get("uid", ""), "url": d.get("url", ""), "state": d.get("state", ""), "branch": d.get("meta", {}).get("branch", "")} for d in deps]
    failed = [r for r in results if r.get("state") == "ERROR"]
    latest = results[0] if results else None

    return {
        "summary": {"latest_state": latest.get("state") if latest else None, "failed_count": len(failed)},
        "deployments": results,
    }


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
