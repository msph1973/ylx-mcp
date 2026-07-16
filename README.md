# YLx Dev Assistant — MCP Server

FastMCP v3 server for YLx photo proofing platform development workflow.

## Tools

| Tool | Fungsi |
|------|--------|
| `pr_review` | Review PR dengan konteks codebase |
| `codebase_query` | Query arsitektur, patterns, dependencies |
| `suggest_feature` | Suggest fitur baru berdasarkan codebase |
| `audit` | Security/quality audit |
| `test_generator` | Generate test cases |
| `deployment_status` | Cek health Vercel deployment |

## Setup

```bash
cd ~/ylx-mcp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment Variables

```env
GITHUB_TOKEN=ghp_...
GITHUB_REPO=msph1973/ylx
SANITY_PROJECT_ID=741sif2l
SANITY_DATASET=production
SANITY_API_TOKEN=...
VERCEL_TOKEN=...
VERCEL_PROJECT_ID=ylx-msph
```

## Run Locally

```bash
python server.py
# or
fastmcp run server.py:mcp --transport http --port 8000
```

## Deploy to Horizon

1. Push to GitHub repo
2. Sign in at https://horizon.prefect.io
3. Create server → entrypoint: `server.py:mcp`
4. Add environment variables in Horizon dashboard

## Connect Client (Claude Desktop)

```json
{
  "mcpServers": {
    "ylx-dev": {
      "url": "https://ylx-dev-assistant.fastmcp.app/mcp",
      "transport": "http",
      "headers": {
        "Authorization": "Bearer fmcp_..."
      }
    }
  }
}
```
