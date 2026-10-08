import logging
import os
import random
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from icalendar import Calendar, Event

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
        service_http = getattr(self.service, "_http", None)
        if service_http is not None:
            service_http.timeout = self.config.request_timeout_seconds

    @staticmethod
    def _event_from_ics_component(component: Event) -> dict:
        """Convert an ICS event component to a Google Calendar event body."""
        start_dt = component.get("dtstart").dt
        end_dt = component.get("dtend").dt

        if hasattr(start_dt, "hour"):
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
            event = {
                "summary": str(component.get("summary", "No Title")),
                "start": {"date": start_dt.strftime("%Y-%m-%d")},
                "end": {"date": end_dt.strftime("%Y-%m-%d")},
            }

        uid = component.get("uid")
        if uid:
            event["iCalUID"] = str(uid)
        if component.get("description"):
            event["description"] = str(component.get("description"))
        if component.get("location"):
            event["location"] = str(component.get("location"))
        return event

    @staticmethod
    def _http_status(error: Exception | None) -> int | None:
        response = getattr(error, "resp", None)
        status = getattr(response, "status", None)
        return status if isinstance(status, int) else None

    TRANSIENT_STATUSES = frozenset({403, 429, 500, 502, 503, 504})

    @staticmethod
    def _error_reason(error: Exception) -> str:
        details = getattr(error, "error_details", None) or []
        return str(details[0].get("reason", "")) if details else ""

    @staticmethod
    def _is_transient(error: Exception) -> bool:
        if isinstance(error, OSError):
            return True
        return (
            GoogleCalendarClient._http_status(error)
            in GoogleCalendarClient.TRANSIENT_STATUSES
        )

    @staticmethod
    def _should_retry(error: Exception, attempt: int, max_retries: int) -> bool:
        return attempt < max_retries - 1 and GoogleCalendarClient._is_transient(error)

    def add_events_from_ics_batch(self, calendar_id: str, ics_path: str) -> None:
        with open(ics_path) as f:
            cal = Calendar.from_ical(f.read())

        events_to_create = [
            self._event_from_ics_component(component)
            for component in cal.walk()
            if component.name == "VEVENT"
        ]

        batch_size = 100
        total_events = len(events_to_create)
        max_retries = 5

        for i in range(0, total_events, batch_size):
            batch_events = events_to_create[i : i + batch_size]
            failed_requests: dict[str, Exception] = {}

            def callback(
                request_id,
                response,
                exception,
                failures=failed_requests,
            ):
                if exception is None:
                    event_id = response.get("id", "Unknown ID")
                    self.logger.debug(f"Event imported successfully: {event_id}")
                else:
                    failures[request_id] = exception
                    self.logger.debug(f"Request {request_id} failed: {exception}")

            batch = self.service.new_batch_http_request(callback=callback)
            for idx, event in enumerate(batch_events):
                batch.add(
                    self.service.events().import_(calendarId=calendar_id, body=event),
                    request_id=f"event_{i + idx}",
                )

            self.logger.debug(
                "Executing batch %s with %s events ...",
                i // batch_size + 1,
                len(batch_events),
            )
            backoff = 20
            for attempt in range(max_retries):
                failed_requests.clear()
                try:
                    batch.execute()
                except (HttpError, OSError) as error:
                    if not self._should_retry(error, attempt, max_retries):
                        raise
                else:
                    if not failed_requests:
                        break
                    retryable = all(
                        self._is_transient(error) for error in failed_requests.values()
                    )
                    if not retryable or attempt == max_retries - 1:
                        first_error = next(iter(failed_requests.values()))
                        raise RuntimeError(
                            "Google Calendar event insertion failed: "
                            f"HTTP {self._http_status(first_error) or 'unknown'} "
                            f"{self._error_reason(first_error)} "
                            f"for {len(failed_requests)} of {total_events} events"
                        )
                if attempt < max_retries - 1:
                    time.sleep(backoff + random.uniform(0, 0.5 * backoff))
                    backoff *= 2

    def delete_events_batch(self, calendar_id: str, event_ids: list[str]) -> None:
        """Delete a bounded list of events, failing visibly on API errors."""
        batch_size = 500
        for start in range(0, len(event_ids), batch_size):
            failed_requests: dict[str, Exception] = {}

            def callback(request_id, response, exception, failures=failed_requests):
                if exception is not None and self._http_status(exception) != 404:
                    failures[request_id] = exception
                    self.logger.debug(f"Request {request_id} failed: {exception}")

            batch = self.service.new_batch_http_request(callback=callback)
            for index, event_id in enumerate(event_ids[start : start + batch_size]):
                batch.add(
                    self.service.events().delete(
                        calendarId=calendar_id,
                        eventId=event_id,
                    ),
                    request_id=f"delete_{start + index}",
                )
            batch.execute()
            if failed_requests:
                first_error = next(iter(failed_requests.values()))
                raise RuntimeError(
                    "Google Calendar deletion failed: "
                    f"HTTP {self._http_status(first_error) or 'unknown'} "
                    f"{self._error_reason(first_error)} "
                    f"for {len(failed_requests)} of {len(event_ids)} events"
                )

    def list_events(
        self,
        calendar_id: str,
        time_min: str | None = None,
        time_max: str | None = None,
    ) -> list[dict]:
        """List all events in a calendar, following every API page."""
        events: list[dict] = []
        request: dict[str, str | bool] = {
            "calendarId": calendar_id,
            "singleEvents": True,
            "showDeleted": False,
        }
        if time_min is not None:
            request["timeMin"] = time_min
        if time_max is not None:
            request["timeMax"] = time_max

        try:
            while True:
                events_result = self.service.events().list(**request).execute()
                events.extend(events_result.get("items", []))
                page_token = events_result.get("nextPageToken")
                if not page_token:
                    break
                request["pageToken"] = page_token

            self.logger.debug(f"Found {len(events)} events in calendar {calendar_id}")
            return events
        except Exception as e:
            self.logger.error(f"Failed to list events for calendar {calendar_id}: {e}")
            raise
