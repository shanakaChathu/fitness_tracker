import os
import time
import httpx
from .config import WHOOP_CLIENT_ID, WHOOP_CLIENT_SECRET, WHOOP_TOKEN_URL

# In-memory token cache
_access_token: str | None = None
_token_expiry: float = 0.0


async def get_access_token() -> str:
    """
    Return a valid Whoop access token, refreshing automatically when expired.
    Uses the WHOOP_REFRESH_TOKEN env var and caches the access token in memory.
    """
    global _access_token, _token_expiry

    # Return cached token if still valid (60s buffer before expiry)
    if _access_token and time.time() < _token_expiry - 60:
        return _access_token

    refresh_token = os.environ.get("WHOOP_REFRESH_TOKEN", "")
    if not refresh_token:
        raise RuntimeError(
            "WHOOP_REFRESH_TOKEN is not set. Run scripts/get_token.py to obtain one."
        )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            WHOOP_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": WHOOP_CLIENT_ID,
                "client_secret": WHOOP_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        data = response.json()

    _access_token = data["access_token"]
    _token_expiry = time.time() + data.get("expires_in", 3600)

    # Whoop may rotate the refresh token — keep the env var up-to-date in memory
    new_refresh = data.get("refresh_token")
    if new_refresh and new_refresh != refresh_token:
        os.environ["WHOOP_REFRESH_TOKEN"] = new_refresh

    return _access_token
