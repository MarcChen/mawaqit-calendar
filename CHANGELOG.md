# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-09-04
- Merged PR #1 by @MarcChen: #1 Project ini
**Core Functionality Implementation:**

* Added initial version of `src/calendar/ics_generator.py`, implementing the main ICS calendar generation logic, including event creation, alarm configuration, and file output for mosque prayer times.
* Defined configuration constants in `src/config/settings.py` for processed data and calendar output directories.
* Created `src/models/calendar_config.py` with Pydantic models for calendar and event configuration, supporting flexible calendar generation and validation.

**Data Addition:**

* Added metadata for the Grande Mosquée de Paris in `data/processed/grande-mosquee-de-paris/mosque_metadata.json`, providing sample mosque data for scraping and calendar generation.

