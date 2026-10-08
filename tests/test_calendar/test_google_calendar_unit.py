import logging
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from icalendar import Calendar, Event

from src.calendar.google_calendar import GoogleCalendarClient
from src.models.google_calendar_config import GoogleCalendarConfig


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def execute(self):
        return self.data


class FakeHttpError(Exception):
    def __init__(self, status, reason=""):
        self.resp = SimpleNamespace(status=status)
        self.error_details = [{"domain": "global", "reason": reason}]


class FakeEvents:
    def __init__(self, pages):
        self.pages = list(pages)
        self.list_calls = []
        self.inserted_bodies = []
        self.call_names = []
        self.deleted_event_ids = []

    def list(self, **kwargs):
        self.list_calls.append(kwargs)
        return FakeResponse(self.pages.pop(0))

    def insert(self, **kwargs):
        self.call_names.append("insert")
        self.inserted_bodies.append(kwargs["body"])
        return self

    def import_(self, **kwargs):
        self.call_names.append("import_")
        self.inserted_bodies.append(kwargs["body"])
        return self

    def delete(self, **kwargs):
        self.deleted_event_ids.append(kwargs["eventId"])
        return self


class FakeBatch:
    def __init__(self, callback, outcomes=None, execute_error=None):
        self.callback = callback
        self.outcomes = outcomes if outcomes is not None else []
        self.execute_error = execute_error
        self.execute_count = 0
        self.requests = []

    def add(self, request, request_id):
        self.requests.append((request_id, request))

    def execute(self, http=None):
        self.http = http
        self.execute_count += 1
        if self.execute_error is not None:
            error = self.execute_error
            self.execute_error = None
            raise error
        outcome = self.outcomes.pop(0) if self.outcomes else {}
        for request_id, _ in self.requests:
            self.callback(request_id, {}, outcome.get(request_id))


class FakeService:
    def __init__(
        self,
        pages=None,
        batch_outcomes=None,
        batch_execute_errors=None,
    ):
        self._events = FakeEvents(pages or [])
        self.batch_outcomes = list(batch_outcomes or [])
        self.batch_execute_errors = list(batch_execute_errors or [])
        self.batches = []

    def events(self):
        return self._events

    def new_batch_http_request(self, callback):
        execute_error = (
            self.batch_execute_errors.pop(0) if self.batch_execute_errors else None
        )
        batch = FakeBatch(callback, self.batch_outcomes, execute_error)
        self.batches.append(batch)
        return batch


def make_client(monkeypatch, service):
    monkeypatch.setattr(GoogleCalendarClient, "_authenticate", lambda self: None)
    client = GoogleCalendarClient(GoogleCalendarConfig())
    client.service = service
    client.logger = logging.getLogger(__name__)
    return client


def test_list_events_paginates_and_filters_by_window(monkeypatch):
    service = FakeService(
        [
            {"items": [{"id": "event-1"}], "nextPageToken": "page-2"},
            {"items": [{"id": "event-2"}]},
        ]
    )
    client = make_client(monkeypatch, service)

    events = client.list_events(
        "calendar-id",
        time_min="2026-01-01T00:00:00Z",
        time_max="2026-07-01T00:00:00Z",
    )

    assert events == [{"id": "event-1"}, {"id": "event-2"}]
    assert service._events.list_calls[0]["timeMin"] == "2026-01-01T00:00:00Z"
    assert service._events.list_calls[0]["timeMax"] == "2026-07-01T00:00:00Z"
    assert service._events.list_calls[0]["singleEvents"] is True
    assert service._events.list_calls[1]["pageToken"] == "page-2"


def test_add_events_sends_stable_ical_uid_without_custom_id(monkeypatch, tmp_path):
    service = FakeService()
    client = make_client(monkeypatch, service)
    calendar = Calendar()
    event = Event()
    event.add("uid", "mosque-20260101-fajr@mawaqit-calendar")
    event.add("summary", "Fajr")
    event.add("dtstart", datetime(2026, 1, 1, 6, 0))
    event.add("dtend", datetime(2026, 1, 1, 6, 15))
    calendar.add_component(event)
    ics_path = Path(tmp_path) / "events.ics"
    ics_path.write_bytes(calendar.to_ical())

    client.add_events_from_ics_batch("calendar-id", str(ics_path))
    client.add_events_from_ics_batch("calendar-id", str(ics_path))

    first_body = service._events.inserted_bodies[0]
    second_body = service._events.inserted_bodies[1]
    assert first_body["iCalUID"] == "mosque-20260101-fajr@mawaqit-calendar"
    assert first_body["iCalUID"] == second_body["iCalUID"]
    assert "id" not in first_body
    assert service._events.call_names == ["import_", "import_"]


