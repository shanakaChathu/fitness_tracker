# whoop-mcp — Agent Guide

## Project Overview

MCP (Model Context Protocol) server that bridges the Whoop fitness API with Claude. Deployed on Fly.io, it exposes 16 tools so Claude can read a user's recovery, sleep, workout, and cycle data in real time.

## Architecture

```
Claude (MCP client)
    ↓ HTTP streamable
FastMCP Server (server.py)
    ↓ tool calls
Whoop API v2 Client (whoop_client.py)
    ↓ auth
Token Manager (auth.py) → /data/refresh_token.txt (Fly.io persistent volume)
    ↓
Whoop OAuth v2 (api.prod.whoop.com)
```

## Key Files

| File | Role |
|------|------|
| [src/whoop_mcp/server.py](src/whoop_mcp/server.py) | FastMCP server; all 16 tool definitions |
| [src/whoop_mcp/whoop_client.py](src/whoop_mcp/whoop_client.py) | `whoop_get()` and `whoop_get_paginated()` HTTP helpers |
| [src/whoop_mcp/auth.py](src/whoop_mcp/auth.py) | Token cache, refresh, and rotation logic |
| [src/whoop_mcp/config.py](src/whoop_mcp/config.py) | OAuth credentials and API base URLs |
| [scripts/get_token.py](scripts/get_token.py) | One-time OAuth flow to obtain the initial refresh token |
| [fly.toml](fly.toml) | Fly.io deployment (app: `fitness-tracker-whoop`, region: SIN) |
| [Dockerfile](Dockerfile) | Python 3.11-slim, entry: `python -m whoop_mcp.server` |

## Tech Stack

- **Python 3.11+** with `mcp[cli]`, `httpx`, `python-dotenv`
- **FastMCP** — decorator-based async MCP tool registration
- **Fly.io** — always-on deployment (no auto-stop), 256 MB VM, 1 GB `/data` volume

## Environment Variables

Defined in `.env` (see [.env.example](.env.example)):

```
WHOOP_CLIENT_ID       # from developer.whoop.com
WHOOP_CLIENT_SECRET
WHOOP_REFRESH_TOKEN   # obtained via scripts/get_token.py
PORT                  # default 8080
HOST                  # default 0.0.0.0
```

On Fly.io, `WHOOP_REFRESH_TOKEN` is the initial seed; the live token is persisted to `/data/refresh_token.txt` and rotated on every API call.

## Available MCP Tools

**Profile / Body:** `get_user_profile`, `get_body_measurements`

**Recovery:** `get_latest_recovery`, `get_recovery_history(days)`

**Sleep:** `get_latest_sleep`, `get_sleep_history(days)`

**Workouts:** `get_recent_workouts(limit)`, `get_workouts_by_date(start, end)`

**Cycles:** `get_latest_cycle`, `get_cycle_history(days)`

**Summaries (composite):** `get_today_summary`, `get_weekly_summary`, `get_monthly_summary`

## Common Tasks

### Run locally
```bash
pip install -e .
python -m whoop_mcp.server
```

### Get initial OAuth token
```bash
python scripts/get_token.py
# Follow browser prompt, then copy refresh_token into .env
```

### Deploy to Fly.io
```bash
fly deploy
```

### Set secrets on Fly.io
```bash
fly secrets set WHOOP_CLIENT_ID=... WHOOP_CLIENT_SECRET=... WHOOP_REFRESH_TOKEN=...
```

## Important Constraints

- **Token rotation:** Whoop rotates the refresh token on every OAuth call. The latest token is always written to `/data/refresh_token.txt`; never overwrite it with a stale value.
- **Async-only:** All HTTP calls use `httpx` async; keep new tool handlers `async def`.
- **No rate-limit backoff** is currently implemented — be careful with bulk historical queries.
- **Pagination:** `whoop_get_paginated()` follows `next_token` cursors; respect the `max_records` cap.
- **Scopes are read-only:** offline, profile, body, cycles, recovery, sleep, workout.

## Adding a New Tool

1. Add an `async def` function in [server.py](src/whoop_mcp/server.py) decorated with `@mcp.tool()`.
2. Use `whoop_get()` for single-page responses or `whoop_get_paginated()` for list endpoints.
3. Write a clear docstring — it becomes the tool description Claude sees.
