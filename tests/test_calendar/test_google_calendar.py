from datetime import datetime

import pytest
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
        self.client.add_events_from_ics(calendar_id, str(ics_path))

        events = self.client.list_events(calendar_id)
        assert any(
            e.get("summary") == "Test Event"
            and e.get("start", {}).get("dateTime", "").startswith("2025-01-01T12:00:00")
            and e.get("end", {}).get("dateTime", "").startswith("2025-01-01T13:00:00")
            for e in events
        )
        self.client.delete_calendar(calendar_id)


if __name__ == "__main__":
    pytest.main(["-vvv", __file__, "-s"])
