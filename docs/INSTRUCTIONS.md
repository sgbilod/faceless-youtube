# GITHUB COPILOT INSTRUCTIONS

## Faceless YouTube Automation Platform v2.0

**Project-Specific AI Assistant Directives**

---

## 🎯 PROJECT OVERVIEW [REF:PROJ-001]

**Mission:** Transform functional prototype into world-class autonomous revenue generation platform for faceless YouTube content creation.

**Current State:** PyQt5 monolithic app with basic video generation  
**Target State:** Microservices architecture with AI-driven automation, multi-platform publishing, and enterprise-grade infrastructure

---

## 💰 STRATEGIC CONSTRAINTS [REF:STRAT-002]

### Cost Optimization (CRITICAL)

1. **FREE FIRST:** Always use free/open-source alternatives before paid APIs
   - Voice: `pyttsx3`, `Coqui TTS`, `Ollama` (NOT ElevenLabs initially)
   - AI: `Ollama` (Mistral/Llama2), `GPT4All` (NOT GPT-4 initially)
   - Assets: 20 free stock sites (NO paid stock initially)
2. **FREEMIUM SECOND:** Use free tiers aggressively

   - OpenAI: GPT-3.5-turbo ($0.002/1K tokens) before GPT-4
   - Google Cloud TTS: Free tier before Azure Neural
   - ElevenLabs: 10K chars/month free tier

3. **PAID LAST:** Upgrade only after revenue proves ROI
   - Monitor: Cost must be < 20% of generated revenue
   - Rule: No API upgrade until generating $500+/month

### Performance Targets

- Video rendering: < 2 minutes for 10-minute video
- Script generation: < 10 seconds
- Asset search: < 1 second
- API response: < 100ms
- Database queries: < 50ms
- Memory usage: < 2GB during operation

### Quality Standards

- Test coverage: 90%+ minimum
- Code coverage: 95%+ for core modules
- Documentation: Every function must have docstring
- Error handling: All external calls must have try/except
- Logging: All operations must be logged
- Security: All credentials must be encrypted

---

## 🏗️ ARCHITECTURAL PRINCIPLES [REF:ARCH-003]

### 1. Local-First Development

```python
# GOOD: Local processing, no cloud costs
from ollama import Client
model = Client(host='localhost:11434')

# BAD: Immediate cloud dependency
from openai import OpenAI
client = OpenAI(api_key=expensive_key)
```

### 2. Microservices Design

- **Rule:** Each service = single responsibility
- **Communication:** REST + gRPC (not monolithic imports)
- **Isolation:** Services can be deployed independently
- **Scaling:** Horizontal scaling per service

### 3. Database Strategy

```python
# GOOD: Normalized schema with indexes
class Video(Base):
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, index=True)  # Index for queries

# BAD: Storing JSON blobs
config_json = Column(Text)  # Anti-pattern
```

### 4. Caching Everything

```python
# ALWAYS implement caching for:
# - API responses (TTL: 1 hour)
# - Database queries (TTL: 5 minutes)
# - Asset metadata (TTL: 24 hours)
# - ML model predictions (TTL: 1 week)

from functools import lru_cache
import redis

@lru_cache(maxsize=1000)
def expensive_computation(param):
    # Cache in memory for repeated calls
    pass
```

### 5. Async/Await Everywhere

```python
# GOOD: Non-blocking operations
async def generate_video(script):
    voice_task = asyncio.create_task(generate_voice(script))
    assets_task = asyncio.create_task(fetch_assets(script))
    thumbnail_task = asyncio.create_task(create_thumbnail(script))

    voice, assets, thumbnail = await asyncio.gather(
        voice_task, assets_task, thumbnail_task
    )

# BAD: Blocking operations
voice = generate_voice(script)  # Wait
assets = fetch_assets(script)  # Wait
thumbnail = create_thumbnail(script)  # Wait
```

---

## 📝 CODING STANDARDS [REF:CODE-004]

### File Organization

