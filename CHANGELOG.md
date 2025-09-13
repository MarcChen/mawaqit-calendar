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

