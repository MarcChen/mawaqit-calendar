import json
from datetime import UTC, date, datetime, time
from pathlib import Path
from urllib.parse import unquote, urlparse

from icalendar import Calendar, Event

from src.calendar.google_calendar import GoogleCalendarClient
from src.calendar.ics_generator import generate_prayer_calendar
from src.calendar.refresh_planner import (
    RefreshWindow,
    plan_window_replacement,
    source_year_window,
)
from src.config.settings import CALENDAR_DIR
from src.models.google_calendar_config import GoogleCalendarConfig
from src.scrapers.mawaqit_scraper import MawaqitScraper

DEFAULT_SLUG = "annour-ivry-sur-seine"
DEFAULT_REGISTRY_PATH = Path("registry/mosque_calendars.json")
DEFAULT_PLAN_PATH = Path("data/refresh_plan.json")


def calendar_id_from_public_ics_url(url: str) -> str | None:
    """Extract a Google Calendar ID from a public ICS URL."""
    path_parts = urlparse(url).path.strip("/").split("/")
    if len(path_parts) < 3 or path_parts[-2:] != ["public", "basic.ics"]:
        return None
    calendar_id = unquote(path_parts[-3])
    return calendar_id or None


def _load_registry_entry(path: Path, slug: str) -> dict[str, str]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    metadata = registry.get(slug)
    if not isinstance(metadata, dict):
        raise ValueError(f"Mosque is not registered: {slug}")

    calendar_url = metadata.get("calendarUrl")
    if not isinstance(calendar_url, str):
        raise ValueError(f"Mosque has no public calendar URL: {slug}")
    mosque_url = metadata.get("url")
    if not isinstance(mosque_url, str) or urlparse(mosque_url).netloc != "mawaqit.net":
        raise ValueError(f"Mosque has an unsupported Mawaqit URL: {slug}")

    parsed_url = urlparse(calendar_url)
    if parsed_url.netloc != "calendar.google.com":
        raise ValueError(f"Unsupported calendar URL for {slug}: {parsed_url.netloc}")

    if not calendar_id_from_public_ics_url(calendar_url):
        raise ValueError(f"Could not parse the calendar ID for {slug}")
    return metadata


def _registry_slugs(path: Path) -> list[str]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(registry, dict):
        raise ValueError(f"Registry must contain an object: {path}")
    return [str(slug) for slug in registry]


def _plan_path_for_slug(base_path: Path, slug: str) -> Path:
    return base_path.with_name(f"{base_path.stem}_{slug}{base_path.suffix}")


def _component_date(component: Event) -> date:
    start = component.get("dtstart").dt
    return start.date() if isinstance(start, datetime) else start


def _write_window_calendar(
    calendar: Calendar,
    window: RefreshWindow,
    path: Path,
) -> None:
    window_calendar = Calendar()
    for component in calendar.walk():
        if component.name != "VEVENT":
            continue
        if window.start <= _component_date(component) < window.end:
            window_calendar.add_component(component)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(window_calendar.to_ical())


def _events_in_window(
    calendar: Calendar, window: RefreshWindow
) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    for component in calendar.walk():
        if component.name != "VEVENT":
            continue
        if not window.start <= _component_date(component) < window.end:
            continue
        uid = component.get("uid")
        if uid:
            events.append({"uid": str(uid)})
    return events


def _window_bounds(window: RefreshWindow) -> tuple[str, str]:
    start = datetime.combine(window.start, time.min, tzinfo=UTC)
    end = datetime.combine(window.end, time.min, tzinfo=UTC)
    return start.isoformat().replace("+00:00", "Z"), end.isoformat().replace(
        "+00:00", "Z"
    )


def build_refresh_plan(
    *,
    slug: str,
    registry_path: Path,
    plan_path: Path,
    use_remote: bool = True,
    execute: bool = False,
    confirmation_token: str = "",
) -> dict[str, str | int | list[str]]:
    if execute and not use_remote:
        raise ValueError("Live refresh requires remote event inspection.")
    expected_token = f"REFRESH-{slug}"
    if execute and confirmation_token != expected_token:
        raise PermissionError(f"Expected confirmation token: {expected_token}")

    metadata = _load_registry_entry(registry_path, slug)
    calendar_id = calendar_id_from_public_ics_url(metadata["calendarUrl"])
    if not calendar_id:
        raise ValueError(f"Could not parse the calendar ID for {slug}")

    with MawaqitScraper() as scraper:
        mosque = scraper.scrape(metadata["url"])
    if mosque is None or mosque.prayer_time is None:
        raise RuntimeError(f"Mawaqit returned no prayer times for {slug}")
    window = source_year_window(mosque.year)

    generator = generate_prayer_calendar(mosque)
    calendar = generator.generate_calendar()
    full_ics_path = Path(CALENDAR_DIR) / str(mosque.year) / f"{mosque.id}.ics"
    generator.save_calendar()
    window_ics_path = full_ics_path.with_name(f"{mosque.id}_window.ics")
    _write_window_calendar(calendar, window, window_ics_path)
    desired_events = _events_in_window(calendar, window)

    client: GoogleCalendarClient | None = None
    existing_events: list[dict] = []
    if use_remote:
        client = GoogleCalendarClient(GoogleCalendarConfig())
        time_min, time_max = _window_bounds(window)
        existing_events = client.list_events(
            calendar_id,
            time_min=time_min,
            time_max=time_max,
        )
    refresh_plan = plan_window_replacement(
        existing_events=existing_events,
        desired_events=desired_events,
        window=window,
    )

    plan_data: dict[str, str | int | list[str]] = {
        "slug": slug,
        "calendar_id": calendar_id,
        "window_start": window.start.isoformat(),
        "window_end": window.end.isoformat(),
        "existing_count": refresh_plan.existing_count,
        "desired_count": refresh_plan.desired_count,
        "delete_event_ids": list(refresh_plan.delete_event_ids),
        "desired_uids": list(refresh_plan.desired_uids),
        "window_ics_path": str(window_ics_path),
    }
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan_data, indent=2) + "\n", encoding="utf-8")

    if execute:
        if client is None:
            raise RuntimeError("Remote client is required for live refresh.")
        client.delete_events_batch(calendar_id, list(refresh_plan.delete_event_ids))
        client.add_events_from_ics_batch(calendar_id, str(window_ics_path))
    return plan_data


def build_all_refresh_plans(
    *,
    registry_path: Path,
    plan_path: Path,
    use_remote: bool,
    execute: bool,
    confirmation_token: str,
) -> list[dict[str, str | int | list[str]]]:
    if execute and confirmation_token != "REFRESH-ALL":
        raise PermissionError("Expected confirmation token: REFRESH-ALL")

    slugs = _registry_slugs(registry_path)
    if not slugs:
        raise ValueError("The active registry contains no mosques.")

    return [
        build_refresh_plan(
            slug=slug,
            registry_path=registry_path,
            plan_path=_plan_path_for_slug(plan_path, slug),
            use_remote=use_remote,
            execute=execute,
            confirmation_token=f"REFRESH-{slug}" if execute else "",
        )
        for slug in slugs
    ]
