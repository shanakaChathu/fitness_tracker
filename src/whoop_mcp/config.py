import os
from dotenv import load_dotenv

load_dotenv()

# Whoop OAuth credentials (set as Fly.io secrets in production)
WHOOP_CLIENT_ID: str = os.environ["WHOOP_CLIENT_ID"]
WHOOP_CLIENT_SECRET: str = os.environ["WHOOP_CLIENT_SECRET"]
WHOOP_REFRESH_TOKEN: str = os.environ["WHOOP_REFRESH_TOKEN"]

# Whoop API endpoints
WHOOP_BASE_URL = "https://api.prod.whoop.com/developer"
WHOOP_TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
WHOOP_AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"

# OAuth settings
REDIRECT_URI = "http://localhost:8080/callback"
SCOPES = "offline read:profile read:body_measurement read:cycles read:recovery read:sleep read:workout"

# MCP server settings
PORT = int(os.getenv("PORT", "8080"))
HOST = os.getenv("HOST", "0.0.0.0")
