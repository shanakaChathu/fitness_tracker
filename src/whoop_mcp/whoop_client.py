from datetime import datetime, timedelta, timezone
from typing import Any
import httpx
from .auth import get_access_token
from .config import WHOOP_BASE_URL


async def whoop_get(endpoint: str, params: dict[str, Any] | None = None) -> dict:
    """Make a single authenticated GET request to the Whoop API."""
    token = await get_access_token()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{WHOOP_BASE_URL}{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
            params=params or {},
        )
        response.raise_for_status()
        return response.json()


async def whoop_get_paginated(
    endpoint: str,
    params: dict[str, Any] | None = None,
    max_records: int = 25,
) -> list[dict]:
    """
    Fetch records from a paginated Whoop endpoint, following next_token cursors
    until max_records is reached or no more pages exist.
    """
    all_records: list[dict] = []
    p = dict(params or {})
    p.setdefault("limit", min(25, max_records))

    while len(all_records) < max_records:
        data = await whoop_get(endpoint, p)
        records = data.get("records", [])
        all_records.extend(records)

        next_token = data.get("next_token")
        if not next_token or not records:
            break
        p = dict(p)  # don't mutate original
        p["nextToken"] = next_token

    return all_records[:max_records]


def days_ago_iso(days: int) -> str:
    """Return an ISO 8601 UTC timestamp for N days ago."""
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