```
src/
├── core/
│   ├── __init__.py
│   ├── video_generator.py      # Main video generation logic
│   ├── script_generator.py     # AI script generation
│   └── publisher.py             # Multi-platform publishing
├── services/
│   ├── content_generator/      # Port 8001
│   ├── video_renderer/         # Port 8002
│   └── asset_manager/          # Port 8003
├── ai_engine/
│   ├── models/                  # ML models
│   ├── embeddings/              # CLIP, text embeddings
│   └── classifiers/             # Asset classification
├── ui/
│   ├── main_window.py           # PyQt6 main UI
│   ├── widgets/                 # Custom widgets
│   └── themes/                  # UI themes
├── api/
│   ├── routes/                  # FastAPI routes
│   ├── schemas/                 # Pydantic models
│   └── middleware/              # Auth, CORS, etc.
└── utils/
    ├── config.py                # Configuration management
    ├── logger.py                # Logging setup
    └── security.py              # Encryption utilities
```

### Naming Conventions

```python
# Classes: PascalCase
class VideoGenerator:
    pass

# Functions/methods: snake_case
def generate_video(script: str) -> Video:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_VIDEO_DURATION = 600
DEFAULT_RESOLUTION = "1080p"

# Private methods: leading underscore
def _internal_helper(self):
    pass

# Async functions: prefix with async_ (optional but helpful)
async def async_fetch_assets(query: str) -> List[Asset]:
    pass
```

### Type Hints (MANDATORY)

```python
from typing import List, Dict, Optional, Union
from pathlib import Path

# GOOD: Full type hints
async def process_video(
    script: str,
    assets: List[Path],
    config: Dict[str, Any],
    output_dir: Optional[Path] = None
) -> Video:
    """Process video with full type safety."""
    pass

# BAD: No type hints
def process_video(script, assets, config, output_dir=None):
    pass
```

### Docstrings (MANDATORY)

```python
def generate_script(niche: str, duration: int) -> str:
    """
    Generate meditation script using AI.

    Args:
        niche: Content niche (e.g., "sleep meditation", "focus music")
        duration: Target duration in seconds

    Returns:
        Generated script text

    Raises:
        APIError: If AI service is unavailable
        ValueError: If duration < 60 or > 3600

    Examples:
        >>> script = generate_script("sleep meditation", 600)
        >>> len(script) > 100
        True
    """
    pass
```

### Error Handling

```python
# GOOD: Specific exceptions, logging, graceful degradation
import logging

async def fetch_api_data(url: str) -> Optional[Dict]:
    """Fetch data with proper error handling."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        logging.error(f"API timeout: {url}")
        return None
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error {e.response.status_code}: {url}")
        return None
    except Exception as e:
        logging.exception(f"Unexpected error fetching {url}")
        return None

# BAD: Bare except, no logging
def fetch_api_data(url):
    try:
        return requests.get(url).json()
    except:
        return None
```

---

## 🤖 AI & AUTOMATION RULES [REF:AUTO-005]

### Script Generation

```python
# Priority order for AI providers:
# 1. Ollama (FREE, local) - Use first
# 2. GPT4All (FREE, offline) - Fallback #1
# 3. OpenAI GPT-3.5-turbo (CHEAP) - Fallback #2
# 4. OpenAI GPT-4 (EXPENSIVE) - Only if revenue > $500/month

class AIScriptGenerator:
    def __init__(self):
        self.providers = [
            OllamaProvider(),      # Try first
            GPT4AllProvider(),     # Try second
            OpenAIProvider()       # Try last
        ]

    async def generate(self, prompt: str) -> str:
        for provider in self.providers:
            try:
                result = await provider.generate(prompt)
                if result:
                    return result
            except Exception as e:
                logging.warning(f"{provider} failed: {e}")
                continue

        raise AIGenerationError("All providers failed")
```

### Voice Synthesis

```python
# Priority order:
# 1. Coqui TTS (FREE, local, high quality) - Use first
# 2. pyttsx3 (FREE, offline, lower quality) - Fallback
# 3. Google Cloud TTS (CHEAP, $4/1M chars) - Only if needed
# 4. ElevenLabs (EXPENSIVE) - Only if revenue > $1000/month

class VoiceGenerator:
    def __init__(self):
        try:
            self.engine = CoquiTTS()  # Try high-quality free first
        except Exception:
            self.engine = pyttsx3.init()  # Fallback to offline
```

### Asset Selection Intelligence

