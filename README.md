# Mawaqit Calendar 🕌

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](VERSION)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

> **⚠️ DEPRECATION NOTICE**: The website/batch scraping approach has been deprecated. The project now focuses on a personal CLI tool for syncing prayer times to your own Google Calendar.

Sync mosque prayer times from [Mawaqit](https://mawaqit.net) directly to your personal Google Calendar. Run it once a month to keep your calendar up-to-date with your mosque's prayer schedule.

## 🚀 Features

- **Personal Calendar Sync**: Connect your Google Calendar to a specific mosque
- **Monthly Updates**: Designed to run once per month to sync upcoming prayer times
- **Interactive CLI**: Easy-to-use Typer-based command line interface
- **Smart Configuration**: Stores your mosque and calendar preferences
- **Conflict-Free**: Clears old events before adding new ones
- **Prayer Reminders**: Automatic 15-minute reminders for each prayer

## 📦 Installation

```bash
pip install mawaqit-calendar
```

Or install from source:

```bash
git clone https://github.com/marcChen/mawaqit-calendar.git
cd mawaqit-calendar
pip install -e .
```

## 🔧 Setup

### 1. Google Calendar API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing
3. Enable the **Google Calendar API**
4. Create **OAuth 2.0 credentials** (Desktop application type)
5. Download the credentials JSON file
6. Move it to `~/.mawaqit-calendar/credentials.json`

### 2. Initial Configuration

Run the setup wizard to connect your mosque and calendar:

```bash
mawaqit-calendar setup
```

This will:
- Authenticate with your Google account
- Let you select or create a calendar
- Configure your mosque URL

## 💻 Usage

### Setup (One-time)

```bash
# Interactive setup
mawaqit-calendar setup

# Or with arguments
mawaqit-calendar setup --mosque-url "https://mawaqit.net/fr/m/grande-mosquee-de-paris"
```

### Sync Prayer Times

```bash
# Sync next month (default)
mawaqit-calendar sync

# Sync specific month
mawaqit-calendar sync --month 5 --year 2026

# Dry run (see what would be synced without making changes)
mawaqit-calendar sync --dry-run
```

### Check Status

```bash
mawaqit-calendar status
```

### View Configuration

```bash
mawaqit-calendar config-show
```

## 📋 CLI Commands

| Command | Description |
|---------|-------------|
| `setup` | Configure mosque and calendar (one-time) |
| `sync` | Sync prayer times for upcoming month |
| `status` | Show current configuration and sync status |
| `config-show` | Display configuration file contents |

## 🔧 Configuration

Configuration is stored in `~/.mawaqit-calendar/config.json`:

```json
{
  "mosque_url": "https://mawaqit.net/fr/m/grande-mosquee-de-paris",
  "calendar_id": "your-calendar-id@group.calendar.google.com",
  "last_sync": "2026-04-21T14:30:00"
}
```

## 🧪 Testing

Run the test suite:

```bash
# Unit tests
pytest tests/ -v

# Integration tests (makes real HTTP requests)
pytest tests/ -v -m integration

# Specific integration test for Grande Mosquée de Paris
pytest tests/test_integration_mosque_scraper.py -v
```

### Integration Test

The integration test verifies we can successfully scrape prayer data from:
- **Grande Mosquée de Paris**: https://mawaqit.net/fr/m/grande-mosquee-de-paris

This ensures the scraper works correctly with real Mawaqit data.

## 🏗️ Architecture

```
mawaqit-calendar/
├── src/
│   ├── cli.py                  # Typer CLI (NEW - main entry point)
│   ├── scrapers/
│   │   └── mawaqit_scraper.py  # Mawaqit website scraper
│   ├── models/
│   │   ├── mosque.py           # Mosque data models
│   │   └── prayer_time.py      # Prayer time models
│   └── calendar/
│       └── ics_generator.py    # ICS calendar generation (legacy)
├── tests/
│   └── test_integration_mosque_scraper.py  # Integration tests
└── website/                    # DEPRECATED - old batch approach
```

## ⚠️ Deprecated Features

The following features have been deprecated in favor of the personal CLI approach:

- ❌ Batch scraping all mosques
- ❌ Static website generation
- ❌ GitHub Pages deployment
- ❌ GitHub Actions automated scraping
- ❌ City-wide combined calendars

**Why the change?**
- **Personal focus**: Better suited for individual use
- **Lower maintenance**: No need to host a website
- **Privacy**: Your calendar data stays in your Google account
- **Flexibility**: Choose any mosque, not just pre-scraped ones

## 🤝 Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE)

## 🙏 Acknowledgments

- [Mawaqit](https://mawaqit.net) for providing prayer time data
- Contributors who help make this project better
