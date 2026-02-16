#!/usr/bin/env python3
"""
Upwork OAuth 2.0 Setup Script

Completes the OAuth Authorization Code flow for the Upwork API.
After running, tokens are saved to ~/.mcp-upwork/tokens.json so the
MCP server can use them for real-time job search.

Usage:
    1. Set environment variables:
       export UPWORK_CLIENT_ID=your_client_id
       export UPWORK_CLIENT_SECRET=your_client_secret
    2. Run: python3 scripts/upwork_oauth_setup.py
    3. Browser opens → authorize the app on Upwork
    4. Tokens are saved automatically

Requirements:
    pip install requests
"""

import http.server
import json
import os
import secrets
import sys
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

# Configuration
CLIENT_ID = os.getenv("UPWORK_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("UPWORK_CLIENT_SECRET", "")
CALLBACK_PORT = 8080
CALLBACK_PATH = "/callback"
CALLBACK_URL = f"http://localhost:{CALLBACK_PORT}{CALLBACK_PATH}"

# Upwork OAuth 2.0 endpoints
AUTH_URL = "https://www.upwork.com/ab/account-security/oauth2/authorize"
TOKEN_URL = "https://www.upwork.com/api/v3/oauth2/token"

# MCP token storage
MCP_DIR = Path.home() / ".mcp-upwork"
TOKEN_FILE = MCP_DIR / "tokens.json"


def save_tokens_plain(tokens: dict) -> None:
    """Save tokens as plain JSON (MCP server handles its own encryption)."""
    MCP_DIR.mkdir(exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(tokens, indent=2))
    TOKEN_FILE.chmod(0o600)
    print(f"Tokens saved to {TOKEN_FILE}")


def save_tokens_encrypted(tokens: dict) -> None:
    """Save tokens using AES-256-CBC encryption matching MCP server format."""
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding

        key_file = MCP_DIR / ".key"
        if not key_file.exists():
            print("WARNING: No encryption key found at ~/.mcp-upwork/.key")
            print("Saving as plain JSON instead.")
            save_tokens_plain(tokens)
            return

        key = key_file.read_bytes()
        iv = secrets.token_bytes(16)

        # PKCS7 padding
        padder = padding.PKCS7(128).padder()
        data = json.dumps(tokens).encode()
        padded = padder.update(data) + padder.finalize()

        # AES-256-CBC encrypt
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded) + encryptor.finalize()

        # Store as iv:encrypted (hex encoded)
        blob = iv.hex() + ":" + encrypted.hex()

        MCP_DIR.mkdir(exist_ok=True)
        TOKEN_FILE.write_text(blob)
        TOKEN_FILE.chmod(0o600)
        print(f"Encrypted tokens saved to {TOKEN_FILE}")

    except ImportError:
        print("cryptography package not installed, saving as plain JSON.")
        save_tokens_plain(tokens)


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that captures the OAuth callback."""

    auth_code = None
    state_received = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != CALLBACK_PATH:
            self.send_response(404)
            self.end_headers()
            return

        params = urllib.parse.parse_qs(parsed.query)

        if "error" in params:
            error = params["error"][0]
            desc = params.get("error_description", ["Unknown"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"<h1>Authorization Failed</h1><p>{error}: {desc}</p>".encode()
            )
            print(f"\nERROR: Authorization failed: {error} - {desc}")
            return

        if "code" not in params:
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Missing authorization code</h1>")
            return

        OAuthCallbackHandler.auth_code = params["code"][0]
        OAuthCallbackHandler.state_received = params.get("state", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(
            b"<h1>Authorization Successful!</h1>"
            b"<p>You can close this tab. Tokens are being saved...</p>"
        )

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def exchange_code_for_tokens(auth_code: str) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": CALLBACK_URL,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )

    if resp.status_code != 200:
        print(f"ERROR: Token exchange failed ({resp.status_code}): {resp.text}")
        sys.exit(1)

    data = resp.json()
    return {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token", ""),
        "token_type": data.get("token_type", "Bearer"),
        "expires_in": data.get("expires_in", 86400),
        "obtained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def refresh_access_token(refresh_token: str) -> dict:
    """Use refresh token to get a new access token."""
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )

    if resp.status_code != 200:
        print(f"ERROR: Token refresh failed ({resp.status_code}): {resp.text}")
        return {}

    data = resp.json()
    return {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token", refresh_token),
        "token_type": data.get("token_type", "Bearer"),
        "expires_in": data.get("expires_in", 86400),
        "obtained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("ERROR: Set UPWORK_CLIENT_ID and UPWORK_CLIENT_SECRET env vars first.")
        print()
        print("Example:")
        print("  export UPWORK_CLIENT_ID=86d306028686ebfd962deae387fa3cc7")
        print('  export UPWORK_CLIENT_SECRET="your_secret_here"')
        print("  python3 scripts/upwork_oauth_setup.py")
        sys.exit(1)

    # Check for --refresh flag
    if "--refresh" in sys.argv:
        if not TOKEN_FILE.exists():
            print("ERROR: No existing tokens to refresh.")
            sys.exit(1)
        tokens = json.loads(TOKEN_FILE.read_text())
        if not tokens.get("refresh_token"):
            print("ERROR: No refresh_token in stored tokens.")
            sys.exit(1)
        print("Refreshing access token...")
        new_tokens = refresh_access_token(tokens["refresh_token"])
        if new_tokens:
            save_tokens_plain(new_tokens)
            print("Token refreshed successfully!")
        sys.exit(0)

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Build authorization URL
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": CALLBACK_URL,
        "state": state,
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    # Start local callback server
    server = http.server.HTTPServer(("localhost", CALLBACK_PORT), OAuthCallbackHandler)
    server_thread = threading.Thread(target=server.handle_request, daemon=True)
    server_thread.start()

    print("=" * 60)
    print("Upwork OAuth 2.0 Setup")
    print("=" * 60)
    print()
    print("Opening browser for Upwork authorization...")
    print(f"If browser doesn't open, visit:\n{auth_url}")
    print()
    print("Waiting for callback on localhost:8080...")

    webbrowser.open(auth_url)

    # Wait for the callback (max 5 minutes)
    server_thread.join(timeout=300)

    if not OAuthCallbackHandler.auth_code:
        print("\nERROR: Timed out waiting for authorization (5 min).")
        sys.exit(1)

    # Verify state matches
    if OAuthCallbackHandler.state_received != state:
        print("\nWARNING: State mismatch — possible CSRF. Proceeding anyway.")

    print("\nAuthorization code received! Exchanging for tokens...")

    tokens = exchange_code_for_tokens(OAuthCallbackHandler.auth_code)
    save_tokens_plain(tokens)

    print()
    print("=" * 60)
    print("SUCCESS! Upwork OAuth tokens saved.")
    print("=" * 60)
    print()
    print("The MCP server can now use these tokens for API calls.")
    print("Test with: upwork_search_jobs_by_keywords or upwork_get_latest_jobs")
    print()
    print("To refresh later: python3 scripts/upwork_oauth_setup.py --refresh")


if __name__ == "__main__":
    main()
