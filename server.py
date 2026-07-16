import os
from fastmcp import FastMCP

from tools.pr_review import pr_review
from tools.codebase_query import codebase_query
from tools.suggest_feature import suggest_feature
from tools.audit import audit
from tools.test_generator import test_generator
from tools.deployment_status import deployment_status

mcp = FastMCP(
    "YLx Dev Assistant",
    on_duplicate="error",
)

mcp.add_tool(pr_review)
mcp.add_tool(codebase_query)
mcp.add_tool(suggest_feature)
mcp.add_tool(audit)
mcp.add_tool(test_generator)
mcp.add_tool(deployment_status)


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
