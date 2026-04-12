"""
One-time script to obtain a Whoop OAuth refresh token.

Usage:
    1. Copy .env.example to .env and fill in WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET
    2. Run:  python scripts/get_token.py
    3. Your browser will open — log into Whoop and approve the app
    4. Copy the WHOOP_REFRESH_TOKEN printed at the end
    5. Set it as a Fly.io secret:  fly secrets set WHOOP_REFRESH_TOKEN=<token>

You only need to run this once. The MCP server refreshes the access token automatically.
"""

import os
import secrets
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

try:
    import httpx
    from dotenv import load_dotenv
except ImportError:
    print("Missing dependencies. Run:  pip install httpx python-dotenv")
    sys.exit(1)

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

CLIENT_ID = os.environ.get("WHOOP_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("WHOOP_CLIENT_SECRET", "")
REDIRECT_URI = "http://localhost:8080/callback"
SCOPES = "offline read:profile read:body_measurement read:cycles read:recovery read:sleep read:workout"
AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"

if not CLIENT_ID or not CLIENT_SECRET:
    print("ERROR: WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET must be set in .env")
    sys.exit(1)

# ── Local callback server ─────────────────────────────────────────────────────

_auth_code: str | None = None
_state = secrets.token_urlsafe(16)


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        global _auth_code
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            _auth_code = params["code"][0]
            returned_state = params.get("state", [None])[0]
            if returned_state != _state:
                self._respond(400, b"<h1>State mismatch - possible CSRF. Try again.</h1>")
                return
            self._respond(200, b"<h1>Authorization successful! You can close this tab.</h1>")
        else:
            error = params.get("error", ["unknown"])[0]
            self._respond(400, f"<h1>Authorization failed: {error}</h1>".encode())

    def _respond(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        pass  # suppress server logs


# ── OAuth flow ────────────────────────────────────────────────────────────────


def main() -> None:
    # Build authorization URL
    auth_params = urlencode(
        {
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": SCOPES,
            "state": _state,
        }
    )
    url = f"{AUTH_URL}?{auth_params}"

    print("Opening Whoop authorization page in your browser...")
    print(f"If it doesn't open automatically, visit:\n  {url}\n")
    webbrowser.open(url)

    # Wait for the callback
    print("Waiting for Whoop to redirect to http://localhost:8080/callback ...")
    server = HTTPServer(("localhost", 8080), _CallbackHandler)
    server.handle_request()  # blocks until one request is received

    if not _auth_code:
        print("ERROR: No authorization code received.")
        sys.exit(1)

    # Exchange authorization code for tokens
    print("\nExchanging authorization code for tokens...")
    response = httpx.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": _auth_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if response.status_code != 200:
        print(f"ERROR: Token exchange failed ({response.status_code}): {response.text}")
        sys.exit(1)

    tokens = response.json()
    refresh_token = tokens.get("refresh_token", "")

    if not refresh_token:
        print("ERROR: No refresh token in response. Make sure 'offline' scope is included.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("SUCCESS! Your Whoop refresh token:")
    print(f"\n  {refresh_token}\n")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Add to your local .env file:")
    print(f"       WHOOP_REFRESH_TOKEN={refresh_token}")
    print("\n  2. Set as a Fly.io secret (for deployment):")
    print(f"       fly secrets set WHOOP_REFRESH_TOKEN={refresh_token}")
    print("\nYou're all set!")


if __name__ == "__main__":
    main()
