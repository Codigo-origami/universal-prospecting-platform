# Changelog

All notable changes to **Universal Prospecting Platform** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):
`MAJOR.MINOR.PATCH` — MAJOR for big changes, MINOR for new features, PATCH for fixes.

## [Unreleased]

## [9.0.1] - 2026-10-07

### Fixed
- `start.bat` closed immediately on the first run: a message with parentheses inside a block broke `install.bat`. The installer was rewritten without fragile blocks.
- The window now always stays open with a clear message if the installation fails or the app stops.
- Streamlit's first-run email question no longer blocks the start.
- The installer checks the real Python version (3.10–3.13) and ignores the Microsoft Store "python" shortcut.

## [9.0.0] - 2026-10-07 — "Turbo Core"

### Added
- **English / Spanish interface** with a language selector, and a help tooltip (ⓘ) on every field.
- **Formatted Excel export** (`.xlsx`) that looks like the on-screen table: same columns, colours per priority badge, score bars, clickable links, filters, frozen header and a summary sheet.
- **Email confidence** for every email: HIGH (company domain), MEDIUM (free mail found on the company's own site or page), LOW (another company's domain).
- **MX verification** of email domains before saving them (optional).
- **International phone and WhatsApp normalisation** with mobile detection, based on the country of each location.
- **Contact page discovery** from the website's own links, in several languages.
- **JavaScript websites** rendered in a real browser when the plain HTML has no contact data.
- **Facebook page reading** to find emails when the website has none.
- **CAPTCHA / rate-limit handling**: all tabs pause automatically, the CAPTCHA can be solved in the visible window, and the run stops cleanly (everything saved) if Google keeps blocking.
- **Persistent browser profile** using the installed Chrome when available (fewer CAPTCHAs).
- New Discovery options: parallel tabs, fast browser (no images), show browser, search-engine fallback, social search, re-enrichment age, debug mode.
- New Qualify filters: location and free-text search. Clickable links and score bars in the table.
- Prospect tab: template selector (`template_*.html`), email preview, **test email to yourself**, `[Company Name]` also usable in the subject.
- `template_es.html` (Spanish template).
- **One-click start**: `start.bat` installs everything on first run in a private `.venv` and reinstalls automatically when `requirements.txt` changes.
- `CHANGELOG.md`, `.gitignore`, `.streamlit/config.toml` (app colours).

### Changed
- **Much faster discovery**: Google Maps search and place pages run in parallel (1–4 tabs) while websites are analysed in a 12-thread pool. End of the results list is detected to avoid useless scrolling.
- Known prospects are skipped unless older than N days (configurable) or the ICP rules changed.
- `install.bat` now creates an isolated virtual environment, supports Python 3.10–3.13 and shows bilingual messages.
- Dependencies updated (`streamlit>=1.40`, `playwright>=1.45`, …) and new ones added: `openpyxl`, `phonenumbers`, `dnspython`.
- Search-engine requests are throttled and automatically paused if DuckDuckGo starts blocking.
- Clearing the local database now requires a confirmation.
- Header credits: "Developed by Código Origami · Alejandro Moreno".

### Fixed
- Junk emails (search-engine error pages, tracking hashes, image names, placeholders) are no longer saved.
- Emails stuck to the next word (e.g. `info@site.comPhone`) are cut correctly.
- Search-engine emails unrelated to the company are discarded instead of being kept.
- Button styles with recent Streamlit versions.

## [8.12.0] - "The Enterprise Core - Ultimate"

### Added
- ICP qualification (required gate, weighted strong and bonus signals, absolute exclusions with contextual negation).
- Hierarchical identity resolution and deduplication with conflict logging.
- FAST / SMART / DEEP enrichment modes.
- Native Gmail outreach with atomic transactions and global recipient locks.
- Local SQLite database with automatic schema migrations.

[Unreleased]: https://github.com/Codigo-origami/universal-prospecting-platform/compare/v9.0.1...HEAD
[9.0.1]: https://github.com/Codigo-origami/universal-prospecting-platform/compare/v9.0.0...v9.0.1
[9.0.0]: https://github.com/Codigo-origami/universal-prospecting-platform/compare/v8.12.0...v9.0.0
[8.12.0]: https://github.com/Codigo-origami/universal-prospecting-platform/releases/tag/v8.12.0
