import logging
import os
import random
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
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

    def add_events_from_ics_batch(self, calendar_id: str, ics_path: str):
        def callback(request_id, response, exception):
            """Callback function to handle batch request responses"""
            if exception:
                self.logger.debug(f"Request {request_id} failed: {exception}")
            else:
                self.logger.debug(
                    f"Event created successfully: {response.get('id', 'Unknown ID')}"
                )

        with open(ics_path) as f:
            cal = Calendar.from_ical(f.read())

        events_to_create = []

        # Extract events from ICS
        for component in cal.walk():
            if component.name == "VEVENT":
                start_dt = component.get("dtstart").dt
                end_dt = component.get("dtend").dt

                if hasattr(start_dt, "hour"):
                    # Datetime event
                    event = {
                        "summary": str(component.get("summary", "No Title")),
                        "start": {
                            "dateTime": start_dt.isoformat(),
                            "timeZone": "UTC",
                        },
                        "end": {
                            "dateTime": end_dt.isoformat(),
                            "timeZone": "UTC",
                        },
                    }
                else:
                    # Date-only event
                    event = {
                        "summary": str(component.get("summary", "No Title")),
                        "start": {
                            "date": start_dt.strftime("%Y-%m-%d"),
                        },
                        "end": {
                            "date": end_dt.strftime("%Y-%m-%d"),
                        },
                    }

                if component.get("description"):
                    event["description"] = str(component.get("description"))
                if component.get("location"):
                    event["location"] = str(component.get("location"))

                events_to_create.append(event)

        # Process events in batches (API limit)
        batch_size = 500
        total_events = len(events_to_create)

        for i in range(0, total_events, batch_size):
            batch_events = events_to_create[i : i + batch_size]
            batch = self.service.new_batch_http_request(callback=callback)

            for idx, event in enumerate(batch_events):
                request_id = f"event_{i + idx}"
                batch.add(
                    self.service.events().insert(calendarId=calendar_id, body=event),
                    request_id=request_id,
                )

            self.logger.debug(
                f"Executing batch {i // batch_size + 1} with {len(batch_events)} events ..."  # noqa E501
            )

            max_retries = 3
            backoff = 30  # seconds
            for attempt in range(max_retries):
                try:
                    batch.execute()
                    self.logger.debug(f"Batch {i // batch_size + 1} completed")
                    break
                except HttpError as e:
                    status = e.resp.status
                    if status in [403, 429]:
                        self.logger.warning(
                            f"Batch execution hit usage limits (HTTP {status}), retrying in {backoff}s (attempt {attempt + 1}/{max_retries})"  # noqa E501
                        )
                        time.sleep(backoff + random.uniform(0, 0.5 * backoff))
                        backoff *= 2
                    else:
                        self.logger.error(f"Batch execution failed: {e}")
                        break
                except Exception as e:
                    self.logger.error(f"Batch execution failed: {e}")
                    break
            else:
                self.logger.error(
                    f"Batch execution failed after {max_retries} retries due to usage limits."  # noqa E501
                )

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
            self.logger.debug(f"Found {len(events)} events in calendar {calendar_id}")
            return events
        except Exception as e:
            self.logger.error(f"Failed to list events for calendar {calendar_id}: {e}")
            raise

    def make_calendar_public(self, calendar_id: str):
        """Make the calendar public by adding a 'reader' ACL for 'default' scope."""
        rule = {"scope": {"type": "default"}, "role": "reader"}
        try:
            self.service.acl().insert(calendarId=calendar_id, body=rule).execute()
            self.logger.info(f"Calendar {calendar_id} is now public.")
        except Exception as e:
            self.logger.error(f"Failed to make calendar public: {e}")
            raise

    def get_public_ics_url(self, calendar_id: str) -> str:
        """Return the public ICS URL for the calendar."""
        return (
            f"https://calendar.google.com/calendar/ical/{calendar_id}/public/basic.ics"
        )
