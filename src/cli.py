"""Personal Mawaqit Calendar CLI - Sync mosque prayer times to your Google Calendar.

This CLI replaces the old website/scraping-all approach with a personal,
monthly-sync model where users connect their own Google Calendar to a
specific mosque.
"""

from __future__ import annotations

import asyncio
import json
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated

import typer
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.calendar.ics_generator import generate_prayer_calendar
from src.config.settings import PROCESSED_DATA_DIR
from src.models.mosque import Mosque
from src.scrapers.mawaqit_scraper import MawaqitScraper

console = Console()
app = typer.Typer(
    name="mawaqit-calendar",
    help="Sync mosque prayer times to your personal Google Calendar",
    no_args_is_help=True,
)

# Google Calendar API scopes
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_google_credentials() -> Credentials | None:
    """Get or refresh Google OAuth credentials."""
    creds = None
    token_path = Path.home() / ".mawaqit-calendar" / "token.json"
    token_path.parent.mkdir(parents=True, exist_ok=True)

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            return None

    return creds


def authenticate_google() -> Credentials:
    """Authenticate with Google and return credentials."""
    creds = get_google_credentials()
    if creds:
        return creds

    # Check for credentials.json
    creds_path = Path.home() / ".mawaqit-calendar" / "credentials.json"
    if not creds_path.exists():
        console.print(Panel(
            "[red]Google Calendar credentials not found![/red]\n\n"
            "1. Go to https://console.cloud.google.com/apis/credentials\n"
            "2. Create OAuth 2.0 credentials and download as credentials.json\n"
            "3. Place it at: ~/.mawaqit-calendar/credentials.json\n\n"
            "Then run this command again.",
            title="Setup Required"
        ))
        raise typer.Exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
    creds = flow.run_local_server(port=0)

    # Save token for future runs
    token_path = Path.home() / ".mawaqit-calendar" / "token.json"
    with open(token_path, "w") as token:
        token.write(creds.to_json())

    return creds


def list_calendars(service) -> list[dict]:
    """List user's Google Calendars."""
    calendars = []
    page_token = None

    while True:
        response = service.calendarList().list(pageToken=page_token).execute()
        calendars.extend(response.get("items", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return calendars


def select_calendar(calendars: list[dict]) -> dict:
    """Interactive calendar selection."""
    if not calendars:
        console.print("[red]No calendars found in your Google account.[/red]")
        raise typer.Exit(1)

    table = Table(title="Your Google Calendars")
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Name", style="green")
    table.add_column("ID", style="dim")

    for idx, cal in enumerate(calendars, 1):
        name = cal.get("summary", "Unnamed")
        cal_id = cal.get("id", "unknown")
        table.add_row(str(idx), name, cal_id[:40] + "..." if len(cal_id) > 40 else cal_id)

    console.print(table)

    while True:
        choice = console.input("\nSelect calendar number (or 0 to create new): ")
        try:
            idx = int(choice)
            if idx == 0:
                return create_new_calendar(service)
            if 1 <= idx <= len(calendars):
                return calendars[idx - 1]
            console.print("[red]Invalid selection. Try again.[/red]")
        except ValueError:
            console.print("[red]Please enter a number.[/red]")


def create_new_calendar(service) -> dict:
    """Create a new calendar for prayer times."""
    name = console.input("Enter new calendar name [Prayer Times]: ") or "Prayer Times"

    calendar = {
        "summary": name,
        "description": "Islamic prayer times from Mawaqit",
        "timeZone": "Europe/Paris",
    }

    created = service.calendars().insert(body=calendar).execute()
    console.print(f"[green]Created calendar: {created['summary']}[/green]")
    return created


class ConfigManager:
    """Manage user configuration with Pydantic-style validation."""

    CONFIG_PATH = Path.home() / ".mawaqit-calendar" / "config.json"

    def __init__(self):
        self.config = self._load()

    def _load(self) -> dict:
        """Load config from disk."""
        if self.CONFIG_PATH.exists():
            with open(self.CONFIG_PATH, "r") as f:
                return json.load(f)
        return {}

    def save(self):
        """Save config to disk."""
        self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.CONFIG_PATH, "w") as f:
            json.dump(self.config, f, indent=2)

    def get_mosque_url(self) -> str | None:
        return self.config.get("mosque_url")

    def set_mosque_url(self, url: str):
        self.config["mosque_url"] = url
        self.save()

    def get_calendar_id(self) -> str | None:
        return self.config.get("calendar_id")

    def set_calendar_id(self, cal_id: str):
        self.config["calendar_id"] = cal_id
        self.save()

    def get_last_sync(self) -> str | None:
        return self.config.get("last_sync")

    def set_last_sync(self, date: str):
        self.config["last_sync"] = date
        self.save()


def find_existing_prayer_event(service, calendar_id: str, year: int, month: int, day: int, prayer_name: str) -> dict | None:
    """Find an existing prayer event for a specific date and prayer.
    
    Returns the event dict if found, None otherwise.
    """
    # Search for events on this specific day with this prayer name
    start_of_day = datetime(year, month, day, 0, 0).isoformat() + "Z"
    end_of_day = datetime(year, month, day, 23, 59).isoformat() + "Z"
    
    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=start_of_day,
            timeMax=end_of_day,
            q=f"🕌 {prayer_name.title()}",
        )
        .execute()
    )
    
    events = events_result.get("items", [])
    for event in events:
        if f"🕌 {prayer_name.title()}" in event.get("summary", ""):
            return event
    
    return None


