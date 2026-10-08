# Contributing to Mawaqit Calendar 🤝

Thank you for your interest in contributing to Mawaqit Calendar! This project aims to make prayer times easily accessible to the Muslim community worldwide.

## 🌟 Ways to Contribute

### 🐛 Bug Reports
- Report issues with mosque scraping
- Calendar generation problems
- Data validation errors
- Performance issues

### ✨ Feature Requests
- New mosque sources
- Calendar customization options
- Calendar registry and subscription improvements
- API enhancements

### 💻 Code Contributions
- Bug fixes
- New features
- Performance optimizations
- Documentation improvements

### 📝 Documentation
- README improvements
- Code documentation
- User guides
- API documentation

### 🕌 Mosque Data
- Add new mosques to `registry/mosque_calendars.json`
- Verify existing mosque information
- Report outdated prayer times


## 🔧 Development Guidelines

### Code Style
We use [Ruff](https://github.com/astral-sh/ruff) for code formatting and linting:

```bash
# Format code
ruff format src/ tests/

# Check for issues
ruff check src/ tests/

# Fix auto-fixable issues
ruff check --fix src/ tests/
```

### Code Standards
- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Follow Google-style docstrings
- **Error Handling**: Implement proper error handling with logging
- **Validation**: Use Pydantic models for data validation
