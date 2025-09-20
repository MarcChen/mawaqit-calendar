from datetime import datetime

import pytest
import requests
from icalendar import Calendar, Event

from src.calendar.google_calendar import GoogleCalendarClient
from src.models.google_calendar_config import GoogleCalendarConfig


@pytest.fixture(scope="class")
def google_calendar_client(request):
    config = GoogleCalendarConfig(
        credentials_path="client_secret.json",
        token_path="token.json",
        scopes=["https://www.googleapis.com/auth/calendar"],
    )
    client = GoogleCalendarClient(config)
    request.cls.client = client


@pytest.mark.usefixtures("google_calendar_client")
class TestGoogleCalendarClient:
    def test_create_calendar(self):
        calendar_id = self.client.create_calendar("Test Calendar")
        assert isinstance(calendar_id, str)
        assert calendar_id

    def test_list_calendars(self):
        calendars = self.client.list_calendars()
        assert isinstance(calendars, list)
        assert any(cal.get("summary") == "Test Calendar" for cal in calendars)

    def test_create_existing_calendar(self):
        with pytest.raises(ValueError):
            self.client.create_calendar("Test Calendar")

    def test_delete_blacklisted_calendar(self):
        with pytest.raises(ValueError):
            self.client.delete_calendar("kemar987415@gmail.com")

    def test_get_calendar_id_by_name(self):
        calendar_id = self.client.create_calendar("Unique Calendar Name")
        found_id = self.client.get_calendar_id_by_name("Unique Calendar Name")
        assert found_id == calendar_id
        self.client.delete_calendar(calendar_id)

    def test_delete_calendar(self):
        calendar_name = "Test Calendar"
        calendar_id = self.client.get_calendar_id_by_name(calendar_name)
        if not calendar_id:
            calendar_id = self.client.create_calendar(calendar_name)
        self.client.delete_calendar(calendar_id)
        assert self.client.get_calendar_id_by_name(calendar_name) is None

    def test_add_events_from_ics(self, tmp_path):
        try:
            calendar_id = self.client.create_calendar("ICS Calendar")
        except ValueError:
            calendar_id = self.client.get_calendar_id_by_name("ICS Calendar")

        # Create and add event from ICS
        ics_path = tmp_path / "test.ics"
        cal = Calendar()
        event = Event()
        event.add("summary", "Test Event")
        event.add("dtstart", datetime(2025, 1, 1, 12, 0, 0))
        event.add("dtend", datetime(2025, 1, 1, 13, 0, 0))
        cal.add_component(event)
        ics_path.write_bytes(cal.to_ical())
        self.client.add_events_from_ics_batch(calendar_id, str(ics_path))

        events = self.client.list_events(calendar_id)
        assert any(
            e.get("summary") == "Test Event"
            and e.get("start", {}).get("dateTime", "").startswith("2025-01-01T12:00:00")
            and e.get("end", {}).get("dateTime", "").startswith("2025-01-01T13:00:00")
            for e in events
        )
        self.client.delete_calendar(calendar_id)

    def test_make_calendar_public(self):
        calendar_id = self.client.create_calendar("Public Calendar")
        self.client.make_calendar_public(calendar_id)
        acl = self.client.service.acl().list(calendarId=calendar_id).execute()
        assert any(
            rule.get("scope", {}).get("type") == "default"
            and rule.get("role") == "reader"
            for rule in acl.get("items", [])
        )
        self.client.delete_calendar(calendar_id)

    def test_get_public_ics_url(self):
        calendar_id = self.client.create_calendar("Public ICS Calendar")
        self.client.make_calendar_public(calendar_id)
        url = self.client.get_public_ics_url(calendar_id)
        assert (
            url
            == f"https://calendar.google.com/calendar/ical/{calendar_id}/public/basic.ics"
        )
        response = requests.get(url)
        assert response.status_code == 200
        assert b"BEGIN:VCALENDAR" in response.content
        self.client.delete_calendar(calendar_id)

    def test_add_multiple_events_from_ics_batch(self, tmp_path):
        try:
            calendar_id = self.client.create_calendar("Batch ICS Calendar")
        except ValueError:
            calendar_id = self.client.get_calendar_id_by_name("Batch ICS Calendar")

        # Create ICS file with multiple events
        cal = Calendar()
        for i in range(10):
            event = Event()
            event.add("summary", f"Batch Event {i}")
            event.add("dtstart", datetime(2025, 2, 1, 10 + i, 0, 0))
            event.add("dtend", datetime(2025, 2, 1, 11 + i, 0, 0))
            cal.add_component(event)
        ics_path = tmp_path / "batch_test.ics"
        ics_path.write_bytes(cal.to_ical())

        self.client.add_events_from_ics_batch(calendar_id, str(ics_path))

        events = self.client.list_events(calendar_id)
        for i in range(10):
            assert any(
                e.get("summary") == f"Batch Event {i}"
                and e.get("start", {})
                .get("dateTime", "")
                .startswith(f"2025-02-01T{10 + i:02d}:00:00")
                and e.get("end", {})
                .get("dateTime", "")
                .startswith(f"2025-02-01T{11 + i:02d}:00:00")
                for e in events
            )
        self.client.delete_calendar(calendar_id)

    def test_add_date_only_events_from_ics_batch(self, tmp_path):
        try:
            calendar_id = self.client.create_calendar("Date Only ICS Calendar")
        except ValueError:
            calendar_id = self.client.get_calendar_id_by_name("Date Only ICS Calendar")

        cal = Calendar()
        for i in range(3):
            event = Event()
            event.add("summary", f"Date Event {i}")
            event.add("dtstart", datetime(2025, 3, 1 + i).date())
            event.add("dtend", datetime(2025, 3, 2 + i).date())
            cal.add_component(event)
        ics_path = tmp_path / "date_only_test.ics"
        ics_path.write_bytes(cal.to_ical())

        self.client.add_events_from_ics_batch(calendar_id, str(ics_path))

        events = self.client.list_events(calendar_id)
        for i in range(3):
            assert any(
                e.get("summary") == f"Date Event {i}"
                and e.get("start", {}).get("date", "") == f"2025-03-{1 + i:02d}"
                and e.get("end", {}).get("date", "") == f"2025-03-{2 + i:02d}"
                for e in events
            )
        self.client.delete_calendar(calendar_id)

    def test_add_events_from_ics_batch_with_description_and_location(self, tmp_path):
        try:
            calendar_id = self.client.create_calendar("DescLoc ICS Calendar")
        except ValueError:
            calendar_id = self.client.get_calendar_id_by_name("DescLoc ICS Calendar")

        cal = Calendar()
        event = Event()
        event.add("summary", "Event with Desc and Loc")
        event.add("dtstart", datetime(2025, 4, 1, 9, 0, 0))
        event.add("dtend", datetime(2025, 4, 1, 10, 0, 0))
        event.add("description", "This is a test description.")
        event.add("location", "Test Location")
        cal.add_component(event)
        ics_path = tmp_path / "desc_loc_test.ics"
        ics_path.write_bytes(cal.to_ical())

        self.client.add_events_from_ics_batch(calendar_id, str(ics_path))

        events = self.client.list_events(calendar_id)
        assert any(
            e.get("summary") == "Event with Desc and Loc"
            and e.get("description") == "This is a test description."
            and e.get("location") == "Test Location"
            for e in events
        )
        self.client.delete_calendar(calendar_id)


if __name__ == "__main__":
    pytest.main(["-vvv", __file__, "-s", "-k", "test_add_"])