def test_add_events_retries_ambiguous_timeout_without_duplicate_insert(
    monkeypatch, tmp_path
):
    service = FakeService(
        batch_outcomes=[{}, {"event_0": FakeHttpError(409)}],
        batch_execute_errors=[TimeoutError("read timed out"), None],
    )
    client = make_client(monkeypatch, service)
    calendar = Calendar()
    event = Event()
    event.add("uid", "mosque-20260101-fajr@mawaqit-calendar")
    event.add("dtstart", datetime(2026, 1, 1, 6, 0))
    event.add("dtend", datetime(2026, 1, 1, 6, 15))
    calendar.add_component(event)
    ics_path = Path(tmp_path) / "events.ics"
    ics_path.write_bytes(calendar.to_ical())
    monkeypatch.setattr("src.calendar.google_calendar.time.sleep", lambda _: None)

    client.add_events_from_ics_batch("calendar-id", str(ics_path))

    assert service.batches[0].execute_count == 2
    assert (
        service._events.inserted_bodies[0]["iCalUID"]
        == "mosque-20260101-fajr@mawaqit-calendar"
    )


def test_add_events_retries_transient_server_error(monkeypatch, tmp_path):
    service = FakeService(
        batch_outcomes=[{"event_0": FakeHttpError(503, reason="backendError")}, {}],
        batch_execute_errors=[None, None],
    )
    client = make_client(monkeypatch, service)
    calendar = Calendar()
    event = Event()
    event.add("uid", "mosque-20260101-fajr@mawaqit-calendar")
    event.add("dtstart", datetime(2026, 1, 1, 6, 0))
    event.add("dtend", datetime(2026, 1, 1, 6, 15))
    calendar.add_component(event)
    ics_path = Path(tmp_path) / "events.ics"
    ics_path.write_bytes(calendar.to_ical())
    monkeypatch.setattr("src.calendar.google_calendar.time.sleep", lambda _: None)

    client.add_events_from_ics_batch("calendar-id", str(ics_path))

    assert service.batches[0].execute_count == 2


def test_add_events_fails_fast_on_invalid_request(monkeypatch, tmp_path):
    service = FakeService(
        batch_outcomes=[{"event_0": FakeHttpError(400, reason="invalid")}]
    )
    client = make_client(monkeypatch, service)
    calendar = Calendar()
    event = Event()
    event.add("uid", "mosque-20260101-fajr@mawaqit-calendar")
    event.add("dtstart", datetime(2026, 1, 1, 6, 0))
    event.add("dtend", datetime(2026, 1, 1, 6, 15))
    calendar.add_component(event)
    ics_path = Path(tmp_path) / "events.ics"
    ics_path.write_bytes(calendar.to_ical())
    monkeypatch.setattr("src.calendar.google_calendar.time.sleep", lambda _: None)

    with pytest.raises(RuntimeError, match="HTTP 400 invalid"):
        client.add_events_from_ics_batch("calendar-id", str(ics_path))

    assert service.batches[0].execute_count == 1


def test_delete_events_batch_treats_already_deleted_event_as_success(monkeypatch):
    service = FakeService(batch_outcomes=[{"delete_0": FakeHttpError(404)}])
    client = make_client(monkeypatch, service)

    client.delete_events_batch("calendar-id", ["event-1"])


def test_delete_events_batch_reports_http_status_and_reason(monkeypatch):
    service = FakeService(
        batch_outcomes=[{"delete_0": FakeHttpError(403, reason="forbidden")}]
    )
    client = make_client(monkeypatch, service)

    with pytest.raises(RuntimeError, match="HTTP 403 forbidden"):
        client.delete_events_batch("calendar-id", ["event-1"])


def test_delete_events_batch_removes_requested_ids(monkeypatch):
    service = FakeService()
    client = make_client(monkeypatch, service)

    client.delete_events_batch("calendar-id", ["event-1", "event-2"])
