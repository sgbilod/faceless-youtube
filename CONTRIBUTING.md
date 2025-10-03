# Contributing to Faceless YouTube Automation Platform

First off, thank you for considering contributing! 🎉

This project aims to democratize content creation through AI automation. Every contribution helps make this tool more accessible and powerful.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing Guidelines](#testing-guidelines)
- [Documentation Guidelines](#documentation-guidelines)

## 📜 Code of Conduct

### Our Pledge

We pledge to make participation in this project a harassment-free experience for everyone, regardless of:
- Age, body size, disability, ethnicity, gender identity
- Experience level, education, socio-economic status
- Nationality, personal appearance, race, religion
- Sexual identity and orientation

### Our Standards

**Positive behavior:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior:**
- Trolling, insulting/derogatory comments, personal attacks
- Public or private harassment
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

## 🤝 How Can I Contribute?

### Reporting Bugs

Before creating bug reports:
- **Check existing issues** to avoid duplicates
- **Use the bug report template** (.github/ISSUE_TEMPLATE/bug_report.md)
- **Include as much detail as possible**: OS, Python version, steps to reproduce

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues:
- **Use the feature request template** (.github/ISSUE_TEMPLATE/feature_request.md)
- **Explain the problem** your feature solves
- **Consider cost implications** (we prioritize FREE solutions)

### Code Contributions

1. **Find an issue** to work on (or create one)
2. **Comment on the issue** to claim it
3. **Fork the repository**
4. **Create a feature branch**
5. **Make your changes**
6. **Submit a pull request**

## 🛠️ Development Setup

### Prerequisites

- Python 3.11+
- Git
- Docker & Docker Compose (optional but recommended)
- FFmpeg

### Initial Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/faceless-youtube.git
cd faceless-youtube

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/faceless-youtube.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
alembic upgrade head

# Run tests to verify setup
pytest
```

### Running the Application

```bash
# Development mode
python -m src.main

# With Docker Compose
docker-compose up -d
```

## 📝 Coding Standards

### Python Style Guide

We follow **PEP 8** with some project-specific conventions:

```python
# GOOD: Clear function names with type hints
def generate_video(
    script: str,
    duration: int,
    output_path: Path
) -> Video:
    """
    Generate video from script.
    
    Args:
        script: Video script content
        duration: Video duration in seconds
        output_path: Path to save generated video
        
    Returns:
        Video object with metadata
        
    Raises:
        ValueError: If script is empty
        IOError: If output_path is not writable
    """
    pass

# BAD: No type hints, unclear name
def gen(s, d, o):
    pass
```

### Code Formatting

We use automated formatters:

```bash
# Format code with Black
black src/ tests/

# Lint with Ruff
ruff check src/ tests/

# Type check with mypy
mypy src/
```

### Import Organization

```python
# Standard library imports
import os
from pathlib import Path
from typing import List, Optional

# Third-party imports
from fastapi import FastAPI, Depends
from sqlalchemy import select

# Local application imports
from src.core.models import Video
from src.core.database import get_db
from src.services.video_generator import VideoGenerator
```

### Naming Conventions

- **Variables/Functions:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private methods:** `_leading_underscore`
- **Files:** `snake_case.py`

```python
# GOOD
MAX_VIDEO_LENGTH = 3600
class VideoGenerator:
    def generate_video(self):
        pass
    
    def _validate_script(self):  # Private method
        pass

# BAD
maxVideoLength = 3600  # Not snake_case
class video_generator:  # Not PascalCase
    def GenerateVideo(self):  # Not snake_case
        pass
```

### Documentation

Every function must have a docstring:

```python
def calculate_video_duration(assets: List[Asset]) -> int:
    """
    Calculate total video duration from assets.
    
    This function sums the duration of all assets and applies
    transition time adjustments.
    
    Args:
        assets: List of Asset objects with duration_seconds attribute
        
    Returns:
        Total duration in seconds (int)
        
    Raises:
        ValueError: If assets list is empty
        
    Example:
        >>> assets = [Asset(duration_seconds=10), Asset(duration_seconds=20)]
        >>> calculate_video_duration(assets)
        30
        
    Note:
        Transition effects add 1 second per transition
    """
    if not assets:
        raise ValueError("Assets list cannot be empty")
    
    base_duration = sum(asset.duration_seconds for asset in assets)
    transition_time = (len(assets) - 1) * 1  # 1 second per transition
    return base_duration + transition_time
```

## 📌 Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting (no logic change)
- `refactor`: Code restructuring (no behavior change)
- `perf`: Performance improvement
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples:**

```bash
# Feature
git commit -m "feat(video): add auto-caption generation"

# Bug fix
git commit -m "fix(database): resolve connection pool timeout issue"

# Documentation
git commit -m "docs(readme): add installation instructions for Windows"

# Performance
git commit -m "perf(asset): optimize database queries with eager loading"
```

### Commit Best Practices

- **Atomic commits:** One logical change per commit
- **Present tense:** "Add feature" not "Added feature"
- **Imperative mood:** "Fix bug" not "Fixes bug"
- **Reference issues:** "Fixes #123" to auto-close issues

## 🔄 Pull Request Process

### Before Submitting

1. **Update from upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests:**
   ```bash
   pytest
   pytest --cov=src --cov-report=html
   ```

3. **Format code:**
   ```bash
   black src/ tests/
   ruff check src/ tests/ --fix
   mypy src/
   ```

4. **Update documentation:**
   - Code comments
   - Docstrings
   - README.md (if needed)
   - CHANGELOG.md

### PR Template

Use the provided template (.github/pull_request_template.md):
- Fill out all sections
- Check all applicable boxes
- Add screenshots for UI changes
- Include test results
- Explain cost/performance impact

### Review Process

1. **Automated checks must pass:**
   - CI/CD pipeline (tests, linting, type checking)
   - Code coverage >= 90%
   - No security vulnerabilities

2. **Code review:**
   - At least 1 approval required
   - Address all review comments
   - Be responsive to feedback

3. **Final checks:**
   - No merge conflicts
   - Commit history is clean
   - Documentation updated

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/              # Unit tests (fast, isolated)
│   ├── test_models.py
│   ├── test_database.py
│   └── test_services/
├── integration/       # Integration tests (slower)
│   ├── test_api.py
│   └── test_workflows.py
└── e2e/              # End-to-end tests (slowest)
    └── test_video_generation.py
```

### Writing Tests

```python
import pytest
from src.core.models import Video, VideoStatus

class TestVideo:
    """Test Video model."""
    
    def test_create_video(self, db_session):
        """Test creating a video record."""
        video = Video(
            title="Test Video",
            duration_seconds=300,
            status=VideoStatus.COMPLETED
        )
        db_session.add(video)
        db_session.commit()
        
        assert video.id is not None
        assert video.title == "Test Video"
        assert video.status == VideoStatus.COMPLETED
    
    def test_video_title_required(self, db_session):
        """Test that title is required."""
        with pytest.raises(ValueError):
            video = Video(duration_seconds=300)
            db_session.add(video)
            db_session.commit()
    
    @pytest.mark.parametrize("duration", [0, -1, 10000000])
    def test_video_duration_validation(self, duration):
        """Test duration validation."""
        # Test various duration values
        pass
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_models.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run only fast tests
pytest -m "not slow"

# Run tests matching pattern
pytest -k "test_video"
```

### Test Coverage

- **Minimum coverage:** 90%
- **Critical paths:** 100% (auth, payments, data persistence)
- **Focus on:** Edge cases, error handling, integration points

## 📚 Documentation Guidelines

### Code Documentation

```python
# GOOD: Clear, comprehensive docstring
def scrape_assets(
    source: str,
    query: str,
    limit: int = 10
) -> List[Asset]:
    """
    Scrape assets from specified source.
    
    Fetches video/image assets from free stock platforms based on
    search query. Results are cached for 1 hour to reduce API calls.
    
    Args:
        source: Asset source platform ('pexels', 'pixabay', 'unsplash')
        query: Search query (e.g., "nature sunset")
        limit: Maximum number of assets to return (1-100)
        
    Returns:
        List of Asset objects with metadata populated
        
    Raises:
        ValueError: If source is not supported
        APIError: If source API returns error
        RateLimitError: If API rate limit exceeded
        
    Example:
        >>> assets = scrape_assets('pexels', 'mountain', limit=5)
        >>> len(assets)
        5
        >>> assets[0].source_platform
        'pexels'
    """
    pass
```

### README Guidelines

- Keep README.md up to date
- Include installation instructions
- Add usage examples
- Update feature list
- Keep screenshots current

### Architecture Documentation

- Update ARCHITECTURE.md for significant changes
- Include Mermaid diagrams for complex flows
- Document design decisions and trade-offs

## 💰 Cost Considerations

This project prioritizes cost-effective solutions:

1. **Always prefer FREE:**
   - Local AI models (Ollama, GPT4All)
   - Free stock assets (Pexels, Pixabay)
   - Open-source TTS (Coqui, pyttsx3)

2. **Freemium second:**
   - Use free tiers aggressively
   - Document cost implications in PR

3. **Paid last:**
   - Requires strong justification
   - Must improve revenue/cost ratio
   - Needs approval from maintainers

## 🎓 Learning Resources

- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/en/20/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

## ❓ Questions?

- **General questions:** Open a [Discussion](https://github.com/OWNER/faceless-youtube/discussions)
- **Bug reports:** Use [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md)
- **Feature requests:** Use [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md)

## 🏆 Recognition

Contributors are recognized in:
- README.md contributors section
- CHANGELOG.md for each release
- GitHub contributors page

---

Thank you for contributing to Faceless YouTube Automation Platform! 🚀

Together, we're democratizing content creation through AI automation.
