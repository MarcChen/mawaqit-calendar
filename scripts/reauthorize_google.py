# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "google-api-python-client",
#   "google-auth-httplib2",
#   "google-auth-oauthlib",
# ]
# ///
# How to run: uv run python -m scripts.reauthorize_google

import argparse
import json
import os
import stat
import tempfile
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.models.google_calendar_config import GoogleCalendarConfig

DEFAULT_TOKEN_PATH = Path("token.json")
DEFAULT_BACKUP_DIR = Path("data/oauth-backups")
WRITER_ROLES = frozenset({"owner", "writer"})
DEFAULT_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
DEFAULT_TOKEN_URI = "https://oauth2.googleapis.com/token"


def build_client_config(token: dict[str, Any]) -> dict[str, Any]:
    """Build an installed-app OAuth config from existing token metadata."""
    client_id = token.get("client_id")
    client_secret = token.get("client_secret")
    if not client_id or not client_secret:
        raise ValueError(
            "The existing token has no OAuth client metadata. "
            "Provide --credentials with the downloaded OAuth client JSON."
        )

    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": DEFAULT_AUTH_URI,
            "token_uri": token.get("token_uri", DEFAULT_TOKEN_URI),
            "redirect_uris": ["http://localhost"],
        }
    }


def _read_token(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Token file does not exist: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Token file must contain an object: {path}")
    return data


def _read_credentials(path: Path | None, token: dict[str, Any]) -> dict[str, Any]:
    if path is None:
        return build_client_config(token)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Credentials file must contain an object: {path}")
    return data


def backup_token(token_path: Path, backup_dir: Path) -> Path:
    """Copy the current token into an ignored, private backup directory."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"token-{timestamp}.json"
    backup_path.write_bytes(token_path.read_bytes())
    backup_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    return backup_path


def write_token_atomic(token_path: Path, serialized_token: str) -> None:
    """Replace a token file atomically with private permissions."""
    token_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=token_path.parent,
            prefix=f".{token_path.name}.",
            delete=False,
        ) as temporary_file:
            temporary_file.write(serialized_token)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
            temporary_path = Path(temporary_file.name)
        temporary_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        temporary_path.replace(token_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _calendar_roles(credentials: Any) -> dict[str, str]:
    service = build("calendar", "v3", credentials=credentials)
    result = service.calendarList().list(maxResults=250).execute()
    return {
        str(item["id"]): str(item.get("accessRole", ""))
        for item in result.get("items", [])
        if isinstance(item, dict) and item.get("id")
    }


def require_write_role(roles: Mapping[str, str], calendar_id: str) -> None:
    """Refuse a grant that cannot write to the requested calendar."""
    role = roles.get(calendar_id, "")
    if role not in WRITER_ROLES:
        raise GoogleAuthError(
            f"The reauthorized account has role '{role or 'none'}' on {calendar_id}; "
            "writer or owner access is required. Token file was not changed."
        )


def reauthorize(
    token_path: Path,
    backup_dir: Path,
    credentials_path: Path | None = None,
    expected_calendar_id: str | None = None,
    open_browser: bool = True,
) -> Path:
    """Obtain, validate, back up, and install a new OAuth token."""
    old_token = _read_token(token_path)
    client_config = _read_credentials(credentials_path, old_token)
    scopes = list(GoogleCalendarConfig().scopes)

    flow = InstalledAppFlow.from_client_config(client_config, scopes=scopes)
    credentials = flow.run_local_server(
        port=0,
        open_browser=open_browser,
        access_type="offline",
        prompt="consent",
    )
    if not credentials.valid:
        credentials.refresh(Request())
    if not credentials.refresh_token:
        raise GoogleAuthError(
            "Google did not return a refresh token. Revoke prior grants and try again."
        )

    roles = _calendar_roles(credentials)
    if expected_calendar_id:
        require_write_role(roles, expected_calendar_id)

    serialized_token = credentials.to_json()
    backup_path = backup_token(token_path, backup_dir)
    write_token_atomic(token_path, serialized_token)
    return backup_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reauthorize Google Calendar without deleting calendar data."
    )
    parser.add_argument("--token-path", type=Path, default=DEFAULT_TOKEN_PATH)
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    parser.add_argument("--credentials", type=Path)
    parser.add_argument("--expected-calendar-id")
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Print the authorization URL instead of opening a browser.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        backup_path = reauthorize(
            token_path=args.token_path,
            backup_dir=args.backup_dir,
            credentials_path=args.credentials,
            expected_calendar_id=args.expected_calendar_id,
            open_browser=not args.no_browser,
        )
    except (
        FileNotFoundError,
        GoogleAuthError,
        HttpError,
        OSError,
        ValueError,
    ) as error:
        print(f"Reauthorization failed: {error}")
        return 1

    print("Google Calendar authorization succeeded.")
    print(f"Previous token backed up to: {backup_path}")
    print("No calendars were changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
