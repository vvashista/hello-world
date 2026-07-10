#!/usr/bin/env python3
"""Upload IPTV M3U playlists to Google Drive.

Authentication options (pick one):

1. Service account (best for automation)
   - Create a service account in Google Cloud Console
   - Download the JSON key to e.g. credentials/service-account.json
   - Share your Drive folder with the service account email
   - export GOOGLE_APPLICATION_CREDENTIALS=credentials/service-account.json
   - export GOOGLE_DRIVE_FOLDER_ID=<folder_id_from_drive_url>

2. OAuth user account (interactive, one-time browser sign-in)
   - Create an OAuth Desktop client in Google Cloud Console
   - Download client_secret JSON to credentials/oauth-client.json
   - export GOOGLE_OAUTH_CLIENT_SECRET=credentials/oauth-client.json
   - export GOOGLE_DRIVE_FOLDER_ID=<optional_folder_id>
   - Run this script; complete sign-in in the browser when prompted
"""

from __future__ import annotations

import argparse
import mimetypes
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IPTV_DIR = ROOT / "iptv"
DEFAULT_FILES = [
    IPTV_DIR / "hindi-news.m3u",
    IPTV_DIR / "english-news.m3u",
    IPTV_DIR / "all-news.m3u",
    IPTV_DIR / "channel-guide.txt",
]
TOKEN_PATH = Path(os.environ.get("GOOGLE_DRIVE_TOKEN_PATH", ROOT / "credentials" / "drive-token.json"))
OAUTH_CLIENT = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", str(ROOT / "credentials" / "oauth-client.json"))
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def get_drive_service():
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    service_account_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if service_account_path and Path(service_account_path).exists():
        creds = service_account.Credentials.from_service_account_file(
            service_account_path, scopes=SCOPES
        )
        return build("drive", "v3", credentials=creds, cache_discovery=False)

    if not Path(OAUTH_CLIENT).exists():
        print(
            "Google Drive credentials not found.\n\n"
            "Set up one of the following:\n"
            "  1. GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json\n"
            "  2. GOOGLE_OAUTH_CLIENT_SECRET=/path/to/oauth-client.json (then sign in)\n\n"
            "Also set GOOGLE_DRIVE_FOLDER_ID to upload into a specific folder.\n"
            "See scripts/upload-to-drive.py header for full setup steps.",
            file=sys.stderr,
        )
        sys.exit(2)

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT, SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return build("drive", "v3", credentials=creds, cache_discovery=False)


def upload_file(service, path: Path, folder_id: str | None) -> dict:
    from googleapiclient.http import MediaFileUpload

    mime, _ = mimetypes.guess_type(path.name)
    mime = mime or "application/octet-stream"
    metadata: dict = {"name": path.name}
    if folder_id:
        metadata["parents"] = [folder_id]

    media = MediaFileUpload(str(path), mimetype=mime, resumable=True)
    result = (
        service.files()
        .create(body=metadata, media_body=media, fields="id,name,webViewLink,webContentLink")
        .execute()
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload IPTV playlists to Google Drive")
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Files to upload (defaults to all M3U playlists)",
    )
    parser.add_argument(
        "--folder-id",
        default=os.environ.get("GOOGLE_DRIVE_FOLDER_ID"),
        help="Google Drive folder ID (or set GOOGLE_DRIVE_FOLDER_ID)",
    )
    args = parser.parse_args()

    files = args.files or DEFAULT_FILES
    missing = [f for f in files if not f.exists()]
    if missing:
        for path in missing:
            print(f"Missing file: {path}", file=sys.stderr)
        sys.exit(1)

    service = get_drive_service()
    uploaded = []
    for path in files:
        print(f"Uploading {path.name}...")
        info = upload_file(service, path, args.folder_id)
        uploaded.append(info)
        print(f"  id:   {info.get('id')}")
        print(f"  link: {info.get('webViewLink')}")

    print(f"\nUploaded {len(uploaded)} file(s) to Google Drive.")
    if args.folder_id:
        print(f"Folder: https://drive.google.com/drive/folders/{args.folder_id}")


if __name__ == "__main__":
    main()
