from fastmcp.tools import tool
from mcp.types import ToolAnnotations
from lib.github import get_repo_tree


@tool(
    annotations=ToolAnnotations(readOnlyHint=True),
    timeout=30.0,
)
async def suggest_feature(area: str = "general") -> dict:
    """Suggest new features for the YLx photo proofing platform.

    Analyzes the current codebase and suggests features based on
    what exists, what's missing, and photography industry best practices.

    Args:
        area: Focus area — general, gallery, admin, upload, security, or performance.
    """
    tree = await get_repo_tree()
    paths = [item["path"] for item in tree if item.get("type") == "blob"]

    existing = {
        "gallery": any("gallery" in p.lower() for p in paths),
        "admin": any("admin" in p.lower() for p in paths),
        "upload": any("upload" in p.lower() for p in paths),
        "auth": any("auth" in p.lower() for p in paths),
        "realtime": any("ably" in p.lower() or "realtime" in p.lower() for p in paths),
        "analytics": any("analytics" in p.lower() for p in paths),
        "email": any("email" in p.lower() or "notification" in p.lower() for p in paths),
        "i18n": any("i18n" in p.lower() or "locale" in p.lower() for p in paths),
        "pwa": any("manifest" in p.lower() or "service-worker" in p.lower() for p in paths),
        "seo": any("sitemap" in p.lower() or "robots" in p.lower() for p in paths),
    }

    suggestions = _get_suggestions(area, existing)

    return {
        "area": area,
        "existing_features": {k: v for k, v in existing.items() if v},
        "missing_features": {k: v for k, v in existing.items() if not v},
        "suggestions": suggestions,
    }


def _get_suggestions(area: str, existing: dict) -> list[dict]:
    all_suggestions = {
        "gallery": [
            {"name": "Before/After Slider", "priority": "medium", "description": "Side-by-side comparison view for photo edits"},
            {"name": "Favorites Collection", "priority": "high", "description": "Let clients create multiple favorite lists from selections"},
            {"name": "Download Watermarked Previews", "priority": "medium", "description": "Low-res watermarked downloads before final delivery"},
            {"name": "Comment Thread per Photo", "priority": "low", "description": "Discuss individual photos with threaded comments"},
        ],
        "admin": [
            {"name": "Batch Export to Lightroom Collection", "priority": "high", "description": "Auto-create Lightroom collection from selection list"},
            {"name": "Client Selection Statistics", "priority": "medium", "description": "Analytics on selection patterns, popular photos, time spent"},
            {"name": "Album Templates", "priority": "medium", "description": "Pre-configured album templates for different wedding styles"},
            {"name": "Automated Album Lock Timer", "priority": "low", "description": "Auto-lock gallery after configurable deadline"},
        ],
        "upload": [
            {"name": "AI Auto-Tagging", "priority": "medium", "description": "Auto-tag photos with people, scenes, and events using Vision API"},
            {"name": "RAW File Support", "priority": "low", "description": "Support CR2/NEF/ARW with server-side preview generation"},
            {"name": "Upload Progress Webhook", "priority": "low", "description": "Notify external systems when upload completes"},
        ],
        "security": [
            {"name": "Two-Factor Auth for Admin", "priority": "high", "description": "TOTP-based 2FA for admin login"},
            {"name": "IP Allowlisting", "priority": "medium", "description": "Restrict admin access to specific IPs"},
            {"name": "Audit Log", "priority": "medium", "description": "Track all admin actions with timestamps and details"},
        ],
        "performance": [
            {"name": "Image CDN Optimization", "priority": "high", "description": "Serve images via CDN with auto WebP/AVIF conversion"},
            {"name": "Incremental Static Regeneration", "priority": "medium", "description": "ISR for gallery pages to reduce cold starts"},
            {"name": "Edge Middleware", "priority": "low", "description": "Move rate limiting and auth checks to edge"},
        ],
        "general": [
            {"name": "Multi-Language Support", "priority": "medium", "description": "i18n for gallery interface (EN/ID/ZH)"},
            {"name": "Client Mobile App", "priority": "low", "description": "React Native app for photo selection on mobile"},
            {"name": "API for Third-Party Integration", "priority": "medium", "description": "REST/GraphQL API for CRM and studio management tools"},
            {"name": "White-Label Branding", "priority": "low", "description": "Custom domain, logo, and colors per photographer"},
        ],
    }

    return all_suggestions.get(area, all_suggestions["general"])
