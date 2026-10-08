import json
from pathlib import Path
from urllib.parse import unquote

import src.models.mosque as mosque_module
from src.models.google_calendar_config import GoogleCalendarConfig
from tests.utils.base_test_case import BaseTestCase

ROOT = Path(__file__).parents[2]
IVRY_SLUG = "annour-ivry-sur-seine"
IVRY_CALENDAR_ID = (
    "614e8a4cb293fcfc093f481be59e9c588a6d507a49d1b341413f16f62741c5a4"
    "@group.calendar.google.com"
)


def test_legacy_registry_contains_all_archived_mosques():
    metadata = json.loads(
        (ROOT / "registry" / "legacy_mosque_metadata.json").read_text(encoding="utf-8")
    )

    assert len(metadata) == 67
    assert IVRY_SLUG in metadata


def test_active_registry_contains_only_ivry():
    metadata = json.loads(
        (ROOT / "registry" / "mosque_calendars.json").read_text(encoding="utf-8")
    )

    assert list(metadata) == [IVRY_SLUG]
    assert IVRY_CALENDAR_ID in unquote(metadata[IVRY_SLUG]["calendarUrl"])


def test_google_calendar_credentials_default_to_repository_root():
    config = GoogleCalendarConfig()

    assert Path(config.credentials_path).parent == ROOT
    assert Path(config.token_path).parent == ROOT


def test_mosque_save_updates_the_active_registry(tmp_path, monkeypatch):
    registry_path = tmp_path / "registry" / "mosque_calendars.json"
    registry_path.parent.mkdir()
    registry_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(mosque_module, "GLOBAL_METADATA_PATH", str(registry_path))
    monkeypatch.setattr(
        mosque_module, "PROCESSED_DATA_DIR", str(tmp_path / "processed")
    )

    test_case = BaseTestCase()
    test_case.setup_method()
    mosque = test_case.create_sample_mosque()

    mosque.save()

    saved_metadata = json.loads(registry_path.read_text(encoding="utf-8"))
    assert mosque.id in saved_metadata
    assert saved_metadata[mosque.id]["name"] == mosque.name
