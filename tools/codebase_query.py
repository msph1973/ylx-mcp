from fastmcp.tools import tool
from mcp.types import ToolAnnotations
from lib.github import get_repo_tree, get_file_content


@tool(
    annotations=ToolAnnotations(readOnlyHint=True),
    timeout=30.0,
)
async def codebase_query(query: str) -> dict:
    """Query the YLx codebase for architecture, patterns, and dependencies.

    Searches file tree and reads relevant files to answer questions
    about codebase structure, patterns, and implementation details.

    Args:
        query: Natural language question about the codebase.
    """
    tree = await get_repo_tree()

    relevant_files = []
    query_lower = query.lower()

    keywords_to_paths = {
        "auth": ["auth", "login", "session", "cookie"],
        "upload": ["upload", "finalize", "credentials"],
        "gallery": ["gallery", "pin", "photo", "lightbox"],
        "admin": ["admin", "album", "selection"],
        "api": ["api/", "pages/api"],
        "schema": ["schema", "sanity"],
        "deploy": ["vercel", "deploy", "turbo"],
        "test": ["test", "spec", "vitest", "playwright"],
        "security": ["rate-limit", "csrf", "csp", "hsts", "middleware"],
        "realtime": ["ably", "realtime"],
    }

    for category, path_keywords in keywords_to_paths.items():
        if any(kw in query_lower for kw in [category] + path_keywords):
            for item in tree:
                path = item.get("path", "")
                if item.get("type") == "blob" and any(kw in path.lower() for kw in path_keywords):
                    relevant_files.append(path)

    if not relevant_files:
        for item in tree:
            path = item.get("path", "")
            if item.get("type") == "blob" and any(kw in path.lower() for kw in query_lower.split()):
                relevant_files.append(path)

    relevant_files = list(dict.fromkeys(relevant_files))[:10]

    file_contents = {}
    for path in relevant_files:
        content = await get_file_content(path)
        if content:
            file_contents[path] = content[:2000]

    return {
        "query": query,
        "relevant_files": relevant_files,
        "file_count": len(tree),
        "file_contents": file_contents,
    }
