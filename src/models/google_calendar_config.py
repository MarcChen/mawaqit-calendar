from pathlib import Path

from pydantic import BaseModel


class GoogleCalendarConfig(BaseModel):
    credentials_path: str = str(Path(__file__).parent.parent / "credentials.json")
    token_path: str = str(Path(__file__).parent.parent / "token.json")
    scopes: list[str] = ["https://www.googleapis.com/auth/calendar"]
    blacklisted_ids: list[str] = [
        "kemar987415@gmail.com",
        "f124d4d19b778c4811837aaa9b9e6471a0639da794a611ec5792e6df6ec2d6bd@group.calendar.google.com",
    ]
