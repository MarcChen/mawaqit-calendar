from pathlib import Path

from pydantic import BaseModel

CALENDAR_READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
CALENDAR_EVENTS_SCOPE = "https://www.googleapis.com/auth/calendar.events"


class GoogleCalendarConfig(BaseModel):
    credentials_path: str = str(Path(__file__).parents[2] / "credentials.json")
    token_path: str = str(Path(__file__).parents[2] / "token.json")
    request_timeout_seconds: int = 120
    scopes: list[str] = [CALENDAR_READONLY_SCOPE, CALENDAR_EVENTS_SCOPE]
