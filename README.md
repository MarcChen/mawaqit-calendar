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


## 🗓️ Roadmap to v1.0.0

### 🌐 Static Website Features
- **Mosque Discovery**: Search and browse available mosques by location
- **Direct Subscription**: One-click calendar subscription links
- **Multiple Formats**: Support for Google Calendar, Outlook, Apple Calendar
- **Mosque Details**: Display mosque information, facilities, and contact details
- **Responsive Design**: Mobile-friendly interface

### 🔄 Automation & Deployment
- **GitHub Actions**: Automated daily scraping and calendar updates
- **GitHub Pages**: Static website deployment

### 📊 Enhanced Features
- **Combined Calendars**: City-wide or regional prayer time calendars
- **Multi-language Support**: Internationalization for different languages
- **Prayer Time Notifications**: Optional reminder settings

### 🔗 Integration Goals
- **Direct Calendar URLs**: `https://username.github.io/mawaqit-calendar/calendars/mosque-{id}.ics`
- **Subscription Instructions**: Step-by-step guides for different calendar apps

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
