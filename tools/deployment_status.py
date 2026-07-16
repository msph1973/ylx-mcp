from fastmcp.tools import tool
from mcp.types import ToolAnnotations
from lib.vercel import list_deployments


@tool(
    annotations=ToolAnnotations(readOnlyHint=True),
    timeout=30.0,
)
async def deployment_status(limit: int = 5) -> dict:
    """Check Vercel deployment health and recent deployments.

    Fetches the latest deployments and reports their status,
    URLs, and any failures.

    Args:
        limit: Number of recent deployments to check (max 10).
    """
    deployments = await list_deployments(min(limit, 10))

    results = []
    for d in deployments:
        dep = {
            "id": d.get("uid", ""),
            "url": d.get("url", ""),
            "state": d.get("state", ""),
            "branch": d.get("meta", {}).get("branch", ""),
            "created": d.get("created", ""),
            "ready_state": d.get("readyState", ""),
        }

        if d.get("state") == "ERROR":
            dep["error"] = d.get("errorMessage", "Unknown error")

        results.append(dep)

    latest = results[0] if results else None
    failed = [r for r in results if r.get("state") == "ERROR"]

    return {
        "summary": {
            "latest_state": latest.get("state") if latest else None,
            "latest_url": f"https://{latest.get('url')}" if latest else None,
            "total_checked": len(results),
            "failed_count": len(failed),
        },
        "deployments": results,
        "failures": failed,
    }
