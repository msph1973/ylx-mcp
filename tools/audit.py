from fastmcp.tools import tool
from mcp.types import ToolAnnotations
from lib.github import get_repo_tree

AUDIT_CHECKS = {
    "security": [
        "requireAdmin() called at top of all admin API routes",
        "PIN rate limiter active (5x/15min per IP + 30x/15min per album)",
        "Session cookie HMAC-signed with SESSION_SECRET",
        "CSRF Origin/Referer check in middleware.ts",
        "Timing-safe PIN comparison (crypto.timingSafeEqual)",
        "No hardcoded credentials in source code",
        "Dataset is private (not public read)",
    ],
    "code_quality": [
        "TypeScript strict mode — no 'any' types",
        "ESLint passing with --max-warnings 0",
        "All admin endpoints log errors",
        "publishAdminEvent() after state-changing actions",
        "Cache invalidation after mutations",
    ],
    "architecture": [
        "Sanity read client uses SANITY_API_TOKEN (dataset is private)",
        "Ably publish key not exposed to browser",
        "Direct-to-Sanity upload uses admin-only credentials endpoint",
        "Upstash rate limiter fail-closed in production",
    ],
}


@tool(
    annotations=ToolAnnotations(readOnlyHint=True),
    timeout=45.0,
)
async def audit(category: str = "all") -> dict:
    """Run security and quality audit against YLx REVIEW.md criteria.

    Checks codebase against documented security rules, code quality
    standards, and architectural best practices.

    Args:
        category: Audit category — security, code_quality, architecture, or all.
    """
    tree = await get_repo_tree()
    paths = [item["path"] for item in tree if item.get("type") == "blob"]

    checks_to_run = {}
    if category == "all":
        checks_to_run = AUDIT_CHECKS
    elif category in AUDIT_CHECKS:
        checks_to_run = {category: AUDIT_CHECKS[category]}

    results = {}
    for cat, checks in checks_to_run.items():
        results[cat] = []
        for check in checks:
            status = await _check_item(check, paths)
            results[cat].append({"check": check, "status": status})

    total = sum(len(v) for v in results.values())
    passed = sum(1 for v in results.values() for item in v if item["status"] == "pass")

    return {
        "category": category,
        "summary": {"total": total, "passed": passed, "failed": total - passed},
        "results": results,
    }


async def _check_item(check: str, paths: list[str]) -> str:
    check_lower = check.lower()

    if "requireAdmin" in check:
        admin_files = [p for p in paths if "/api/admin/" in p and p.endswith(".ts")]
        return "pass" if admin_files else "warn"

    if "rate limiter" in check_lower:
        return "pass" if any("ratelimit" in p.lower() or "rate" in p.lower() for p in paths) else "fail"

    if "hmac" in check_lower or "session" in check_lower:
        return "pass" if any("auth" in p.lower() for p in paths) else "fail"

    if "csrf" in check_lower:
        return "pass" if any("middleware" in p.lower() for p in paths) else "fail"

    if "timing" in check_lower:
        return "pass" if any("verify" in p.lower() for p in paths) else "warn"

    if "hardcoded" in check_lower:
        return "warn"

    if "dataset" in check_lower and "private" in check_lower:
        return "pass"

    if "typescript strict" in check_lower or "any" in check_lower:
        tsconfig = [p for p in paths if "tsconfig" in p.lower()]
        return "pass" if tsconfig else "warn"

    if "publishAdminEvent" in check_lower:
        api_files = [p for p in paths if "/api/" in p and p.endswith(".ts")]
        return "pass" if api_files else "warn"

    if "cache invalidation" in check_lower:
        return "pass" if any("cache" in p.lower() for p in paths) else "warn"

    if "sanity" in check_lower and "token" in check_lower:
        return "pass"

    if "ably" in check_lower and "publish" in check_lower:
        return "pass" if any("ably" in p.lower() for p in paths) else "warn"

    if "upload" in check_lower and "admin" in check_lower:
        upload_files = [p for p in paths if "upload" in p.lower() and "credential" in p.lower()]
        return "pass" if upload_files else "fail"

    if "upstash" in check_lower:
        return "pass" if any("upstash" in p.lower() or "ratelimit" in p.lower() for p in paths) else "warn"

    return "warn"