def sync_prayer_times(
    service,
    calendar_id: str,
    mosque: Mosque,
    year: int,
    month: int,
) -> tuple[int, int, int]:
    """Sync prayer times for a specific month to Google Calendar.
    
    Returns:
        Tuple of (events_created, events_updated, events_unchanged)
    """
    timezone = mosque.metadata.timezone if mosque.metadata else "Europe/Paris"

    events_created = 0
    events_updated = 0
    events_unchanged = 0

    # Get days in month
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)

    days_in_month = (next_month - datetime(year, month, 1)).days

    for day in range(1, days_in_month + 1):
        try:
            daily_prayers = mosque.prayer_time.get_prayer_time(month, day)
            if not daily_prayers:
                continue

            prayers = daily_prayers.to_dict()
            date_obj = datetime(year, month, day).date()

            for prayer_name, prayer_time_str in prayers.items():
                if prayer_name.lower() == "sunrise":
                    continue  # Skip sunrise

                try:
                    # Parse time
                    hour, minute = map(int, prayer_time_str.split(":"))
                    start_time = datetime(year, month, day, hour, minute)

                    # Check if this prayer already exists
                    existing_event = find_existing_prayer_event(
                        service, calendar_id, year, month, day, prayer_name
                    )

                    # Create new event data
                    new_event = {
                        "summary": f"🕌 {prayer_name.title()}",
                        "description": f"{prayer_name.title()} prayer at {mosque.name}",
                        "start": {
                            "dateTime": start_time.isoformat(),
                            "timeZone": timezone,
                        },
                        "end": {
                            "dateTime": (start_time + timedelta(minutes=30)).isoformat(),
                            "timeZone": timezone,
                        },
                        "reminders": {
                            "useDefault": False,
                            "overrides": [
                                {"method": "popup", "minutes": 15},
                            ],
                        },
                    }

                    if existing_event:
                        # Check if the time has changed
                        existing_start = existing_event.get("start", {}).get("dateTime")
                        new_start = new_event["start"]["dateTime"]
                        
                        if existing_start == new_start:
                            # Time hasn't changed, skip
                            events_unchanged += 1
                        else:
                            # Delete old event and recreate
                            service.events().delete(
                                calendarId=calendar_id, 
                                eventId=existing_event["id"]
                            ).execute()
                            service.events().insert(
                                calendarId=calendar_id, 
                                body=new_event
                            ).execute()
                            events_updated += 1
                    else:
                        # No existing event, create new
                        service.events().insert(
                            calendarId=calendar_id, 
                            body=new_event
                        ).execute()
                        events_created += 1

                except Exception as e:
                    console.print(f"[yellow]Warning: Could not add {prayer_name} on {date_obj}: {e}[/yellow]")

        except Exception as e:
            console.print(f"[yellow]Warning: Could not process day {day}: {e}[/yellow]")

    return events_created, events_updated, events_unchanged


@app.command()
def setup(
    mosque_url: Annotated[str, typer.Option("--mosque-url", "-m", help="Mawaqit mosque URL")] = None,
    calendar_id: Annotated[str, typer.Option("--calendar", "-c", help="Google Calendar ID")] = None,
):
    """Configure your mosque and calendar (one-time setup)."""
    config = ConfigManager()

    console.print(Panel(
        "[bold blue]Mawaqit Calendar Setup[/bold blue]\n\n"
        "This will connect your Google Calendar to a mosque.",
        title="Welcome"
    ))

    # Authenticate with Google
    console.print("\n[bold]Step 1: Google Calendar Authentication[/bold]")
    creds = authenticate_google()
    service = build("calendar", "v3", credentials=creds)
    console.print("[green]✓ Authenticated with Google Calendar[/green]")

    # Select or create calendar
    if not calendar_id:
        console.print("\n[bold]Step 2: Select Calendar[/bold]")
        calendars = list_calendars(service)
        selected = select_calendar(calendars)
        calendar_id = selected["id"]

    config.set_calendar_id(calendar_id)
    console.print(f"[green]✓ Calendar configured: {calendar_id}[/green]")

    # Configure mosque
    if not mosque_url:
        console.print("\n[bold]Step 3: Configure Mosque[/bold]")
        console.print("Enter the Mawaqit URL for your mosque")
        console.print("Example: https://mawaqit.net/fr/m/grande-mosquee-de-paris")
        mosque_url = console.input("Mosque URL: ").strip()

    config.set_mosque_url(mosque_url)
    console.print(f"[green]✓ Mosque configured: {mosque_url}[/green]")

    console.print(Panel(
        "[bold green]Setup complete![/bold green]\n\n"
        "Run [bold]mawaqit-calendar sync[/bold] to sync prayer times.",
        title="Success"
    ))


