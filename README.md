# whoop-mcp

A Model Context Protocol (MCP) server that connects your [Whoop](https://www.whoop.com/) fitness data to Claude. Ask Claude about your recovery score, sleep quality, workouts, and daily strain — directly in conversation.

## What It Does

Once connected, Claude can answer questions like:

- *"How is my recovery today?"*
- *"Show me my sleep trends for the past two weeks."*
- *"What was my highest strain workout this month?"*
- *"Give me a summary of this week's fitness data."*

It exposes 16 tools covering recovery, sleep, workouts, daily cycles, and composite summaries.

## Prerequisites

- Python 3.11+
- A [Whoop](https://www.whoop.com/) account with API access ([developer.whoop.com](https://developer.whoop.com))
- Claude desktop app or any MCP-compatible client

## Setup

### 1. Clone and install

```bash
git clone https://github.com/shanakaChathu/fitness_tracker.git
cd fitness_tracker
pip install -e .
```

### 2. Create a Whoop OAuth app

1. Go to [developer.whoop.com](https://developer.whoop.com) and create an application.
2. Set the redirect URI to `http://localhost:8080/callback`.
3. Copy your **Client ID** and **Client Secret**.

### 3. Configure environment variables

```bash
cp .env.example .env
```

Fill in `.env`:

```env
WHOOP_CLIENT_ID=your_client_id
WHOOP_CLIENT_SECRET=your_client_secret
WHOOP_REFRESH_TOKEN=     # leave blank for now
PORT=8080
HOST=0.0.0.0
```

### 4. Get your refresh token

Run the one-time OAuth flow:

```bash
python scripts/get_token.py
```

This opens a browser for Whoop authorization. After you approve, copy the printed `refresh_token` into your `.env` file.

### 5. Run the server

```bash
python -m whoop_mcp.server
```

The MCP server starts on `http://localhost:8080`.

### 6. Connect to Claude

Add the server to your Claude desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "whoop": {
      "url": "http://localhost:8080"
    }
  }
}
```

Restart Claude — your Whoop tools will appear automatically.

## Available Tools

| Category | Tools |
|----------|-------|
| **Profile** | `get_user_profile`, `get_body_measurements` |
| **Recovery** | `get_latest_recovery`, `get_recovery_history` |
| **Sleep** | `get_latest_sleep`, `get_sleep_history` |
| **Workouts** | `get_recent_workouts`, `get_workouts_by_date` |
| **Cycles** | `get_latest_cycle`, `get_cycle_history` |
| **Summaries** | `get_today_summary`, `get_weekly_summary`, `get_monthly_summary` |

## Deployment (Fly.io)

The server is configured for always-on deployment on Fly.io so it's accessible from the Claude mobile app.

```bash
fly launch       # first time only
fly secrets set \
  WHOOP_CLIENT_ID=... \
  WHOOP_CLIENT_SECRET=... \
  WHOOP_REFRESH_TOKEN=...
fly deploy
```

The refresh token is automatically persisted to a 1 GB volume at `/data/refresh_token.txt` and rotated on every API call — no manual token management needed after the initial setup.

## Project Structure

```
src/whoop_mcp/
├── server.py          # MCP server & tool definitions
├── whoop_client.py    # Whoop API HTTP helpers
├── auth.py            # OAuth token lifecycle
└── config.py          # Credentials & API endpoints
scripts/
└── get_token.py       # One-time OAuth setup
```

## Tech Stack

- [FastMCP](https://github.com/jlowin/fastmcp) — MCP server framework
- [httpx](https://www.python-httpx.org/) — async HTTP client
- [Fly.io](https://fly.io/) — deployment platform

## License

MIT
