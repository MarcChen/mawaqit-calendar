from datetime import date

import pytest

from src.calendar.refresh_planner import (
    RefreshSafetyError,
    RefreshWindow,
    plan_window_replacement,
    source_year_window,
)


def test_plan_window_replacement_keeps_only_desired_window_events():
    window = source_year_window(2026)
    existing_events = [
        {"id": "event-before", "start": {"dateTime": "2025-12-31T12:00:00Z"}},
        {"id": "event-inside", "iCalUID": "old-event"},
    ]
    desired_events = [
        {"uid": f"mosque-20260101-{index}@mawaqit-calendar"} for index in range(100)
    ]

    plan = plan_window_replacement(
        existing_events=existing_events,
        desired_events=desired_events,
        window=window,
        min_desired_events=100,
    )

    assert plan.delete_event_ids == ("event-inside",)
    assert plan.desired_uids == tuple(event["uid"] for event in desired_events)
    assert plan.existing_count == 2
    assert plan.desired_count == 100


def test_plan_window_replacement_deletes_only_stale_events():
    window = source_year_window(2026)
    existing_events = [
        {
            "id": "stale",
            "iCalUID": "annour_ivry_sur_seine-20251231-isha@mawaqit-calendar",
            "start": {"dateTime": "2026-02-01T06:00:00Z"},
        },
        {
            "id": "upserted",
            "iCalUID": "annour_ivry_sur_seine-20260101-fajr@mawaqit-calendar",
            "start": {"dateTime": "2026-01-01T06:00:00Z"},
        },
        {
            "id": "outside",
            "iCalUID": "other",
            "start": {"dateTime": "2027-02-01T06:00:00Z"},
        },
    ]
    desired_events = [{"uid": "annour_ivry_sur_seine-20260101-fajr@mawaqit-calendar"}]
    desired_events += [{"uid": f"uid-{index}"} for index in range(99)]

    plan = plan_window_replacement(
        existing_events=existing_events,
        desired_events=desired_events,
        window=window,
    )

    assert plan.delete_event_ids == ("stale",)


def test_plan_window_replacement_rejects_duplicate_desired_uids():
    window = source_year_window(2026)
    desired_events = [{"uid": "duplicate"} for _ in range(100)]

    with pytest.raises(RefreshSafetyError, match="unique"):
        plan_window_replacement(
            existing_events=[],
            desired_events=desired_events,
            window=window,
        )


def test_plan_window_replacement_rejects_a_suspiciously_small_refresh():
    window = source_year_window(2026)

    with pytest.raises(RefreshSafetyError):
        plan_window_replacement(
            existing_events=[],
            desired_events=[{"uid": "only-one-event"}],
            window=window,
            min_desired_events=100,
        )


def test_source_year_window_covers_the_whole_source_year():
    assert source_year_window(2026) == RefreshWindow(
        start=date(2026, 1, 1),
        end=date(2027, 1, 1),
    )