```python
# Use ML to select best assets based on:
# - Semantic similarity (CLIP embeddings)
# - Historical performance (views, engagement)
# - Emotional alignment (sentiment analysis)
# - Visual style trends (color, motion, composition)

async def select_optimal_assets(
    script: str,
    required_count: int = 5
) -> List[Asset]:
    """Select assets using AI and performance data."""
    # Get semantic matches using CLIP
    semantic_matches = await clip_search(script, top_k=20)

    # Filter by performance
    high_performers = [
        a for a in semantic_matches
        if a.avg_engagement > 0.05  # 5% engagement threshold
    ]

    # Rank by composite score
    ranked = sorted(
        high_performers,
        key=lambda a: a.semantic_score * 0.5 + a.performance_score * 0.5,
        reverse=True
    )

    return ranked[:required_count]
```

---

## 📊 TESTING REQUIREMENTS [REF:TEST-006]

### Test Structure

```
tests/
├── unit/
│   ├── test_video_generator.py
│   ├── test_script_generator.py
│   └── test_asset_manager.py
├── integration/
│   ├── test_database.py
│   ├── test_api_endpoints.py
│   └── test_external_apis.py
├── e2e/
│   ├── test_full_video_pipeline.py
│   └── test_multi_platform_publish.py
└── performance/
    ├── test_rendering_speed.py
    └── test_concurrent_operations.py
```

### Test Example

```python
import pytest
from unittest.mock import AsyncMock, patch

class TestVideoGenerator:
    @pytest.fixture
    async def generator(self):
        """Create test generator instance."""
        return VideoGenerator(config=test_config)

    @pytest.mark.asyncio
    async def test_generate_video_success(self, generator):
        """Test successful video generation."""
        script = "Test meditation script for relaxation."

        result = await generator.generate(
            script=script,
            duration=60,
            style="meditation"
        )

        assert result.success is True
        assert result.video_path.exists()
        assert result.duration >= 60
        assert result.file_size > 0

    @pytest.mark.asyncio
    async def test_generate_video_empty_script(self, generator):
        """Test error handling for empty script."""
        with pytest.raises(ValueError, match="Script cannot be empty"):
            await generator.generate(script="")

    @pytest.mark.parametrize("animation", ["fade", "slide", "static"])
    async def test_text_animations(self, generator, animation):
        """Test all animation styles."""
        result = await generator.apply_animation(
            text="Test",
            style=animation
        )
        assert result.animation_type == animation
```

---

## 🔒 SECURITY REQUIREMENTS [REF:SEC-007]

### Credential Management

```python
# ALWAYS use encryption for secrets
from cryptography.fernet import Fernet
import keyring

class SecureVault:
    """Encrypted credential storage."""

    def __init__(self):
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)

    def store(self, service: str, username: str, password: str):
        """Store encrypted credential."""
        encrypted = self.cipher.encrypt(password.encode())
        keyring.set_password(service, username, encrypted.decode())

    def retrieve(self, service: str, username: str) -> Optional[str]:
        """Retrieve and decrypt credential."""
        encrypted = keyring.get_password(service, username)
        if encrypted:
            return self.cipher.decrypt(encrypted.encode()).decode()
        return None

# NEVER do this:
API_KEY = "sk-hardcoded-key-here"  # SECURITY VIOLATION
```

### Input Validation

```python
from pydantic import BaseModel, validator, Field

class VideoGenerationRequest(BaseModel):
    """Validated input for video generation."""

    script: str = Field(..., min_length=50, max_length=10000)
    duration: int = Field(..., ge=60, le=3600)
    style: str = Field(..., regex="^(meditation|sleep|focus)$")

    @validator('script')
    def script_not_malicious(cls, v):
        """Prevent injection attacks."""
        forbidden = ['<script>', 'javascript:', 'onerror=']
        if any(x in v.lower() for x in forbidden):
            raise ValueError("Malicious content detected")
        return v
```

---

## 📚 DOCUMENTATION REQUIREMENTS [REF:DOC-008]

### README Structure

```markdown
# Faceless YouTube Automation Platform

## Quick Start

[Installation steps]

## Features

[Feature list with examples]

## Architecture

[System diagram + explanation]

## Configuration

[Config file examples]

## API Reference

[API endpoints + examples]

## Troubleshooting

[Common issues + solutions]

## Contributing

[How to contribute]

## License

[License info]
```

### Code Comments

```python
# GOOD: Explain WHY, not WHAT
# Use exponential backoff because API has aggressive rate limiting
# that resets every 60 seconds. 3 retries give us 1 + 2 + 4 = 7 seconds
for attempt in range(3):
    try:
        return await api_call()
    except RateLimitError:
        await asyncio.sleep(2 ** attempt)

# BAD: Comments that just repeat code
# Retry 3 times
for attempt in range(3):
    ...
```

