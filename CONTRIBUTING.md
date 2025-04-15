# Contributing to Weather CLI

Thank you for your interest in contributing to Weather CLI! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in the [issues section](https://github.com/r123singh/weather-cli/issues)
2. If not, create a new issue with:
   - A clear, descriptive title
   - Steps to reproduce the bug
   - Expected behavior
   - Actual behavior
   - Screenshots if applicable
   - Environment details (OS, Python version, etc.)

### Suggesting Features

1. Check if the feature has already been suggested
2. Create a new issue with:
   - A clear, descriptive title
   - Detailed description of the feature
   - Use cases and benefits
   - Any mockups or examples

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature/fix
3. Make your changes
4. Write/update tests if necessary
5. Update documentation
6. Submit a pull request

## Development Setup

1. Fork and clone the repository
```bash
git clone https://github.com/r123singh/weather-cli.git
cd weather-cli
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -e ".[dev]"
```

4. Run tests
```bash
pytest
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for all functions
- Keep functions small and focused
- Use meaningful variable names

## Documentation

- Update README.md for significant changes
- Add/update docstrings for new/changed functions
- Update API documentation if necessary
- Keep the changelog up to date

## Testing

- Write tests for new features
- Ensure all tests pass
- Update tests for bug fixes
- Maintain test coverage

## Release Process

1. Update version in setup.py
2. Update CHANGELOG.md
3. Create a release tag
4. Build and upload to PyPI
5. Update documentation

## Questions?

Feel free to:
- Open an issue
- Join our [Discord community](https://discord.gg/weather-cli)
- Email us at support@weather-cli.com

Thank you for contributing to Weather CLI! 