# Mawaqit Calendar 🕌

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](VERSION)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

A Python-based project to scrape prayer times from [Mawaqit](https://mawaqit.net) and generate ICS calendar files for mosques. Subscribe to your mosque's prayer times directly in your favorite calendar app!

## 🚀 Current Features

### Prayer Time Scraping
- **Mawaqit Integration**: Scrapes prayer times directly from Mawaqit mosque pages given url
- **Data Validation**: Robust validation using Pydantic models
- **Multiple Mosque Support**: Process multiple mosques in batch
- **Error Handling**: Comprehensive error handling with retry logic

### Calendar Generation
- **ICS Format**: Generates standard ICS calendar files compatible with all major calendar applications
- **Customizable Events**: Configurable event templates and descriptions
- **Timezone Support**: Proper timezone handling for accurate prayer times
- **Individual Calendars**: One calendar file per mosque

### Data Models
- **Mosque Information**: Complete mosque metadata (location, contact, facilities)
- **Prayer Times**: Structured prayer time data with validation
- **Calendar Configuration**: Flexible calendar generation settings


## Subscribe to a calendar

The active mosque registry is [`registry/mosque_calendars.json`](registry/mosque_calendars.json). The current supported calendar is **Mosquée ANNOUR - Ivry-Sur-Seine**:

- [Google Calendar](https://calendar.google.com/calendar/ical/614e8a4cb293fcfc093f481be59e9c588a6d507a49d1b341413f16f62741c5a4%40group.calendar.google.com/public/basic.ics)
- [Apple Calendar / iCal](https://calendar.google.com/calendar/ical/614e8a4cb293fcfc093f481be59e9c588a6d507a49d1b341413f16f62741c5a4%40group.calendar.google.com/public/basic.ics)
- [Outlook](https://calendar.google.com/calendar/ical/614e8a4cb293fcfc093f481be59e9c588a6d507a49d1b341413f16f62741c5a4%40group.calendar.google.com/public/basic.ics)

To add another mosque, use the [mosque submission form](.github/ISSUE_TEMPLATE/mosque_submission.yml). A maintainer will validate the source and add it to the registry before the next refresh.

## Maintainer operations

The refresh workflow is the active calendar operation. It is read-only by default and requires an explicit confirmation token before changing Google Calendar state:

```bash
uv run python -m scripts.refresh_prayer_times --all --no-remote
uv run python -m scripts.refresh_prayer_times --all --no-remote \
  --execute --confirmation REFRESH-ALL
```

The refresh workflow runs once per year, on January 1. It is dry-run by default. To enable live scheduled writes, set the `ENABLE_CALENDAR_WRITES` repository variable to `true` and provide the `GOOGLE_TOKEN_JSON` repository secret. A maintainer can also run it manually with `execute=true` and confirmation `REFRESH-ALL`.

If Google returns `invalid_grant`, reauthorize locally:

```bash
uv run python -m scripts.reauthorize_google \
  --expected-calendar-id <ivry-calendar-id>
```

The command opens the OAuth consent flow, backs up the old token under `data/oauth-backups/`, and does not modify calendars. It requests only `auth/calendar.readonly` plus `auth/calendar.events` — event read/write, never calendar creation, deletion, sharing, or ACL access. It neither inherits scopes from the old token nor accumulates grants across runs. If `--expected-calendar-id` is given, the new token is rejected unless that account has `writer` or `owner` access to the calendar, so authorizing the wrong account cannot silently produce an unusable token.

Google OAuth scopes are per capability, not per calendar: no scope exists that grants access to a single calendar ID. To hard-limit a credential to one calendar, use a dedicated Google account or a service account and share only that calendar with it.

Each run replaces the full calendar year that Mawaqit publishes. Mawaqit supplies one year at a time, so the refresh never fabricates or requires unavailable next-year prayer dates; a run can be repeated safely at any point in the year.

## 🗓️ Roadmap to v1.0.0

### Calendar Operations
- Keep the registry as the single source of truth for supported mosques
- Run a dry-run refresh before any Google Calendar write
- Refresh the full published year with deterministic event IDs and duplicate protection
- Run the maintainer-only scheduled GitHub Actions job

## 🤝 Contributing

We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for details on:
- Setting up the development environment
- Code style guidelines
- Testing requirements
- Pull request process

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Mawaqit](https://mawaqit.net) for providing prayer time data
- Contributors who help make this project better