---

## 🚀 DEPLOYMENT GUIDELINES [REF:DEPLOY-009]

### Docker Best Practices

```dockerfile
# Multi-stage build for smaller images
FROM python:3.11-slim as builder
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

FROM python:3.11-slim
WORKDIR /app

# Copy only wheels (not entire build context)
COPY --from=builder /build/wheels /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/*.whl && rm -rf /tmp/wheels

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser /app
USER appuser

COPY src/ ./src/
CMD ["python", "-m", "src.main"]
```

### Environment Variables

```yaml
# config/default.yaml
database:
  host: ${DB_HOST:localhost}
  port: ${DB_PORT:5432}
  name: ${DB_NAME:faceless_youtube}

# Secrets in .env (NOT committed)
DB_PASSWORD=super-secret
OPENAI_API_KEY=sk-...
```

---

## 📞 COMMUNICATION PROTOCOL [REF:COMM-010]

### Progress Updates Format

```markdown
✅ COMPLETED: [Task Name]
📊 Results:

- Metric 1: Value
- Metric 2: Value
- Files created: X
- Lines of code: Y

⚠️ Issues:

- Issue 1: [Description + Resolution]
- Issue 2: [Description + Workaround]

💾 Artifacts:

- src/new_module.py (150 lines)
- tests/test_new_module.py (80 lines)
- docs/new_feature.md (documentation)

🔜 Next:

- Task A (2 hours)
- Task B (4 hours)

❓ Questions:

- Question 1?
- Question 2?
```

### Blocker Format

```markdown
🚫 BLOCKED: [Task Name]
❌ Issue: [Detailed description]
🔍 Attempted Solutions:

1. Tried X - didn't work because Y
2. Tried Z - partially worked but...

🆘 Help Needed:

- Specific question or guidance needed
- Alternative approaches to consider

⏸️ Paused Tasks:

- Task A (waiting on this blocker)
- Task B (depends on Task A)

⏰ Impact: [Timeline impact if not resolved]
```

---

## 🎯 EXECUTION PRIORITIES [REF:PRIORITY-011]

### Always Ask:

1. **Is this FREE?** Use free alternatives first
2. **Is this FAST?** Optimize for performance
3. **Is this TESTED?** Every feature needs tests
4. **Is this SECURE?** Encrypt credentials, validate input
5. **Is this DOCUMENTED?** Code without docs is incomplete
6. **Is this AUTOMATED?** Can this run without human intervention?

### Never Do:

1. ❌ Use paid APIs without confirming budget
2. ❌ Commit secrets or credentials
3. ❌ Write code without type hints
4. ❌ Skip error handling
5. ❌ Ignore test failures
6. ❌ Leave TODOs unresolved
7. ❌ Copy code without understanding

---

## 📋 QUICK REFERENCE [REF:QUICK-012]

### Import Order

```python
# 1. Standard library
import os
import sys
from typing import List, Dict

# 2. Third-party
import fastapi
import sqlalchemy
import numpy as np

# 3. Local application
from src.core import VideoGenerator
from src.utils import logger
```

### Async Best Practices

```python
# GOOD: Gather concurrent operations
voice, assets, thumb = await asyncio.gather(
    generate_voice(script),
    fetch_assets(script),
    create_thumbnail(script)
)

# BAD: Sequential awaits (slow)
voice = await generate_voice(script)
assets = await fetch_assets(script)
thumb = await create_thumbnail(script)
```

### Database Queries

```python
# GOOD: Use indexes, limit results
query = (
    session.query(Video)
    .filter(Video.created_at >= start_date)  # Indexed field
    .order_by(Video.views.desc())
    .limit(100)
)

# BAD: Full table scan
query = session.query(Video).all()  # Loads entire table
```

---

## 🔗 RELATED REFERENCES

- Master Directive: `copilot_master_prompt.md`
- Executive Summary: `GRAND_EXECUTIVE_SUMMARY.md`
- Architecture Diagrams: `docs/ARCHITECTURE.md`
- API Documentation: `docs/API.md`
- Deployment Guide: `docs/DEPLOYMENT.md`

---

**Last Updated:** October 3, 2025  
**Version:** 1.0  
**Maintainer:** GitHub Copilot (Claude Sonnet 4.5)

---

**END OF INSTRUCTIONS**
