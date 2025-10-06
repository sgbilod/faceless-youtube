# Quick Start Guide: AI Integrations

## Claude Pro + Gemini Pro + Grok

**Version**: 1.0  
**Last Updated**: 2025-05-31

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [API Key Setup](#api-key-setup)
3. [Installation](#installation)
4. [Claude Pro Examples](#claude-pro-examples)
5. [Gemini Pro Examples](#gemini-pro-examples)
6. [Grok Examples](#grok-examples)
7. [MCP Server Setup](#mcp-server-setup)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Python Environment

- Python 3.13+
- Virtual environment activated

### Required Packages

```bash
pip install anthropic google-generativeai httpx aiofiles pillow opencv-python
```

### API Keys

You'll need to sign up for:

1. **Anthropic Claude Pro**: https://console.anthropic.com/
2. **Google Gemini Pro**: https://makersuite.google.com/app/apikey
3. **xAI Grok**: https://x.ai/api

---

## API Key Setup

### 1. Update .env File

```bash
# Copy example to .env
cp .env.example .env

# Edit .env with your keys
nano .env
```

### 2. Add Your API Keys

```bash
# Anthropic Claude Pro
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE

# Google Gemini Pro
GOOGLE_API_KEY=AIzaSyYOUR_KEY_HERE

# xAI Grok
XAI_API_KEY=xai-YOUR_KEY_HERE
```

### 3. Verify Setup

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Check API keys are loaded
assert os.getenv("ANTHROPIC_API_KEY"), "Missing ANTHROPIC_API_KEY"
assert os.getenv("GOOGLE_API_KEY"), "Missing GOOGLE_API_KEY"
assert os.getenv("XAI_API_KEY"), "Missing XAI_API_KEY"

print("✅ All API keys configured!")
```

---

## Installation

### Install Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Or install individually
pip install anthropic>=0.18.0
pip install google-generativeai>=0.4.0
pip install httpx>=0.25.2
```

### Verify Installation

```python
# Test imports
from src.services.ai_integration import ClaudeClient, GeminiClient, GrokClient

print("✅ All AI integrations imported successfully!")
```

---

## Claude Pro Examples

### Basic Usage

#### 1. Simple Message

```python
import asyncio
from src.services.ai_integration import ClaudeClient

async def main():
    client = ClaudeClient()

    response = await client.send_message_async(
        message="Explain quantum computing in simple terms.",
        system_prompt="You are a helpful science educator."
    )

    print(response.content)
    print(f"Tokens used: {response.tokens_used}")
    print(f"Latency: {response.latency_seconds:.2f}s")

asyncio.run(main())
```

#### 2. Architecture Analysis

```python
async def analyze_project():
    client = ClaudeClient()

    architecture_description = """
    Our video generation platform uses:
    - FastAPI backend with async workers
    - PostgreSQL for data storage
    - Redis for job queue
    - Multiple AI services (Claude, Gemini, Grok)
    - Kubernetes for deployment
    """

    analysis = await client.analyze_architecture(architecture_description)
    print(analysis)

asyncio.run(analyze_project())
```

**Expected Output**:

```
Architecture Analysis:
1. Strengths:
   - Async-first design for high concurrency
   - Separation of concerns with job queue
   - Scalable with Kubernetes

2. Potential Bottlenecks:
   - AI service rate limits may cause queuing
   - PostgreSQL could be bottleneck for high writes

3. Recommendations:
   - Implement caching layer for repeated AI requests
   - Consider read replicas for PostgreSQL
   - Add circuit breakers for external API calls
```

#### 3. Code Review

```python
async def review_code():
    client = ClaudeClient()

    code_snippet = """
    def generate_video(topic, duration):
        script = generate_script(topic)
        assets = fetch_assets(script)
        video = assemble_video(assets)
        return video
    """

    review = await client.review_code(
        code=code_snippet,
        context="Video generation pipeline"
    )
    print(review)

asyncio.run(review_code())
```

#### 4. Streaming Response

```python
async def stream_example():
    client = ClaudeClient()

    print("Claude's response:")
    print("-" * 50)

    async for chunk in client.stream_message(
        message="Write a detailed technical blog post about async Python."
    ):
        print(chunk, end="", flush=True)

    print("\n" + "-" * 50)

asyncio.run(stream_example())
```

#### 5. Conversation with History

```python
async def conversation():
    client = ClaudeClient()

    # First message
    response1 = await client.send_message_async(
        message="I'm building a video automation platform.",
        use_history=True
    )
    print("Claude:", response1.content[:200])

    # Follow-up (with context)
    response2 = await client.send_message_async(
        message="What's the best way to handle long video rendering times?",
        use_history=True  # Uses conversation history
    )
    print("Claude:", response2.content[:200])

    # View history
    print(f"\nConversation history: {len(client.conversation_history)} messages")

asyncio.run(conversation())
```

---

## Gemini Pro Examples

### Basic Usage

#### 1. Text Generation

```python
import asyncio
from src.services.ai_integration import GeminiClient

async def main():
    client = GeminiClient()

    response = await client.generate_content_async(
        prompt="Write a 30-second meditation script about ocean waves."
    )

    print(response.content)
    print(f"Safety ratings: {response.safety_ratings}")
    print(f"Latency: {response.latency_seconds:.2f}s")

asyncio.run(main())
```

#### 2. Image Analysis

```python
async def analyze_thumbnail():
    client = GeminiClient()

    # Analyze image for meditation video suitability
    analysis = await client.analyze_image(
        image_path="thumbnail.jpg",
        analysis_type="suitability"
    )

    print(f"Description: {analysis.description}")
    print(f"Mood: {analysis.mood}")
    print(f"Suitability Score: {analysis.suitability_score}/1.0")
    print(f"Recommendations: {', '.join(analysis.recommendations)}")

asyncio.run(analyze_thumbnail())
```

#### 3. Multimodal Input (Text + Image)

```python
async def multimodal_example():
    client = GeminiClient()

    response = await client.generate_content_async(
        prompt="What emotions does this image evoke? Rate it for a meditation video.",
        image_path="nature_scene.jpg"
    )

    print(response.content)

asyncio.run(multimodal_example())
```

#### 4. Thumbnail Prompt Generation

```python
async def generate_thumbnail_prompt():
    client = GeminiClient()

    prompt = await client.generate_thumbnail_prompt(
        video_title="10 Minute Morning Meditation",
        video_description="Start your day with peaceful meditation and deep breathing",
        niche="meditation"
    )

    print("Thumbnail Generation Prompt:")
    print("-" * 50)
    print(prompt)

asyncio.run(generate_thumbnail_prompt())
```

**Expected Output**:

```
Thumbnail Generation Prompt:
--------------------------------------------------
Create a serene meditation thumbnail with:

Visual Elements:
- Peaceful sunrise over calm water
- Soft, warm color palette (oranges, purples, pinks)
- Minimalist composition with negative space
- Person in meditation pose (silhouette, back view)

Text Overlay:
- "10 MIN" in large, clear font (top right)
- "Morning Meditation" below in elegant script
- Subtle glow effect on text

Color Scheme:
- Primary: Warm orange/gold (#FF9E5A)
- Secondary: Soft purple (#B794F6)
- Accent: White with subtle glow

Composition:
- Rule of thirds: person in left third, text in right
- Breathing room around elements
- Eye-catching but not overwhelming

Emotional Appeal:
- Calmness, peace, new beginnings
- Aspirational but accessible
- Inviting and warm
```

#### 5. SEO Optimization

```python
async def optimize_seo():
    client = GeminiClient()

    seo_result = await client.optimize_seo(
        title="Meditation Video",
        description="A calming meditation video",
        niche="meditation"
    )

    print("Optimized Title:", seo_result["optimized_title"])
    print("Optimized Description:", seo_result["optimized_description"])
    print("Tags:", ", ".join(seo_result["tags"]))
    print("\nRecommendations:")
    print(seo_result["recommendations"])

asyncio.run(optimize_seo())
```

#### 6. Asset Categorization

```python
async def categorize_assets():
    client = GeminiClient()

    # Categorize a video asset
    categorization = await client.categorize_asset(
        asset_path="assets/videos/nature_scene.mp4",
        asset_type="video"
    )

    print(f"Primary Category: {categorization['primary_category']}")
    print(f"Tags: {', '.join(categorization['tags'])}")
    print(f"Suitable Niches: {', '.join(categorization['suitable_niches'])}")
    print(f"Mood: {categorization['mood']}")
    print(f"Confidence: {categorization['confidence']*100:.1f}%")

asyncio.run(categorize_assets())
```

---

## Grok Examples

### Basic Usage

#### 1. Get Trending Topics

```python
import asyncio
from src.services.ai_integration import GrokClient

async def main():
    async with GrokClient() as client:
        topics = await client.get_trending_topics(
            niche="meditation",
            region="US",
            limit=5
        )

        for topic in topics:
            print(f"\n📈 {topic.topic}")
            print(f"   Trend Score: {topic.trend_score}/1.0")
            print(f"   Competition: {topic.estimated_competition}")
            print(f"   Keywords: {', '.join(topic.keywords)}")
            print(f"   Video Angles:")
            for angle in topic.suggested_video_angles:
                print(f"      • {angle}")

asyncio.run(main())
```

**Expected Output**:

```
📈 10-Minute Morning Meditation
   Trend Score: 0.85/1.0
   Competition: medium
   Keywords: morning, meditation, mindfulness, routine
   Video Angles:
      • Beginner-friendly morning routine
      • Quick meditation for busy professionals
      • Energizing breathwork session

📈 Sleep Meditation for Anxiety Relief
   Trend Score: 0.78/1.0
   Competition: high
   Keywords: sleep, anxiety, stress relief, insomnia
   Video Angles:
      • Science-backed sleep techniques
      • ASMR-enhanced sleep meditation
      • 8-hour deep sleep music
```

#### 2. Analyze Viral Potential

```python
async def analyze_viral_potential():
    async with GrokClient() as client:
        analysis = await client.analyze_viral_potential(
            video_title="10-Minute Morning Meditation for Anxiety Relief",
            video_description="Start your day calm and focused with guided meditation",
            niche="meditation"
        )

        print(f"Viral Score: {analysis['viral_score']}/100")
        print(f"Optimal Post Time: {analysis['optimal_post_time']}")
        print("\nAnalysis:")
        print(analysis['analysis'])

asyncio.run(analyze_viral_potential())
```

#### 3. Detect Emerging Niches

```python
async def find_opportunities():
    async with GrokClient() as client:
        emerging = await client.detect_emerging_niches(
            broad_category="wellness"
        )

        for niche in emerging:
            print(f"\n🚀 {niche['niche']}")
            print(f"   Opportunity Score: {niche['opportunity_score']}/100")
            print(f"\n   Analysis: {niche['analysis'][:200]}...")

asyncio.run(find_opportunities())
```

#### 4. Competitor Analysis

```python
async def analyze_competitors():
    async with GrokClient() as client:
        analysis = await client.analyze_competitor_trends(
            competitor_channels=[
                "Headspace",
                "Calm",
                "Great Meditation"
            ],
            niche="meditation"
        )

        print("Competitor Strategies:")
        print(analysis['competitor_strategies'][:500])
        print("\n\nContent Gaps:")
        for gap in analysis['content_gaps']:
            print(f"  • {gap}")

asyncio.run(analyze_competitors())
```

#### 5. Predict Best Posting Time

```python
async def find_best_time():
    async with GrokClient() as client:
        timing = await client.predict_best_posting_time(
            niche="meditation",
            target_audience="busy professionals, 25-45 years old",
            video_type="guided meditation"
        )

        print(f"Optimal Time: {timing['optimal_time']}")
        print("\nAlternative Times:")
        for alt_time in timing['alternatives']:
            print(f"  • {alt_time}")
        print("\nReasoning:")
        print(timing['reasoning'][:300])

asyncio.run(find_best_time())
```

#### 6. Current Event Integration

```python
async def event_based_content():
    async with GrokClient() as client:
        concept = await client.generate_current_event_angle(
            niche="meditation",
            event_type="trending"
        )

        print("Timely Video Concept:")
        print("-" * 50)
        print(concept)

asyncio.run(event_based_content())
```

#### 7. Search Trend Analysis

```python
async def analyze_trends():
    async with GrokClient() as client:
        trends = await client.analyze_search_trends(
            keywords=["morning meditation", "sleep meditation", "anxiety relief"],
            timeframe="30d"
        )

        print(f"Trend Direction: {trends['trend_direction']}")
        print("\nAnalysis:")
        print(trends['analysis'][:500])
        print("\n\nRecommended Keywords:")
        for keyword in trends['recommended_keywords']:
            print(f"  • {keyword}")

asyncio.run(analyze_trends())
```

---

## MCP Server Setup

### Configure Claude Desktop

#### 1. Edit Claude Desktop Config

**Location**:

- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "youtube-analytics": {
      "command": "python",
      "args": [
        "C:/FacelessYouTube/src/mcp_servers/youtube_analytics_server.py"
      ],
      "env": {
        "PYTHONPATH": "C:/FacelessYouTube"
      }
    },
    "video-pipeline": {
      "command": "python",
      "args": ["C:/FacelessYouTube/src/mcp_servers/video_pipeline_server.py"],
      "env": {
        "PYTHONPATH": "C:/FacelessYouTube"
      }
    }
  }
}
```

#### 2. Restart Claude Desktop

#### 3. Test MCP Servers

In Claude Desktop, ask:

```
Can you show me the available MCP resources?
```

Claude should respond with:

```
I can see the following resources:
- YouTube Analytics (youtube-analytics)
- Video Pipeline (video-pipeline)

Would you like me to query any of these?
```

#### 4. Query YouTube Analytics

```
Show me the performance metrics for my top 5 videos
```

#### 5. Generate Video with AI

```
Create a new video about "morning meditation routine"
with 60 second duration using the video pipeline
```

---

## Best Practices

### 1. API Key Security

```python
# ✅ GOOD: Load from environment
import os
api_key = os.getenv("ANTHROPIC_API_KEY")

# ❌ BAD: Hardcode in code
api_key = "sk-ant-api03-..."  # Never do this!
```

### 2. Error Handling

```python
import logging

async def safe_ai_call():
    client = ClaudeClient()

    try:
        response = await client.send_message_async("Hello!")
        return response.content
    except Exception as e:
        logging.error(f"AI call failed: {e}")
        # Fallback to simpler method or return error
        return "Sorry, AI service unavailable."
```

### 3. Rate Limiting

```python
import asyncio

async def batch_requests(prompts):
    client = ClaudeClient()

    results = []
    for prompt in prompts:
        response = await client.send_message_async(prompt)
        results.append(response.content)

        # Rate limit: wait 1 second between requests
        await asyncio.sleep(1)

    return results
```

### 4. Cost Optimization

```python
# Cache expensive AI calls
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_ai_call(prompt: str):
    # Only call AI if not in cache
    client = ClaudeClient()
    response = client.send_message(prompt)
    return response.content
```

### 5. Async Context Managers

```python
# ✅ GOOD: Use async context manager for Grok
async with GrokClient() as client:
    response = await client.send_message("Hello")

# ❌ BAD: Forget to close connection
client = GrokClient()
response = await client.send_message("Hello")
# Connection never closed!
```

---

## Troubleshooting

### Issue 1: ImportError

```
ImportError: cannot import name 'ClaudeClient'
```

**Solution**:

```bash
# Ensure you're in project root
cd c:/FacelessYouTube

# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or in Windows PowerShell
$env:PYTHONPATH="C:\FacelessYouTube"
```

### Issue 2: API Key Not Found

```
ValueError: Anthropic API key required
```

**Solution**:

```bash
# Check .env file exists
ls .env

# Verify key is set
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('ANTHROPIC_API_KEY'))"

# If empty, add to .env
echo "ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY" >> .env
```

### Issue 3: MCP Server Not Found

```
Claude Desktop: No MCP servers available
```

**Solution**:

1. Check config file location (Mac vs Windows)
2. Verify absolute paths in config
3. Test server manually:

```bash
python src/mcp_servers/youtube_analytics_server.py
```

4. Check logs: `~/Library/Logs/Claude/mcp-*.log`

### Issue 4: Rate Limit Exceeded

```
AnthropicError: rate_limit_exceeded
```

**Solution**:

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def rate_limited_call():
    client = ClaudeClient()
    return await client.send_message_async("Hello")
```

### Issue 5: Image Analysis Fails

```
PIL.UnidentifiedImageError: cannot identify image file
```

**Solution**:

```python
from PIL import Image

# Verify image is valid
try:
    img = Image.open("thumbnail.jpg")
    img.verify()
    print(f"✅ Valid image: {img.size}, {img.format}")
except Exception as e:
    print(f"❌ Invalid image: {e}")
```

---

## Additional Resources

### Documentation

- **Anthropic Claude**: https://docs.anthropic.com/
- **Google Gemini**: https://ai.google.dev/docs
- **xAI Grok**: https://x.ai/api/docs
- **MCP Protocol**: https://modelcontextprotocol.io/

### Community

- **Claude Discord**: https://discord.gg/anthropic
- **Google AI Forum**: https://discuss.ai.google.dev/
- **GitHub Issues**: https://github.com/yourusername/FacelessYouTube/issues

### Support

- Email: support@doppelganger-studio.com
- Slack: #ai-integrations channel

---

**Last Updated**: 2025-05-31  
**Version**: 1.0  
**Maintained By**: Doppelganger Studio Team
