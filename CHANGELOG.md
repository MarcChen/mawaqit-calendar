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

## [0.2.0] - 2025-09-13
- Merged PR #2 by @MarcChen: Ini project website 
This pull request sets up the initial structure for the Mawaqit Calendar website, including configuration, data, and deployment workflows. It introduces a Next.js 15 static site for displaying mosque information, complete with Tailwind CSS styling, ESLint setup, and automated Vercel deployments for both preview and production environments. The most important changes are grouped below:

**Deployment Automation**

* Added `.github/workflows/vercel-preview.yml` and `.github/workflows/vercel-production.yml` to automate Vercel deployments for preview (on pull requests) and production (on `main` branch pushes) for the `website` directory. These workflows build, deploy, and comment deployment URLs on PRs or log them for production. [[1]](diffhunk://#diff-15b5b68513ac87f8c89235c00cca78613c5187407ba33ad9a6fe7d07115d8238R1-R67) [[2]](diffhunk://#diff-19cb09ef186f9bfbe37a41e4744e63bf4296b059c6b19e22dcec2b8c9b237392R1-R71)

**Project Initialization & Configuration**

* Added `website/package.json` with Next.js 15, React 19, Tailwind CSS 4, TypeScript, and ESLint dependencies, along with scripts for development, building, exporting, linting, and deployment.
* Added `website/next.config.ts` to configure Next.js for static export, trailing slashes, and unoptimized images for compatibility with static hosting.
* Added `website/postcss.config.mjs` to enable Tailwind CSS via PostCSS.
* Added `website/.gitignore` to ignore build artifacts, environment files, and dependencies.
* Added `website/eslint.config.mjs` for linting with Next.js and TypeScript support, ignoring build and dependency folders.

**Mosque Data & Core Functionality**

* Added `website/public/data/mosque_metadata.json` containing metadata for two mosques, including location, facilities, images, and external links.
* Implemented main page logic in `website/src/app/page.tsx`

## [0.3.0] - 2025-09-21
- Merged PR #3 by @MarcChen: Feat/add gcalendar integration
This pull request introduces Google Calendar integration for mosque prayer times, adds developer tooling for code quality and automation, and refactors parts of the calendar generation code for consistency and maintainability. The most significant changes are grouped below.

**Google Calendar Integration:**

* Added `src/calendar/google_calendar.py` implementing a `GoogleCalendarClient` class to create, manage, and publish Google Calendars, including batch event insertion from ICS files, authentication, and public calendar sharing.
* Added `scripts/create_prayer_times_google_calendar.py` script to automate scraping mosque data, generating prayer calendars, and publishing them to Google Calendar, with robust error handling and logging.
* Updated dependencies in `pyproject.toml` to include Google API client libraries required for calendar integration.

**Developer Tooling & Automation:**

* Added `.pre-commit-config.yaml` to enable pre-commit hooks for linting, formatting, and code hygiene checks using Ruff and standard pre-commit hooks.
* Added `.vscode/tasks.json` for convenient build and run tasks in VS Code, streamlining local development workflows.

**Calendar Generation Refactoring:**

* Refactored `src/calendar/ics_generator.py` for improved type annotations, logging consistency (using debug level for non-critical info), and minor code cleanups. [[1]](diffhunk://#diff-5b7f5a48bc3dd0afee54cb8d6c7f18f74747a9303757423304b4d7ddc94266d8L1-L12) [[2]](diffhunk://#diff-5b7f5a48bc3dd0afee54cb8d6c7f18f74747a9303757423304b4d7ddc94266d8L24-R24) [[3]](diffhunk://#diff-5b7f5a48bc3dd0afee54cb8d6c7f18f74747a9303757423304b4d7ddc94266d8L181-R181) [[4]](diffhunk://#diff-5b7f5a48bc3dd0afee54cb8d6c7f18f74747a9303757423304b4d7ddc94266d8L213-R220) [[5]](diffhunk://#diff-5b7f5a48bc3dd0afee54cb8d6c7f18f74747a9303757423304b4d7ddc94266d8L239-R239) [[6]](diffhunk://#diff-5b7f5a48bc3dd0afee54cb8d6c7f18f74747a9303757423304b4d7ddc94266d8L251-R252) [[7]](diffhunk://#diff-5b7f5a48bc3dd0afee54cb8d6c7f18f74747a9303757423304b4d7ddc94266d8R274) [[8]](diffhunk://#diff-5b7f5a48bc3dd0afee54cb8d6c7f18f74747a9303757423304b4d7ddc94266d8L287-R288)
* Added a placeholder script `scripts/add_new_prayer_times.py` for future automation of annual prayer time updates.

**Configuration Updates:**

* Added `GLOBAL_METADATA_PATH` constant to `src/config/settings.py` for centralized metadata file path management.
* Updated optional and test dependencies in `pyproject.toml` to include `pre-commit` and clarified dev/test separation.

**Other Changes:**

* Removed obsolete mosque metadata file for the Grande Mosquée de Paris, likely due to migration or update in data handling.
* Minor cleanups in `pyproject.toml` for linting configuration.

## [0.4.0] - 2025-09-21
- Merged PR #4 by @MarcChen: feat: add @vercel/analytics integration to track user interactions


## [0.4.1] - 2025-09-26
- Merged PR #5 by @MarcChen: feat: added more data


