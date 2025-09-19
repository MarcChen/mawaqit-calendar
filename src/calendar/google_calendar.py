import logging
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from icalendar import Calendar

from src.models.google_calendar_config import GoogleCalendarConfig


class GoogleCalendarClient:
    def __init__(self, config: GoogleCalendarConfig):
        self.config = config
        self.creds = None
        self.service = None
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self._authenticate()

    def _authenticate(self):
        if os.path.exists(self.config.token_path):
            self.creds = Credentials.from_authorized_user_file(
                self.config.token_path, self.config.scopes
            )
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.credentials_path, self.config.scopes
                )
                self.creds = flow.run_local_server(port=0)
            with open(self.config.token_path, "w") as token:
                token.write(self.creds.to_json())
        self.service = build("calendar", "v3", credentials=self.creds)

    def create_calendar(self, name: str, timezone: str = "UTC") -> str:
        # Check if calendar already exists
        if self.get_calendar_id_by_name(name):
            self.logger.error(f"Calendar with name '{name}' already exists.")
            raise ValueError(f"Calendar with name '{name}' already exists.")
        calendar = {
            "summary": name,
            "timeZone": timezone,
        }
        created_calendar = self.service.calendars().insert(body=calendar).execute()
        self.logger.info(f"Created calendar '{name}' with ID: {created_calendar['id']}")
        return created_calendar["id"]

    def list_calendars(self) -> list[dict]:
        calendars = self.service.calendarList().list().execute()
        return calendars.get("items", [])

    def get_calendar_id_by_name(self, name: str) -> str | None:
        for cal in self.list_calendars():
            if cal.get("summary") == name:
                return cal.get("id")
        return None

    def add_events_from_ics(self, calendar_id: str, ics_path: str):
        with open(ics_path) as f:
            cal = Calendar.from_ical(f.read())
        for component in cal.walk():
            if component.name == "VEVENT":
                event = {
                    "summary": str(component.get("summary")),
                    "start": {
                        "dateTime": component.get("dtstart").dt.isoformat(),
                        "timeZone": "UTC",
                    },
                    "end": {
                        "dateTime": component.get("dtend").dt.isoformat(),
                        "timeZone": "UTC",
                    },
                }
                self.service.events().insert(
                    calendarId=calendar_id, body=event
                ).execute()

    def delete_calendar(self, calendar_id: str):
        if calendar_id in self.config.blacklisted_ids:
            self.logger.error(f"Cannot delete blacklisted calendar: {calendar_id}")
            raise ValueError(f"Cannot delete blacklisted calendar: {calendar_id}")
        try:
            self.service.calendars().delete(calendarId=calendar_id).execute()
            self.logger.info(f"Deleted calendar with ID: {calendar_id}")
        except Exception as e:
            self.logger.error(f"Failed to delete calendar {calendar_id}: {e}")
            raise

    def list_events(self, calendar_id: str) -> list[dict]:
        """List all events from a given calendar ID."""
        try:
            events_result = self.service.events().list(calendarId=calendar_id).execute()
            events = events_result.get("items", [])
            self.logger.info(f"Found {len(events)} events in calendar {calendar_id}")
            return events
        except Exception as e:
            self.logger.error(f"Failed to list events for calendar {calendar_id}: {e}")
            raise


if __name__ == "__main__":
    config = GoogleCalendarConfig(
        credentials_path="client_secret.json",
        token_path="token.json",
        scopes=["https://www.googleapis.com/auth/calendar"],
    )
    client = GoogleCalendarClient(config)
    # Example usage
    calendars = client.list_calendars()
    print("Calendars:")
    for cal in calendars:
        print(f"- {cal.get('summary')} (ID: {cal.get('id')})")
