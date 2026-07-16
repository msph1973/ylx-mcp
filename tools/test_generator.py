from fastmcp.tools import tool
from mcp.types import ToolAnnotations
from lib.github import get_repo_tree, get_file_content


@tool(
    annotations=ToolAnnotations(readOnlyHint=True),
    timeout=30.0,
)
async def test_generator(feature_description: str, file_path: str | None = None) -> dict:
    """Generate test cases for a YLx feature or endpoint.

    Analyzes existing test patterns in the codebase and generates
    appropriate test cases following the project's conventions.

    Args:
        feature_description: Description of the feature to test.
        file_path: Optional specific file to generate tests for.
    """
    existing_tests = await _find_existing_tests()
    patterns = _analyze_test_patterns(existing_tests)
    tests = _generate_tests(feature_description, file_path, patterns)

    return {
        "feature": feature_description,
        "target_file": file_path,
        "existing_test_patterns": patterns,
        "generated_tests": tests,
        "suggested_file": _suggest_test_file(file_path, patterns),
    }


async def _find_existing_tests() -> list[dict]:
    tree = await get_repo_tree()
    test_files = [
        item["path"] for item in tree
        if item.get("type") == "blob" and (".test." in item["path"] or ".spec." in item["path"])
    ]

    contents = {}
    for path in test_files[:5]:
        content = await get_file_content(path)
        if content:
            contents[path] = content[:3000]

    return [{"path": p, "content": contents.get(p, "")} for p in test_files]


def _analyze_test_patterns(tests: list[dict]) -> dict:
    patterns = {
        "framework": "vitest",
        "e2e_framework": "playwright",
        "mocking": "vi.fn()",
        "patterns": [],
    }

    for t in tests:
        content = t.get("content", "")
        if "describe(" in content:
            patterns["patterns"].append("describe/it blocks")
        if "expect(" in content:
            patterns["patterns"].append("expect assertions")
        if "vi.fn()" in content or "vi.mock(" in content:
            patterns["patterns"].append("vi mock functions")
        if "page." in content:
            patterns["patterns"].append("Playwright page API")

    patterns["patterns"] = list(set(patterns["patterns"]))
    return patterns


def _generate_tests(feature: str, file_path: str | None, patterns: dict) -> list[dict]:
    tests = [
        {
            "name": f"test {feature} — happy path",
            "type": "unit",
            "description": f"Verify {feature} works with valid inputs",
            "code": _unit_test_template(feature, "happy"),
        },
        {
            "name": f"test {feature} — error handling",
            "type": "unit",
            "description": f"Verify {feature} handles errors gracefully",
            "code": _unit_test_template(feature, "error"),
        },
        {
            "name": f"test {feature} — edge cases",
            "type": "unit",
            "description": f"Verify {feature} handles edge cases",
            "code": _unit_test_template(feature, "edge"),
        },
    ]

    if file_path and "api" in file_path:
        tests.append({
            "name": f"test {feature} — API integration",
            "type": "integration",
            "description": f"Verify {feature} endpoint returns correct status and payload",
            "code": _api_test_template(feature, file_path),
        })

    return tests


def _unit_test_template(feature: str, case: str) -> str:
    if case == "happy":
        return f'''import {{ describe, it, expect }} from "vitest";

describe("{feature}", () => {{
  it("should work with valid input", () => {{
    // TODO: implement
    expect(true).toBe(true);
  }});
}});'''
    elif case == "error":
        return f'''import {{ describe, it, expect }} from "vitest";

describe("{feature}", () => {{
  it("should handle invalid input gracefully", () => {{
    // TODO: implement
    expect(true).toBe(true);
  }});
}});'''
    else:
        return f'''import {{ describe, it, expect }} from "vitest";

describe("{feature}", () => {{
  it("should handle empty input", () => {{
    // TODO: implement
    expect(true).toBe(true);
  }});

  it("should handle boundary values", () => {{
    // TODO: implement
    expect(true).toBe(true);
  }});
}});'''


def _api_test_template(feature: str, file_path: str) -> str:
    return f'''import {{ describe, it, expect }} from "vitest";

describe("{feature} API", () => {{
  it("should return 200 for valid request", async () => {{
    // TODO: implement with fetch or test client
    expect(true).toBe(true);
  }});

  it("should return 401 without auth", async () => {{
    // TODO: implement
    expect(true).toBe(true);
  }});

  it("should return 400 for invalid payload", async () => {{
    // TODO: implement
    expect(true).toBe(true);
  }});
}});'''


def _suggest_test_file(file_path: str | None, patterns: dict) -> str:
    if file_path:
        if file_path.endswith(".ts"):
            return file_path.replace(".ts", ".test.ts")
        if file_path.endswith(".tsx"):
            return file_path.replace(".tsx", ".test.tsx")
    return "apps/web/src/__tests__/new.test.ts"
