import json
from datetime import datetime

from icalendar import Calendar, Event

from src.calendar.refresh_planner import source_year_window
from src.calendar.refresh_service import (
    _events_in_window,
    _load_registry_entry,
    _registry_slugs,
    _write_window_calendar,
)


def test_load_registry_entry_returns_metadata_and_calendar_id(tmp_path):
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "mosque": {
                    "url": "https://mawaqit.net/fr/mosque",
                    "calendarUrl": (
                        "https://calendar.google.com/calendar/ical/"
                        "calendar-id%40group.calendar.google.com/public/basic.ics"
                    ),
                }
            }
        ),
        encoding="utf-8",
    )

    metadata = _load_registry_entry(registry_path, "mosque")

    assert metadata["url"] == "https://mawaqit.net/fr/mosque"
    assert "calendar-id@group.calendar.google.com" in metadata["calendarUrl"].replace(
        "%40", "@"
    )


def test_registry_slugs_returns_registered_mosques(tmp_path):
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps({"mosque-a": {}, "mosque-b": {}}))

    assert _registry_slugs(registry_path) == ["mosque-a", "mosque-b"]


def test_write_window_calendar_only_keeps_in_window_events(tmp_path):
    calendar = Calendar()
    inside = Event()
    inside.add("uid", "inside@mawaqit-calendar")
    inside.add("dtstart", datetime(2026, 2, 1, 6, 0))
    calendar.add_component(inside)
    outside = Event()
    outside.add("uid", "outside@mawaqit-calendar")
    outside.add("dtstart", datetime(2027, 2, 1, 6, 0))
    calendar.add_component(outside)
    output_path = tmp_path / "window.ics"

    _write_window_calendar(calendar, source_year_window(2026), output_path)

    saved = Calendar.from_ical(output_path.read_bytes())
    saved_uids = [
        str(component["uid"])
        for component in saved.walk()
        if component.name == "VEVENT"
    ]
    assert saved_uids == ["inside@mawaqit-calendar"]


def test_events_in_window_keeps_only_requested_dates():
    calendar = Calendar()
    event = Event()
    event.add("uid", "inside@mawaqit-calendar")
    event.add("dtstart", datetime(2026, 2, 1, 6, 0))
    calendar.add_component(event)
    outside = Event()
    outside.add("uid", "outside@mawaqit-calendar")
    outside.add("dtstart", datetime(2027, 2, 1, 6, 0))
    calendar.add_component(outside)

    events = _events_in_window(calendar, source_year_window(2026))

    assert events == [{"uid": "inside@mawaqit-calendar"}]
