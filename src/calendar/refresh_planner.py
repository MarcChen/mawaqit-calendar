from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date


class RefreshSafetyError(RuntimeError):
    """Raised when a refresh plan is unsafe to execute."""


@dataclass(frozen=True, slots=True)
class RefreshWindow:
    """The inclusive-start, exclusive-end date range to replace."""

    start: date
    end: date


@dataclass(frozen=True, slots=True)
class RefreshPlan:
    """The remote event IDs to remove and local event UIDs to insert."""

    window: RefreshWindow
    delete_event_ids: tuple[str, ...]
    desired_uids: tuple[str, ...]
    existing_count: int
    desired_count: int


def source_year_window(source_year: int) -> RefreshWindow:
    """Return the full calendar year covered by the source data."""
    return RefreshWindow(start=date(source_year, 1, 1), end=date(source_year + 1, 1, 1))


def _event_date(event: Mapping[str, str]) -> date | None:
    start = event.get("start", {})
    if not hasattr(start, "get"):
        return None

    value = start.get("dateTime") or start.get("date")
    if not value:
        return None

    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def plan_window_replacement(
    existing_events: Sequence[Mapping[str, str]],
    desired_events: Sequence[Mapping[str, str]],
    window: RefreshWindow,
    min_desired_events: int = 100,
) -> RefreshPlan:
    """Plan a safe full replacement of one calendar date window."""
    if len(desired_events) < min_desired_events:
        raise RefreshSafetyError(
            f"Refusing a refresh with {len(desired_events)} events; "
            f"expected at least {min_desired_events}."
        )

    desired_uids = tuple(event.get("uid", "") for event in desired_events)
    if any(not uid for uid in desired_uids):
        raise RefreshSafetyError("Every desired event must have a UID.")
    if len(set(desired_uids)) != len(desired_uids):
        raise RefreshSafetyError("Desired event UIDs must be unique.")

    desired_uid_set = set(desired_uids)
    delete_event_ids: list[str] = []
    for event in existing_events:
        event_id = event.get("id")
        if not event_id:
            continue
        event_date = _event_date(event)
        if event_date is not None and not (window.start <= event_date < window.end):
            continue
        if event.get("iCalUID") in desired_uid_set:
            continue
        delete_event_ids.append(event_id)

    return RefreshPlan(
        window=window,
        delete_event_ids=tuple(delete_event_ids),
        desired_uids=desired_uids,
        existing_count=len(existing_events),
        desired_count=len(desired_events),
    )
