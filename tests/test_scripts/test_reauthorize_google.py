import json
import stat

import pytest
from google.auth.exceptions import GoogleAuthError

from scripts.reauthorize_google import (
    backup_token,
    build_client_config,
    require_write_role,
    write_token_atomic,
)
from src.models.google_calendar_config import GoogleCalendarConfig


def test_configured_scopes_are_limited_to_readonly_and_events():
    scopes = GoogleCalendarConfig().scopes

    assert "https://www.googleapis.com/auth/calendar.readonly" in scopes
    assert "https://www.googleapis.com/auth/calendar.events" in scopes
    assert "https://www.googleapis.com/auth/calendar" not in scopes


def test_require_write_role_rejects_an_account_without_write_access():
    with pytest.raises(GoogleAuthError, match="writer or owner"):
        require_write_role({"calendar-id": "reader"}, "calendar-id")


def test_require_write_role_rejects_a_missing_calendar():
    with pytest.raises(GoogleAuthError, match="writer or owner"):
        require_write_role({}, "calendar-id")


def test_require_write_role_accepts_writer_and_owner():
    require_write_role({"calendar-id": "writer"}, "calendar-id")
    require_write_role({"calendar-id": "owner"}, "calendar-id")


def test_reauthorize_ignores_scopes_stored_on_a_stale_token(tmp_path, monkeypatch):
    token_path = tmp_path / "token.json"
    token_path.write_text(
        json.dumps(
            {
                "client_id": "client-id",
                "client_secret": "client-secret",
                "token_uri": "https://oauth2.googleapis.com/token",
                "scopes": ["https://www.googleapis.com/auth/calendar"],
            }
        ),
        encoding="utf-8",
    )
    observed: dict[str, object] = {}

    class FakeCredentials:
        refresh_token = "refresh-token"
        valid = True

        def refresh(self, request):
            return None

        def to_json(self):
            return json.dumps({"refresh_token": "refresh-token"})

    class FakeFlow:
        @classmethod
        def from_client_config(cls, config, scopes):
            observed["scopes"] = scopes
            return cls()

        def run_local_server(self, **kwargs):
            observed["flow_kwargs"] = kwargs
            return FakeCredentials()

    monkeypatch.setattr("scripts.reauthorize_google.InstalledAppFlow", FakeFlow)
    monkeypatch.setattr(
        "scripts.reauthorize_google._calendar_roles",
        lambda credentials: {"calendar-id": "owner"},
    )

    from scripts.reauthorize_google import reauthorize

    reauthorize(
        token_path=token_path,
        backup_dir=tmp_path / "backups",
        expected_calendar_id="calendar-id",
        open_browser=False,
    )

    assert observed["scopes"] == GoogleCalendarConfig().scopes
    assert observed["flow_kwargs"].get("include_granted_scopes") is None


def test_build_client_config_uses_existing_oauth_client_metadata():
    token = {
        "client_id": "client-id",
        "client_secret": "client-secret",
        "token_uri": "https://oauth2.googleapis.com/token",
    }

    config = build_client_config(token)

    assert config["installed"]["client_id"] == "client-id"
    assert config["installed"]["client_secret"] == "client-secret"
    assert config["installed"]["token_uri"] == "https://oauth2.googleapis.com/token"
    assert config["installed"]["redirect_uris"] == ["http://localhost"]


def test_backup_token_copies_credentials_with_private_permissions(tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text('{"refresh_token":"value"}', encoding="utf-8")

    backup_path = backup_token(token_path, tmp_path / "backups")

    assert backup_path.exists()
    assert backup_path.read_text(encoding="utf-8") == token_path.read_text(
        encoding="utf-8"
    )
    assert stat.S_IMODE(backup_path.stat().st_mode) == 0o600


def test_write_token_atomic_replaces_file_without_exposing_contents(tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text("old", encoding="utf-8")

    write_token_atomic(token_path, json.dumps({"refresh_token": "new"}))

    assert json.loads(token_path.read_text(encoding="utf-8")) == {
        "refresh_token": "new"
    }
