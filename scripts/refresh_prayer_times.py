# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "beautifulsoup4",
#   "google-api-python-client",
#   "google-auth-httplib2",
#   "google-auth-oauthlib",
#   "icalendar>=6.3.1",
#   "pydantic",
# ]
# ///
# How to run: uv run python -m scripts.refresh_prayer_times --all --no-remote

import argparse
import json
import sys
from pathlib import Path

from src.calendar.refresh_service import (
    DEFAULT_PLAN_PATH,
    DEFAULT_REGISTRY_PATH,
    DEFAULT_SLUG,
    build_all_refresh_plans,
    build_refresh_plan,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the annual full-year Google Calendar refresh plan."
    )
    parser.add_argument("--slug", default=DEFAULT_SLUG)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process every slug in the active registry.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicitly request the default read-only behavior.",
    )
    parser.add_argument(
        "--no-remote",
        action="store_true",
        help="Build the local plan without querying Google Calendar.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Replace the planned window; requires the exact confirmation token.",
    )
    parser.add_argument(
        "--confirm-token",
        default="",
        help="Required with --execute; use REFRESH-<slug> or REFRESH-ALL.",
    )
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN_PATH)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.execute and args.dry_run:
        print("Choose either --execute or --dry-run, not both.", file=sys.stderr)
        return 2
    if args.execute and args.no_remote:
        print("--execute cannot be combined with --no-remote.", file=sys.stderr)
        return 2

    if args.all:
        output = build_all_refresh_plans(
            registry_path=args.registry,
            plan_path=args.plan,
            use_remote=not args.no_remote,
            execute=args.execute,
            confirmation_token=args.confirm_token,
        )
    else:
        output = build_refresh_plan(
            slug=args.slug,
            registry_path=args.registry,
            plan_path=args.plan,
            use_remote=not args.no_remote,
            execute=args.execute,
            confirmation_token=args.confirm_token,
        )
    print(json.dumps(output, indent=2))
    if args.execute:
        print("Live refresh completed.")
    else:
        print("Dry run only; no Google Calendar events were changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
