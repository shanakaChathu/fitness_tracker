import os
import time
import httpx
from .config import WHOOP_CLIENT_ID, WHOOP_CLIENT_SECRET, WHOOP_TOKEN_URL

# In-memory token cache
_access_token: str | None = None
_token_expiry: float = 0.0

# File to persist the rotated refresh token across restarts
_REFRESH_TOKEN_FILE = "/data/refresh_token.txt"


def _load_refresh_token() -> str:
    """
    Load the refresh token with this priority:
      1. Persisted file on disk (written after token rotation)
      2. WHOOP_REFRESH_TOKEN environment variable (Fly.io secret)
    """
    try:
        token = open(_REFRESH_TOKEN_FILE).read().strip()
        if token:
            return token
    except FileNotFoundError:
        pass

    token = os.environ.get("WHOOP_REFRESH_TOKEN", "")
    if not token:
        raise RuntimeError(
            "WHOOP_REFRESH_TOKEN is not set. Run scripts/get_token.py to obtain one."
        )
    return token


def _save_refresh_token(token: str) -> None:
    """Persist the latest refresh token to disk so it survives restarts."""
    try:
        os.makedirs(os.path.dirname(_REFRESH_TOKEN_FILE), exist_ok=True)
        with open(_REFRESH_TOKEN_FILE, "w") as f:
            f.write(token)
    except OSError:
        # /data volume may not exist locally — fall back to env var only
        os.environ["WHOOP_REFRESH_TOKEN"] = token


async def get_access_token() -> str:
    """
    Return a valid Whoop access token, refreshing automatically when expired.
    Persists rotated refresh tokens to /data/refresh_token.txt so they
    survive Fly.io machine restarts.
    """
    global _access_token, _token_expiry

    # Return cached token if still valid (60s buffer before expiry)
    if _access_token and time.time() < _token_expiry - 60:
        return _access_token

    refresh_token = _load_refresh_token()

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

    # Whoop rotates the refresh token on every use — persist the new one immediately
    new_refresh = data.get("refresh_token", "")
    if new_refresh and new_refresh != refresh_token:
        _save_refresh_token(new_refresh)

    return _access_token