@app.command()
def sync(
    month: Annotated[int, typer.Option("--month", "-m", help="Month to sync (1-12, default: next month)")] = None,
    year: Annotated[int, typer.Option("--year", "-y", help="Year to sync (default: current year)")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show what would be synced without making changes")] = False,
):
    """Sync prayer times for the upcoming month to your Google Calendar.

    This command scrapes prayer times from your configured mosque and
    adds them to your Google Calendar. Run this monthly to keep your
    calendar up to date.
    """
    config = ConfigManager()

    # Validate config
    mosque_url = config.get_mosque_url()
    calendar_id = config.get_calendar_id()

    if not mosque_url or not calendar_id:
        console.print(Panel(
            "[red]Not configured![/red]\n\n"
            "Please run [bold]mawaqit-calendar setup[/bold] first.",
            title="Error"
        ))
        raise typer.Exit(1)

    # Determine month/year to sync
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        # Default to next month
        if now.month == 12:
            month = 1
            year += 1
        else:
            month = now.month + 1

    console.print(Panel(
        f"[bold]Syncing prayer times for {datetime(year, month, 1).strftime('%B %Y')}[/bold]\n\n"
        f"Mosque: {mosque_url}\n"
        f"Calendar: {calendar_id}\n"
        f"Mode: {'[yellow]Dry Run[/yellow]' if dry_run else '[green]Live[/green]'}",
        title="Mawaqit Calendar Sync"
    ))

    # Scrape mosque data
    console.print("\n[bold]Scraping prayer times...[/bold]")
    with MawaqitScraper() as scraper:
        mosque = scraper.scrape(mosque_url)

    if not mosque:
        console.print("[red]Failed to scrape mosque data![/red]")
        raise typer.Exit(1)

    console.print(f"[green]✓ Scraped {mosque.name}[/green]")

    if dry_run:
        console.print("\n[yellow]Dry run - would sync:[/yellow]")
        # Show sample data
        sample = mosque.prayer_time.get_prayer_time(month, 1)
        if sample:
            console.print(f"Sample prayers for {datetime(year, month, 1).strftime('%B %d, %Y')}:")
            for name, time in sample.to_dict().items():
                console.print(f"  {name}: {time}")
        console.print("\n[bold]Run without --dry-run to sync.[/bold]")
        return

    # Authenticate and sync
    console.print("\n[bold]Authenticating with Google Calendar...[/bold]")
    creds = authenticate_google()
    service = build("calendar", "v3", credentials=creds)

    # Sync events (checks for existing, updates if changed)
    console.print(f"\n[bold]Syncing prayer times for {datetime(year, month, 1).strftime('%B %Y')}...[/bold]")
    created, updated, unchanged = sync_prayer_times(service, calendar_id, mosque, year, month)

    # Update config
    config.set_last_sync(datetime.now().isoformat())

    console.print(Panel(
        f"[bold green]Sync complete![/bold green]\n\n"
        f"Created: {created} new events\n"
        f"Updated: {updated} changed events\n"
        f"Unchanged: {unchanged} events\n\n"
        f"Your calendar is now up to date for {datetime(year, month, 1).strftime('%B %Y')}.",
        title="Success"
    ))


@app.command()
def status():
    """Show current configuration and sync status."""
    config = ConfigManager()

    mosque_url = config.get_mosque_url() or "[red]Not configured[/red]"
    calendar_id = config.get_calendar_id() or "[red]Not configured[/red]"
    last_sync = config.get_last_sync()

    if last_sync:
        last_sync_dt = datetime.fromisoformat(last_sync)
        last_sync_str = last_sync_dt.strftime("%Y-%m-%d %H:%M")
    else:
        last_sync_str = "[red]Never[/red]"

    table = Table(title="Mawaqit Calendar Status")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Mosque URL", str(mosque_url))
    table.add_row("Calendar ID", str(calendar_id)[:50] + "..." if len(str(calendar_id)) > 50 else str(calendar_id))
    table.add_row("Last Sync", last_sync_str)

    console.print(table)

    if not config.get_mosque_url() or not config.get_calendar_id():
        console.print("\n[yellow]Run [bold]mawaqit-calendar setup[/bold] to configure.[/yellow]")


@app.command()
def config_show():
    """Show configuration file location and contents."""
    config = ConfigManager()

    console.print(f"[bold]Config file:[/bold] {config.CONFIG_PATH}")
    console.print("\n[bold]Contents:[/bold]")
    console.print_json(json.dumps(config.config, indent=2))


if __name__ == "__main__":
    app()
