"""
Run this script ONCE locally to set up Google Calendar OAuth2 authentication.

1. Go to https://console.cloud.google.com/
2. Create a project, enable Google Calendar API
3. Create OAuth2 credentials (Desktop app), download as credentials.json
4. Place credentials.json in the same directory as this script
5. Run: python setup_auth.py
6. Copy the printed GOOGLE_TOKEN_JSON value into your Railway environment variables

You only need to do this once. The token auto-refreshes.
"""

import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


def main():
    creds = None

    if Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(CREDENTIALS_FILE).exists():
                print(f"ERROR: {CREDENTIALS_FILE} not found.")
                print("Download it from Google Cloud Console > APIs & Services > Credentials")
                return

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            print("\nEr opent nu een browser. Log in met je Google-account en geef toestemming.")
            print("Als er geen browser opent, kopieer dan de URL die hieronder verschijnt.\n")
            creds = flow.run_local_server(port=8080, open_browser=True)

        Path(TOKEN_FILE).write_text(creds.to_json())

    token_data = json.loads(Path(TOKEN_FILE).read_text())
    token_json_str = json.dumps(token_data)

    print("\n" + "=" * 60)
    print("SUCCESS! Copy this value into Railway as GOOGLE_TOKEN_JSON:")
    print("=" * 60)
    print(token_json_str)
    print("=" * 60)
    print("\nAlso set GOOGLE_CALENDAR_ID=primary (or your specific calendar ID)")


if __name__ == "__main__":
    main()
