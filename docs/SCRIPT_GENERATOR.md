# Script Generator Documentation

**AI-Powered Content Generation for Faceless YouTube Videos**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Content Niches](#content-niches)
4. [Configuration](#configuration)
5. [Usage Examples](#usage-examples)
6. [Validation System](#validation-system)
7. [API Reference](#api-reference)
8. [Ollama Setup](#ollama-setup)
9. [Troubleshooting](#troubleshooting)
10. [Performance Tips](#performance-tips)
11. [Production Deployment](#production-deployment)

---

## Overview

The Script Generator is an AI-powered service that creates high-quality video scripts for faceless YouTube content. It uses local LLMs (via Ollama) to generate engaging, niche-specific content with automatic quality validation and caching.

### ✨ Key Features

- **10 Content Niches**: Pre-configured templates for meditation, motivation, facts, stories, education, tech, finance, health, philosophy, and history
- **Local AI**: Uses Ollama for free, privacy-friendly content generation
- **Quality Validation**: Multi-layer checks for profanity, hate speech, disclaimers, and content quality
- **Smart Caching**: Reduces duplicate generations with Redis-backed caching
- **Batch Generation**: Create multiple scripts in parallel for efficiency
- **Component Extraction**: Automatic hook and call-to-action identification
- **Feedback Loop**: Regenerate and improve scripts based on user input
- **SEO Optimization**: Auto-generated titles, tags, and keywords

### 🎯 Use Cases

- Generate meditation scripts for calming videos
- Create motivational speeches with strong CTAs
- Produce educational content with clear structure
- Build fact-based videos with numbered points
- Craft engaging stories with emotional depth
- Generate tech explainers for beginners
- Create health content with proper disclaimers

---

## Quick Start

### 1. Install Ollama

```bash
# Windows (PowerShell)
winget install Ollama.Ollama

# Linux
curl https://ollama.ai/install.sh | sh

# macOS
brew install ollama
```

### 2. Pull a Model

```bash
# Recommended: Mistral 7B (fast, high quality)
ollama pull mistral

# Alternative: Llama 2 7B
ollama pull llama2

# For better quality (requires more RAM)
ollama pull llama2:13b
```

### 3. Configure Environment

```bash
# .env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:7b-instruct
```

### 4. Generate Your First Script

```python
from src.services.script_generator import ScriptGenerator, ScriptConfig, NicheType

# Initialize generator
generator = ScriptGenerator()

# Configure script
config = ScriptConfig(
    duration_minutes=5,
    niche=NicheType.MEDITATION,
    tone="calm and soothing",
    target_audience="beginners"
)

# Generate
script = await generator.generate(
    topic="Morning Mindfulness Practice",
    config=config
)

print(script.title)
print(script.script)
```

---

## Content Niches

### 1. 🧘 Meditation

**Purpose**: Guided meditation and mindfulness content  
**Style**: Calm, soothing, with breathing cues and pauses  
**Temperature**: 0.6 (low variance for consistency)  
**Best For**: Relaxation, sleep, stress relief videos

**Example Topics**:
- "10-Minute Morning Meditation"
- "Body Scan for Deep Relaxation"
- "Breathing Exercises for Anxiety"

---

### 2. 💪 Motivation

**Purpose**: Inspirational and empowering content  
**Style**: Energetic, storytelling, strong call-to-action  
**Temperature**: 0.8 (creative and varied)  
**Best For**: Personal development, success stories, life advice

**Example Topics**:
- "The Power of Daily Habits"
- "Overcoming Fear of Failure"
- "Why Consistency Beats Talent"

---

### 3. 📚 Facts

**Purpose**: Informative, educational fact-based content  
**Style**: Clear, numbered points, engaging explanations  
**Temperature**: 0.7 (balanced)  
**Best For**: "Top 10" videos, trivia, educational shorts

**Example Topics**:
- "10 Mind-Blowing Space Facts"
- "5 Historical Events That Changed Everything"
- "7 Psychology Facts About Human Behavior"

---

### 4. 📖 Stories

**Purpose**: Narrative-driven, emotional storytelling  
**Style**: Vivid descriptions, character development, dramatic arc  
**Temperature**: 0.85 (highly creative)  
**Best For**: Fictional stories, historical narratives, parables

**Example Topics**:
- "The Last Man on Mars"
- "A Stranger's Kindness Changed My Life"
- "The Mystery of the Abandoned Lighthouse"

---

### 5. 🎓 Education

**Purpose**: Teaching and explaining complex topics  
**Style**: Structured, clear examples, step-by-step breakdowns  
**Temperature**: 0.65 (precise and clear)  
**Best For**: Tutorials, explainers, how-to videos

**Example Topics**:
- "Understanding Quantum Physics for Beginners"
- "How the Stock Market Actually Works"
- "The Science Behind Sleep"

---

### 6. 💻 Tech

**Purpose**: Technology and programming explanations  
**Style**: Accessible, uses analogies, avoids jargon  
**Temperature**: 0.7 (clear but engaging)  
**Best For**: Tech news, coding tutorials, gadget reviews

**Example Topics**:
- "What is Blockchain? Explained Simply"
- "AI vs Machine Learning: What's the Difference?"
- "5 Coding Principles Every Developer Should Know"

---

### 7. 💰 Finance

**Purpose**: Financial education and money management  
**Style**: Authoritative, includes disclaimers, practical examples  
**Temperature**: 0.65 (precise and responsible)  
**Best For**: Investing basics, budgeting, financial literacy

**Example Topics**:
- "How to Start Investing with $100"
- "Understanding Compound Interest"
- "5 Common Money Mistakes to Avoid"

**⚠️ Note**: Automatically adds "not financial advice" disclaimers

---

### 8. 🏥 Health

**Purpose**: Health information and wellness tips  
**Style**: Evidence-based, clear warnings, includes disclaimers  
**Temperature**: 0.6 (accurate and careful)  
**Best For**: Wellness tips, exercise guides, health awareness

**Example Topics**:
- "Benefits of Morning Exercise"
- "Understanding Sleep Cycles"
- "5 Foods That Boost Brain Health"

**⚠️ Note**: Automatically validates for medical disclaimers

---

### 9. 🤔 Philosophy

**Purpose**: Philosophical concepts and life wisdom  
**Style**: Contemplative, thought-provoking, accessible  
**Temperature**: 0.75 (balanced depth and clarity)  
**Best For**: Stoicism, ethics, existential questions

**Example Topics**:
- "The Stoic Approach to Modern Life"
- "What Makes a Life Meaningful?"
- "The Philosophy of Happiness"

---

### 10. 📜 History

**Purpose**: Historical events and figures  
**Style**: Narrative-driven, contextual, engaging storytelling  
**Temperature**: 0.7 (accurate but engaging)  
**Best For**: Historical deep-dives, biographies, "what if" scenarios

**Example Topics**:
- "The Fall of the Roman Empire Explained"
- "How World War II Changed Technology"
- "The Life of Leonardo da Vinci"

---

## Configuration

### ScriptConfig Options

```python
from src.services.script_generator import ScriptConfig, NicheType

config = ScriptConfig(
    # Content Settings
    duration_minutes=5,              # Target video length (3-15 recommended)
    niche=NicheType.MEDITATION,     # Content type
    tone="calm and soothing",        # Writing style
    target_audience="beginners",     # Audience description
    
    # AI Settings
    model="mistral",                 # Ollama model name
    temperature=0.7,                 # Creativity (0.0-1.0)
    max_tokens=2048,                # Max generation length
    max_retries=3,                   # Retry on failure
    
    # Validation Settings
    validate=True,                   # Enable quality checks
    min_quality_score=0.7,          # Minimum acceptable quality (0.0-1.0)
    
    # Cache Settings
    cache_enabled=True,              # Use Redis caching
    cache_ttl=3600,                 # Cache lifetime (seconds)
)
```

### Environment Variables

```bash
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:7b-instruct

# Script Generation
SCRIPT_CACHE_ENABLED=true
SCRIPT_CACHE_TTL=3600
SCRIPT_MIN_QUALITY_SCORE=0.7
SCRIPT_VALIDATE=true
```

---

## Usage Examples

### Basic Generation

```python
generator = ScriptGenerator()

config = ScriptConfig(
    duration_minutes=5,
    niche=NicheType.FACTS,
    tone="engaging and educational",
    target_audience="general audience"
)

script = await generator.generate(
    topic="10 Amazing Space Facts",
    config=config
)
```

### Batch Generation

```python
topics = [
    "The Power of Gratitude",
    "Building Better Habits",
    "Overcoming Procrastination"
]

config = ScriptConfig(
    duration_minutes=4,
    niche=NicheType.MOTIVATION
)

scripts = await generator.generate_batch(topics, config)
```

### Regeneration with Feedback

```python
# Generate initial version
script_v1 = await generator.generate("Morning Routine", config)

# Improve based on feedback
feedback = "Add more practical examples and make the tone more energetic"
script_v2 = await generator.regenerate_with_feedback(
    script_v1.script,
    feedback,
    config
)
```

### Custom Ollama Configuration

```python
ollama_config = OllamaConfig(
    host="localhost",
    port=11434,
    model="llama2:13b",
    default_temperature=0.85,
    timeout=120
)

generator = ScriptGenerator(ollama_config=ollama_config)
```

---

## Validation System

### Quality Checks

1. **Length Validation**
   - Minimum: 100 words
   - Maximum: 5000 words
   - Duration-based targets

2. **Content Safety**
   - Profanity detection
   - Hate speech patterns
   - Inappropriate content filtering

3. **Compliance**
   - Medical advice disclaimers (health niche)
   - Financial advice warnings (finance niche)
   - Copyright pattern detection
   - Personal information checks

4. **Quality Scoring** (0.0 - 1.0)
   - Vocabulary diversity (30%+ unique words)
   - Sentence completeness (70%+ complete sentences)
   - Readability and flow
   - Structure and coherence

### Validation Result

```python
{
    "is_valid": true,
    "score": 0.85,
    "issues": [],
    "warnings": ["Consider adding more transitions"],
    "suggestions": ["Expand the conclusion section"],
    "word_count": 750,
    "estimated_duration": 300.0  # seconds
}
```

### Speaking Pace

- **Slow**: 120 WPM (meditation, educational)
- **Normal**: 150 WPM (most content)
- **Fast**: 180 WPM (energetic, motivational)

---

## API Reference

### ScriptGenerator

```python
class ScriptGenerator:
    async def generate(
        topic: str,
        config: ScriptConfig,
        additional_context: Optional[str] = None
    ) -> GeneratedScript
    
    async def generate_batch(
        topics: List[str],
        config: ScriptConfig
    ) -> List[GeneratedScript]
    
    async def regenerate_with_feedback(
        original_script: str,
        feedback: str,
        config: ScriptConfig
    ) -> GeneratedScript
```

### GeneratedScript Model

```python
{
    "id": "uuid",
    "niche": "meditation",
    "title": "10-Minute Morning Mindfulness",
    "script": "Welcome to this peaceful morning meditation...",
    "hook": "Start your day with clarity and calm...",
    "call_to_action": "Subscribe for daily mindfulness practices",
    "word_count": 750,
    "estimated_duration": 300.0,
    "generated_at": "2025-01-31T12:00:00Z",
    "model_used": "mistral",
    "temperature": 0.7,
    "prompt_tokens": 156,
    "validation": { ... },
    "quality_score": 0.85,
    "tags": ["meditation", "mindfulness", "morning"],
    "keywords": ["peace", "breath", "awareness", "calm"]
}
```

---

## Ollama Setup

### Installation

**Windows**:
```powershell
winget install Ollama.Ollama
```

**Linux**:
```bash
curl https://ollama.ai/install.sh | sh
```

**macOS**:
```bash
brew install ollama
```

### Starting the Service

```bash
# Start Ollama server
ollama serve

# Verify it's running
curl http://localhost:11434/api/health
```

### Model Management

```bash
# List installed models
ollama list

# Pull a new model
ollama pull mistral
ollama pull llama2
ollama pull codellama

# Remove a model
ollama rm <model-name>

# Get model info
ollama show mistral
```

### Recommended Models

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **mistral:7b-instruct** | 4.1GB | Fast | High | General use (recommended) |
| llama2:7b | 3.8GB | Fast | Good | Alternative |
| llama2:13b | 7.3GB | Medium | Excellent | High quality needs |
| llama2:70b | 39GB | Slow | Superior | Maximum quality |

### Hardware Requirements

- **Minimum**: 8GB RAM, CPU-only (slow)
- **Recommended**: 16GB RAM, NVIDIA GPU (4GB VRAM)
- **Optimal**: 32GB RAM, NVIDIA GPU (8GB+ VRAM)

---

## Troubleshooting

### Ollama Not Responding

**Problem**: `Connection refused` or timeout errors

**Solution**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/health

# Start the service
ollama serve

# Check firewall (Windows)
netsh advfirewall firewall add rule name="Ollama" dir=in action=allow protocol=TCP localport=11434
```

---

### Model Not Found

**Problem**: `Model 'mistral' not found`

**Solution**:
```bash
# List installed models
ollama list

# Pull the missing model
ollama pull mistral

# Verify installation
ollama list
```

---

### Slow Generation

**Problem**: Script generation takes too long (>60s)

**Solution**:
1. Use a smaller model (7B instead of 13B)
2. Reduce `max_tokens` in config
3. Enable GPU acceleration:
   ```bash
   # Check GPU detection
   ollama list
   # Should show GPU info
   ```
4. Reduce `duration_minutes` (less content = faster)

---

### Low Quality Scores

**Problem**: Scripts consistently score below 0.7

**Solution**:
1. Adjust temperature (0.7-0.8 for most niches)
2. Provide more specific topics
3. Add `additional_context` to guide generation
4. Use a larger model (13B or 70B)
5. Try regeneration with feedback

---

### Cache Not Working

**Problem**: Duplicate generations not using cache

**Solution**:
```python
# Check Redis connection
from src.utils.cache import CacheManager
cache = CacheManager()
await cache.set("test", "value")
result = await cache.get("test")  # Should return "value"

# Verify cache config
config = ScriptConfig(cache_enabled=True, cache_ttl=3600)
```

---

### Validation Failures

**Problem**: Scripts fail validation unexpectedly

**Solution**:
```python
# Check validation details
script = await generator.generate(topic, config)
print(script.validation)

# Lower quality threshold temporarily
config = ScriptConfig(min_quality_score=0.6)

# Disable validation for testing
config = ScriptConfig(validate=False)
```

---

## Performance Tips

### 1. Use Caching Aggressively

```python
# Cache common topics for 24 hours
config = ScriptConfig(
    cache_enabled=True,
    cache_ttl=86400  # 24 hours
)
```

**Impact**: 50-100x faster for repeated topics

---

### 2. Batch Similar Requests

```python
# Generate series in parallel
topics = ["Part 1: Intro", "Part 2: Deep Dive", "Part 3: Advanced"]
scripts = await generator.generate_batch(topics, config)
```

**Impact**: 3x faster than sequential

---

### 3. Choose the Right Model

```python
# For speed: 7B models
config = ScriptConfig(model="mistral")

# For quality: 13B models (if you have RAM)
config = ScriptConfig(model="llama2:13b")
```

**Impact**: 7B = 2-5s/script, 13B = 8-15s/script

---

### 4. Optimize Temperature

```python
# Lower for consistency (facts, education)
config = ScriptConfig(temperature=0.6)

# Higher for creativity (stories, motivation)
config = ScriptConfig(temperature=0.85)
```

**Impact**: Better first-try quality, fewer regenerations

---

### 5. Reduce Max Tokens

```python
# Short videos
config = ScriptConfig(
    duration_minutes=3,
    max_tokens=1500  # Less generation time
)
```

**Impact**: Faster generation for shorter content

---

### 6. Pre-warm Models

```bash
# Load model into memory before use
ollama run mistral "test" --no-input
```

**Impact**: Eliminates first-request cold start (2-5s)

---

## Production Deployment

### 1. Resource Planning

**Single Instance**:
- CPU: 4+ cores
- RAM: 16GB minimum (8GB for Ollama, 8GB for OS/app)
- Storage: 20GB for models + app
- GPU (optional): NVIDIA with 4GB+ VRAM

**High Availability**:
- Load balancer → Multiple Ollama instances
- Redis for shared caching
- Queue system (Celery) for batch jobs

---

### 2. Monitoring

```python
# Track generation metrics
import time

start = time.time()
script = await generator.generate(topic, config)
duration = time.time() - start

# Log metrics
logger.info(f"Generated {script.word_count} words in {duration:.2f}s")
logger.info(f"Quality: {script.quality_score:.2f}")
```

**Key Metrics**:
- Generation time (p50, p95, p99)
- Quality scores distribution
- Cache hit rate
- Validation failure rate

---

### 3. Error Handling

```python
try:
    script = await generator.generate(topic, config)
except OllamaConnectionError:
    # Fallback to queue or retry
    await celery_app.send_task("generate_script", args=[topic, config])
except ValidationError as e:
    # Log for review
    logger.error(f"Validation failed: {e.issues}")
    # Optionally regenerate with adjusted config
```

---

### 4. Rate Limiting

```python
from asyncio import Semaphore

# Limit concurrent generations
semaphore = Semaphore(5)  # Max 5 at once

async def generate_with_limit(topic, config):
    async with semaphore:
        return await generator.generate(topic, config)
```

---

### 5. Quality Assurance

```python
# Auto-flag low quality for human review
if script.quality_score < 0.75:
    await send_to_review_queue(script)

# A/B test different configs
configs = [
    ScriptConfig(temperature=0.7),
    ScriptConfig(temperature=0.8),
]
results = await compare_configs(topic, configs)
```

---

### 6. Backup Strategy

```python
# Save all generations to database
await db.scripts.insert_one(script.dict())

# Export high-quality scripts
if script.quality_score >= 0.85:
    await export_to_content_library(script)
```

---

## Best Practices

### ✅ Do

- Use caching for repeated topics
- Validate all generated content
- Monitor quality scores over time
- Provide specific, focused topics
- Use niche-appropriate temperatures
- Test with your audience before bulk generation
- Keep Ollama updated (`ollama pull <model>`)

### ❌ Don't

- Generate without validation in production
- Use very low temperatures (<0.5) for creative content
- Ignore quality warnings
- Generate very long scripts (>15 minutes)
- Run Ollama on underpowered hardware
- Share API keys or sensitive config in scripts
- Forget to handle errors gracefully

---

## Support

For issues and questions:

1. Check this documentation
2. Review examples in `examples/script_generator_usage.py`
3. Check logs for detailed error messages
4. Verify Ollama is running and models are installed
5. Test with simpler topics first

---

## License

Part of the Faceless YouTube project. See LICENSE for details.
