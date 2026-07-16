from fastmcp.tools import tool
from mcp.types import ToolAnnotations
from lib.github import get_pr, get_pr_files, get_pr_diff


@tool(
    annotations=ToolAnnotations(readOnlyHint=True),
    timeout=60.0,
)
async def pr_review(pr_number: int) -> dict:
    """Review a GitHub PR with codebase context.

    Fetches PR metadata, changed files, and diff, then provides
    a structured review with findings and suggestions.

    Args:
        pr_number: The PR number to review.
    """
    pr = await get_pr(pr_number)
    files = await get_pr_files(pr_number)
    diff = await get_pr_diff(pr_number)

    findings = []
    for f in files:
        filename = f.get("filename", "")
        status = f.get("status", "")
        additions = f.get("additions", 0)
        deletions = f.get("deletions", 0)

        finding = {
            "file": filename,
            "status": status,
            "changes": f"+{additions}/-{deletions}",
        }

        patch = f.get("patch", "")
        if patch:
            issues = _check_patch(filename, patch)
            if issues:
                finding["issues"] = issues

        findings.append(finding)

    return {
        "pr": {
            "number": pr_number,
            "title": pr.get("title"),
            "state": pr.get("state"),
            "author": pr.get("user", {}).get("login"),
            "branch": f"{pr.get('head', {}).get('ref')} → {pr.get('base', {}).get('ref')}",
            "mergeable": pr.get("mergeable"),
        },
        "summary": {
            "files_changed": len(files),
            "total_additions": sum(f.get("additions", 0) for f in files),
            "total_deletions": sum(f.get("deletions", 0) for f in files),
        },
        "findings": findings,
        "diff_preview": diff[:3000] if diff else None,
    }


def _check_patch(filename: str, patch: str) -> list[str]:
    issues = []
    lines = patch.split("\n")
    for line in lines:
        if line.startswith("+") and not line.startswith("+++"):
            content = line[1:]
            if "password" in content.lower() or "secret" in content.lower():
                issues.append("Potential secret in code")
            if "TODO" in content or "FIXME" in content:
                issues.append("Contains TODO/FIXME")
            if "any" in content and filename.endswith((".ts", ".tsx")):
                issues.append("Potential use of 'any' type")
    return issues
