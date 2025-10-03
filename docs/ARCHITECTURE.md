# SYSTEM ARCHITECTURE

## Faceless YouTube Automation Platform v2.0

**Version:** 2.0.0  
**Last Updated:** October 3, 2025  
**Status:** Design Phase

---

## 📋 TABLE OF CONTENTS

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Technology Stack](#technology-stack)
4. [Microservices Architecture](#microservices-architecture)
5. [Database Design](#database-design)
6. [API Architecture](#api-architecture)
7. [Data Flow](#data-flow)
8. [Component Interactions](#component-interactions)
9. [Infrastructure](#infrastructure)
10. [Security Architecture](#security-architecture)
11. [Scalability Strategy](#scalability-strategy)
12. [Deployment Architecture](#deployment-architecture)

---

## 🎯 SYSTEM OVERVIEW

### Mission Statement

Transform faceless video content creation into a fully autonomous, AI-driven platform capable of generating, optimizing, and distributing high-engagement content across multiple platforms with 90%+ automation and zero daily human intervention.

### High-Level Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[Desktop UI - PyQt6]
        API[REST API - FastAPI]
    end

    subgraph "Application Layer"
        ContentGen[Content Generator Service]
        VideoRender[Video Renderer Service]
        AssetMgr[Asset Manager Service]
        ScriptGen[Script Generator Service]
        Publisher[Multi-Platform Publisher]
        Analytics[Analytics Service]
    end

    subgraph "AI/ML Layer"
        LLM[LLM Engine - Ollama/GPT4All]
        TTS[Voice Synthesis - Coqui/pyttsx3]
        CLIP[CLIP - Asset Intelligence]
        Classifier[Asset Classifier]
    end

    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL 15+)]
        MongoDB[(MongoDB 6+)]
        Redis[(Redis 7+)]
        VectorDB[(Vector DB)]
    end

    subgraph "External Services"
        YouTube[YouTube API]
        TikTok[TikTok API]
        Instagram[Instagram API]
        Pexels[Asset Sources]
    end

    UI --> API
    API --> ContentGen
    API --> Publisher
    ContentGen --> ScriptGen
    ContentGen --> AssetMgr
    ContentGen --> VideoRender
    ScriptGen --> LLM
    VideoRender --> TTS
    AssetMgr --> CLIP
    AssetMgr --> Classifier
    ContentGen --> PostgreSQL
    AssetMgr --> MongoDB
    API --> Redis
    Publisher --> YouTube
    Publisher --> TikTok
    Publisher --> Instagram
    AssetMgr --> Pexels
    Analytics --> PostgreSQL
```

### System Capabilities

**Current (v1.0):**

- ✅ Desktop UI for video generation
- ✅ Basic script input
- ✅ gTTS voice synthesis
- ✅ Manual asset selection (JSON)
- ✅ YouTube upload
- ✅ Basic analytics

**Target (v2.0):**

- 🎯 AI-driven script generation (Ollama/GPT4All)
- 🎯 Automated asset discovery (10+ scrapers)
- 🎯 Intelligent asset selection (CLIP + ML)
- 🎯 Multi-platform publishing (8+ platforms)
- 🎯 Advanced analytics & optimization
- 🎯 Revenue tracking & forecasting
- 🎯 Affiliate link integration
- 🎯 SEO optimization
- 🎯 Scheduled automation
- 🎯 A/B testing framework

---

## 🏛️ ARCHITECTURE PRINCIPLES

### 1. Microservices First

- **Single Responsibility:** Each service owns one domain
- **Loose Coupling:** Services communicate via APIs/events
- **Independent Deployment:** Update services without downtime
- **Technology Agnostic:** Best tool for each service

### 2. Local-First Development

- **Cost Optimization:** Prefer local/free over cloud/paid
- **Offline Capable:** Core features work without internet
- **Privacy:** Sensitive data stays local
- **Performance:** Reduce network latency

### 3. Data-Driven Decision Making

- **Metrics Everything:** Track every action
- **A/B Testing:** Validate assumptions
- **Performance Analytics:** Continuous optimization
- **Revenue Attribution:** Know what works

### 4. Security by Design

- **Encryption at Rest:** All credentials encrypted
- **Zero Trust:** Validate all inputs
- **Least Privilege:** Minimal permissions
- **Audit Logging:** Track all actions

### 5. Automation First

- **Zero Touch:** Goal is 90%+ automation
- **Self-Healing:** Automatic error recovery
- **Intelligent Scheduling:** Optimal posting times
- **Continuous Learning:** ML improves over time

---

## 🛠️ TECHNOLOGY STACK

### Core Technologies

| Layer             | Technology        | Version | Purpose             | Cost               |
| ----------------- | ----------------- | ------- | ------------------- | ------------------ |
| **UI**            | PyQt6             | 6.5+    | Desktop application | FREE               |
| **API**           | FastAPI           | 0.104+  | REST API framework  | FREE               |
| **Database**      | PostgreSQL        | 15+     | Relational data     | FREE               |
| **Cache**         | Redis             | 7+      | Caching layer       | FREE               |
| **NoSQL**         | MongoDB           | 6+      | Document storage    | FREE               |
| **Vector DB**     | Pinecone/Weaviate | Latest  | Embeddings          | FREE tier          |
| **Queue**         | Celery + Redis    | Latest  | Background tasks    | FREE               |
| **Container**     | Docker            | 24+     | Containerization    | FREE               |
| **Orchestration** | Docker Compose    | 2.23+   | Local orchestration | FREE               |
| **CI/CD**         | GitHub Actions    | -       | Automation          | FREE (2000 min/mo) |

### AI/ML Stack (Local-First)

| Component      | Primary (FREE)          | Fallback     | Premium (Paid) |
| -------------- | ----------------------- | ------------ | -------------- |
| **LLM**        | Ollama (Mistral/Llama2) | GPT4All      | GPT-4          |
| **Voice**      | Coqui TTS               | pyttsx3      | ElevenLabs     |
| **Vision**     | CLIP (OpenAI)           | Local models | GPT-4 Vision   |
| **Embeddings** | sentence-transformers   | word2vec     | OpenAI Ada     |

### Asset Sources (All FREE)

**Video:**

- Pexels, Pixabay, Videvo, Mixkit, Coverr, Unsplash, NASA, Internet Archive

**Audio:**

- YouTube Audio Library, Incompetech, Free Music Archive, Freesound, ccMixter

### Development Tools

```yaml
Language: Python 3.11+
Package Manager: pip
Virtual Environment: venv
Code Formatter: black
Linter: ruff
Type Checker: mypy
Testing: pytest + pytest-asyncio
Coverage: pytest-cov
Documentation: Sphinx + MkDocs
```

---

## 🏗️ MICROSERVICES ARCHITECTURE

### Service Portfolio

```mermaid
graph LR
    subgraph "Core Services"
        CG[Content Generator<br/>Port 8001]
        VR[Video Renderer<br/>Port 8002]
        AM[Asset Manager<br/>Port 8003]
    end

    subgraph "AI Services"
        SG[Script Generator<br/>Port 8004]
        VS[Voice Synthesizer<br/>Port 8005]
        AC[Asset Classifier<br/>Port 8006]
    end

    subgraph "Integration Services"
        MP[Multi-Platform Publisher<br/>Port 8007]
        AN[Analytics Service<br/>Port 8008]
        SC[Scheduler Service<br/>Port 8009]
    end

    subgraph "Support Services"
        NT[Notification Service<br/>Port 8010]
        LG[Logging Service<br/>Port 8011]
    end
```

### 1. Content Generator Service (Port 8001)

**Responsibility:** Orchestrate end-to-end video creation

```python
# src/services/content_generator/main.py

class ContentGeneratorService:
    """Main orchestrator for video creation pipeline."""

    async def generate_video(
        self,
        niche: str,
        duration: int,
        style: str,
        config: VideoConfig
    ) -> Video:
        """
        Full video generation pipeline.

        Steps:
        1. Generate script (via Script Generator)
        2. Fetch assets (via Asset Manager)
        3. Synthesize voice (via Voice Synthesizer)
        4. Render video (via Video Renderer)
        5. Optimize metadata (SEO, tags, description)
        6. Store in database
        """
        # Orchestration logic
        pass
```

**Dependencies:**

- Script Generator (8004)
- Asset Manager (8003)
- Voice Synthesizer (8005)
- Video Renderer (8002)

**Database:**

- PostgreSQL: `videos`, `video_metadata`
- MongoDB: `generation_logs`

---

### 2. Video Renderer Service (Port 8002)

**Responsibility:** Combine assets into final video

```python
# src/services/video_renderer/main.py

class VideoRendererService:
    """Render videos from assets + audio + effects."""

    async def render(
        self,
        script: Script,
        voice: AudioFile,
        assets: List[Asset],
        config: RenderConfig
    ) -> RenderedVideo:
        """
        Render pipeline:
        1. Timeline generation (sync assets to audio)
        2. Apply transitions (fade, slide, etc.)
        3. Add text overlays (animated captions)
        4. Apply color grading
        5. Add background music
        6. Encode final video (H.264, 1080p)
        """
        pass
```

**Tech Stack:**

- FFmpeg-python (video editing)
- Pillow (image manipulation)
- MoviePy (timeline management)

**Performance Target:**

- 10-min video: < 2 minutes rendering time
- Memory: < 2GB peak usage

---

### 3. Asset Manager Service (Port 8003)

**Responsibility:** Asset discovery, storage, classification

```python
# src/services/asset_manager/main.py

class AssetManagerService:
    """Manage asset library with AI classification."""

    async def search_assets(
        self,
        query: str,
        asset_type: AssetType,
        count: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Asset]:
        """
        Intelligent asset search:
        1. Semantic search using CLIP embeddings
        2. Filter by performance metrics
        3. Rank by composite score (relevance + performance)
        4. Return top N assets
        """
        pass

    async def scrape_sources(self):
        """
        Run scrapers for all asset sources:
        - Pexels, Pixabay, Videvo, Mixkit, Coverr
        - Unsplash, NASA, YouTube Audio Library
        - Incompetech, Free Music Archive
        """
        pass
```

**Features:**

- 10+ asset scrapers
- Perceptual hash deduplication
- CLIP-based classification
- Performance tracking

---

### 4. Script Generator Service (Port 8004)

**Responsibility:** AI-powered script generation

```python
# src/services/script_generator/main.py

class ScriptGeneratorService:
    """Generate scripts using local LLMs."""

    async def generate(
        self,
        niche: str,
        duration: int,
        style: str,
        keywords: List[str]
    ) -> Script:
        """
        Generate script with fallback providers:
        1. Try Ollama (Mistral-7B) - FREE, local
        2. Try GPT4All - FREE, offline
        3. Try GPT-3.5-turbo - CHEAP, cloud
        4. Try GPT-4 - EXPENSIVE, only if revenue > $500/mo
        """
        pass
```

**LLM Configuration:**

```yaml
# config/ai.yaml
llm:
  primary:
    provider: ollama
    model: mistral:7b-instruct
    host: localhost:11434
    temperature: 0.7
    max_tokens: 2000

  fallback:
    - provider: gpt4all
      model: mistral-7b-openorca.Q4_0.gguf
    - provider: openai
      model: gpt-3.5-turbo
      max_cost_per_request: 0.01 # $0.01 limit
```

---

### 5. Multi-Platform Publisher (Port 8007)

**Responsibility:** Publish to 8+ platforms

```python
# src/services/publisher/main.py

class MultiPlatformPublisher:
    """Publish videos to multiple platforms."""

    async def publish(
        self,
        video: Video,
        platforms: List[Platform],
        schedule: Optional[datetime] = None
    ) -> PublishResults:
        """
        Publish workflow:
        1. Optimize video for each platform (resolution, aspect ratio)
        2. Generate platform-specific metadata
        3. Upload to platforms (concurrent)
        4. Track publish status
        5. Monitor initial performance
        """
        pass
```

**Supported Platforms:**

- YouTube (primary)
- TikTok
- Instagram Reels
- YouTube Shorts
- LinkedIn
- Twitter
- Pinterest
- Snapchat Spotlight

---

### 6. Analytics Service (Port 8008)

**Responsibility:** Track performance & revenue

```python
# src/services/analytics/main.py

class AnalyticsService:
    """Track video performance and revenue."""

    async def fetch_metrics(
        self,
        video_id: str,
        platform: Platform
    ) -> VideoMetrics:
        """
        Fetch real-time metrics:
        - Views, watch time, engagement
        - CTR, subscriber growth
        - Revenue (ads, affiliates)
        """
        pass

    async def generate_insights(
        self,
        timeframe: str
    ) -> AnalyticsInsights:
        """
        AI-powered insights:
        - Best performing niches
        - Optimal posting times
        - Asset effectiveness
        - Revenue trends
        """
        pass
```

---

## 💾 DATABASE DESIGN

### PostgreSQL Schema (Relational Data)

```mermaid
erDiagram
    VIDEOS ||--o{ VIDEO_ASSETS : contains
    VIDEOS ||--o{ PUBLISHES : published_to
    VIDEOS ||--o{ ANALYTICS : tracked_by
    VIDEOS }o--|| SCRIPTS : generated_from
    ASSETS ||--o{ VIDEO_ASSETS : used_in
    ASSETS ||--o{ ASSET_TAGS : tagged_with
    PLATFORMS ||--o{ PUBLISHES : receives
    USERS ||--o{ VIDEOS : owns

    VIDEOS {
        int id PK
        int user_id FK
        int script_id FK
        string title
        text description
        int duration_seconds
        string resolution
        string file_path
        string thumbnail_path
        timestamp created_at
        timestamp updated_at
        json metadata
        string status
    }

    SCRIPTS {
        int id PK
        text content
        string niche
        string style
        int duration_seconds
        json keywords
        float ai_confidence
        string generator_model
        timestamp created_at
    }

    ASSETS {
        int id PK
        string asset_type
        string source_platform
        string file_path
        string thumbnail_path
        int width
        int height
        int duration_seconds
        string license_type
        json metadata
        string perceptual_hash
        float quality_score
        timestamp created_at
    }

    VIDEO_ASSETS {
        int id PK
        int video_id FK
        int asset_id FK
        float start_time
        float duration
        int order_index
        json effects
    }

    ASSET_TAGS {
        int id PK
        int asset_id FK
        string tag_name
        string tag_type
        float confidence
    }

    PUBLISHES {
        int id PK
        int video_id FK
        int platform_id FK
        string platform_video_id
        string status
        string url
        timestamp published_at
        json platform_metadata
    }

    ANALYTICS {
        int id PK
        int video_id FK
        int platform_id FK
        bigint views
        bigint likes
        bigint comments
        bigint shares
        float watch_time_minutes
        float ctr
        decimal revenue
        timestamp recorded_at
    }

    PLATFORMS {
        int id PK
        string name
        string api_version
        boolean enabled
        json credentials_encrypted
        json default_config
    }

    USERS {
        int id PK
        string username
        string email
        string password_hash
        json preferences
        timestamp created_at
    }
```

### MongoDB Collections (Unstructured Data)

```javascript
// Collection: generation_logs
{
  _id: ObjectId,
  video_id: int,
  timestamp: ISODate,
  stage: "script_generation" | "asset_fetch" | "rendering" | "publishing",
  status: "started" | "completed" | "failed",
  duration_ms: int,
  details: {
    // Stage-specific data
  },
  errors: []
}

// Collection: asset_embeddings
{
  _id: ObjectId,
  asset_id: int,
  embedding_model: "clip-vit-b-32",
  embedding_vector: [float],  // 512 dimensions for CLIP
  generated_at: ISODate
}

// Collection: script_templates
{
  _id: ObjectId,
  niche: string,
  template_name: string,
  structure: {
    intro: string,
    body: [string],
    conclusion: string
  },
  variables: [string],
  performance_score: float,
  usage_count: int
}

// Collection: platform_responses
{
  _id: ObjectId,
  publish_id: int,
  platform: string,
  response_data: object,  // Raw API response
  timestamp: ISODate
}
```

### Redis Cache Structure

```
# Cache Keys Pattern
video:{video_id}:metadata          TTL: 1 hour
asset:{asset_id}:details           TTL: 24 hours
script:generate:{hash}             TTL: 1 week
analytics:{video_id}:{platform}    TTL: 5 minutes
api:rate_limit:{service}:{key}     TTL: 1 minute
session:{user_id}                  TTL: 30 minutes

# Example Cache Entry
video:12345:metadata {
  "title": "10 Minute Deep Sleep Meditation",
  "duration": 600,
  "views": 15234,
  "cached_at": "2025-10-03T10:30:00Z"
}
```

---

## 🔗 API ARCHITECTURE

### REST API Design

**Base URL:** `http://localhost:8000/api/v1`

#### Endpoints

```yaml
# Video Generation
POST   /videos/generate
  Request:
    niche: string
    duration: int
    style: string
    config: object
  Response:
    video_id: int
    status: "queued"
    estimated_completion: datetime

GET    /videos/{video_id}
  Response:
    video: Video object
    analytics: VideoAnalytics
    publishes: [Publish]

# Asset Management
GET    /assets/search
  Query:
    q: string (search query)
    type: video|image|audio
    limit: int
  Response:
    assets: [Asset]
    total: int

POST   /assets/scrape
  Request:
    sources: [string]
    categories: [string]
  Response:
    task_id: string
    status: "started"

# Publishing
POST   /publish
  Request:
    video_id: int
    platforms: [string]
    schedule: datetime (optional)
  Response:
    publish_ids: [int]
    status: "scheduled" | "publishing"

# Analytics
GET    /analytics/videos/{video_id}
  Query:
    platform: string (optional)
    timeframe: string
  Response:
    metrics: VideoMetrics
    insights: AnalyticsInsights

GET    /analytics/summary
  Query:
    start_date: date
    end_date: date
  Response:
    total_views: int
    total_revenue: decimal
    top_videos: [Video]
    trends: object
```

### WebSocket API (Real-Time Updates)

```python
# WebSocket endpoint: ws://localhost:8000/ws/video/{video_id}

# Message types:
{
  "type": "progress",
  "stage": "rendering",
  "progress": 45.2,
  "message": "Applying transitions..."
}

{
  "type": "completed",
  "video_id": 12345,
  "file_path": "/output/video_12345.mp4"
}

{
  "type": "error",
  "stage": "voice_synthesis",
  "error": "API rate limit exceeded",
  "retry_after": 60
}
```

---

## 🔄 DATA FLOW

### Video Generation Flow

```mermaid
sequenceDiagram
    participant UI as Desktop UI
    participant API as FastAPI
    participant CG as Content Generator
    participant SG as Script Generator
    participant AM as Asset Manager
    participant VS as Voice Synthesizer
    participant VR as Video Renderer
    participant DB as PostgreSQL
    participant Cache as Redis

    UI->>API: POST /videos/generate
    API->>DB: Create video record
    API->>CG: Start generation pipeline
    API-->>UI: Return video_id + task_id

    CG->>SG: Generate script
    SG->>Cache: Check script cache
    Cache-->>SG: Cache miss
    SG->>SG: Generate with Ollama
    SG->>Cache: Store script
    SG-->>CG: Return script

    CG->>AM: Search assets
    AM->>Cache: Check asset cache
    AM->>DB: Query asset database
    AM->>AM: CLIP semantic search
    AM-->>CG: Return ranked assets

    par Parallel Processing
        CG->>VS: Synthesize voice
        VS->>VS: Generate with Coqui TTS
        VS-->>CG: Return audio file
    and
        CG->>AM: Download assets
        AM-->>CG: Return asset files
    end

    CG->>VR: Render video
    VR->>VR: FFmpeg processing
    VR-->>CG: Return rendered video

    CG->>DB: Update video record
    CG->>Cache: Cache video metadata
    CG-->>API: Generation complete
    API-->>UI: WebSocket: Video ready
```

### Asset Scraping Flow

```mermaid
sequenceDiagram
    participant Scheduler as Celery Scheduler
    participant AS as Asset Scraper
    participant Source as Asset Source (Pexels)
    participant DH as Deduplicator
    participant CL as CLIP Classifier
    participant DB as PostgreSQL

    Scheduler->>AS: Trigger weekly scrape
    AS->>Source: Fetch asset metadata
    Source-->>AS: Return JSON response

    loop For each asset
        AS->>AS: Parse metadata
        AS->>DH: Check for duplicates
        DH->>DB: Query perceptual hash
        alt Duplicate found
            DH-->>AS: Skip (duplicate)
        else New asset
            DH-->>AS: Proceed
            AS->>AS: Download asset file
            AS->>CL: Generate embeddings
            CL->>CL: CLIP encoding
            CL-->>AS: Return tags + embeddings
            AS->>DB: Insert asset + tags
        end
    end

    AS->>Scheduler: Report: 234 new assets
```

---

## 🧩 COMPONENT INTERACTIONS

### Service Communication Matrix

| From ↓ To →        | Content Gen | Video Renderer | Asset Manager | Script Gen | Publisher | Analytics |
| ------------------ | ----------- | -------------- | ------------- | ---------- | --------- | --------- |
| **Content Gen**    | -           | ✅ Sync        | ✅ Sync       | ✅ Sync    | ❌        | ❌        |
| **Video Renderer** | ✅ Callback | -              | ❌            | ❌         | ❌        | ❌        |
| **Asset Manager**  | ✅ Callback | ❌             | -             | ❌         | ❌        | ❌        |
| **Script Gen**     | ✅ Callback | ❌             | ❌            | -          | ❌        | ❌        |
| **Publisher**      | ❌          | ❌             | ❌            | ❌         | -         | ✅ Async  |
| **Analytics**      | ❌          | ❌             | ❌            | ❌         | ❌        | -         |

**Communication Patterns:**

- ✅ Sync: REST API calls (blocking)
- ✅ Async: Message queue (non-blocking)
- ✅ Callback: Webhook notifications
- ❌ No direct communication

---

## 🏢 INFRASTRUCTURE

### Development Environment

```yaml
# docker-compose.yml (Local Development)

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: faceless_youtube
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  mongodb:
    image: mongo:6
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

  app:
    build:
      context: .
      dockerfile: docker/Dockerfile.app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://dev:dev_password@postgres:5432/faceless_youtube
      - REDIS_URL=redis://redis:6379
      - MONGODB_URL=mongodb://mongodb:27017
    depends_on:
      - postgres
      - redis
      - mongodb
    volumes:
      - ./src:/app/src
      - ./assets:/app/assets
      - ./output_videos:/app/output_videos

  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
    volumes:
      - ./src:/app/src
      - ./assets:/app/assets

volumes:
  postgres_data:
  redis_data:
  mongo_data:
```

### Production Environment (Future)

```yaml
# kubernetes/deployment.yaml (Kubernetes - Phase 3)

apiVersion: apps/v1
kind: Deployment
metadata:
  name: content-generator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: content-generator
  template:
    metadata:
      labels:
        app: content-generator
    spec:
      containers:
        - name: content-generator
          image: faceless-youtube/content-generator:latest
          ports:
            - containerPort: 8001
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "2000m"
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: database-credentials
                  key: url
```

---

## 🔒 SECURITY ARCHITECTURE

### Threat Model

**Assets to Protect:**

1. User credentials (YouTube, TikTok, etc.)
2. API keys (OpenAI, Pexels, etc.)
3. Generated content (videos, scripts)
4. Revenue data
5. Analytics data

**Attack Vectors:**

1. Credential theft
2. API key exposure
3. SQL injection
4. Malicious script injection
5. Rate limit abuse

### Security Controls

```python
# src/utils/security.py

from cryptography.fernet import Fernet
import keyring

class CredentialVault:
    """Encrypted credential storage using system keyring."""

    def __init__(self):
        self.key = self._get_or_create_master_key()
        self.cipher = Fernet(self.key)

    def store_credential(
        self,
        service: str,
        username: str,
        credential: str
    ):
        """Store encrypted credential in system keyring."""
        encrypted = self.cipher.encrypt(credential.encode())
        keyring.set_password(
            service,
            username,
            encrypted.decode()
        )

    def retrieve_credential(
        self,
        service: str,
        username: str
    ) -> Optional[str]:
        """Retrieve and decrypt credential."""
        encrypted = keyring.get_password(service, username)
        if not encrypted:
            return None

        decrypted = self.cipher.decrypt(encrypted.encode())
        return decrypted.decode()
```

### Input Validation

```python
from pydantic import BaseModel, validator, Field

class VideoGenerationRequest(BaseModel):
    """Validated video generation request."""

    script: str = Field(..., min_length=50, max_length=10000)
    duration: int = Field(..., ge=60, le=3600)
    style: str = Field(..., regex="^(meditation|sleep|focus|music)$")

    @validator('script')
    def validate_script_content(cls, v):
        """Prevent injection attacks."""
        forbidden_patterns = [
            '<script>',
            'javascript:',
            'onerror=',
            'onclick=',
            '../',  # Path traversal
            '<?php'
        ]

        v_lower = v.lower()
        for pattern in forbidden_patterns:
            if pattern in v_lower:
                raise ValueError(f"Malicious content detected: {pattern}")

        return v
```

---

## 📈 SCALABILITY STRATEGY

### Horizontal Scaling

**Services to Scale:**

1. **Video Renderer** (CPU-intensive)

   - Run 3+ workers
   - Load balance via queue
   - Auto-scale based on queue depth

2. **Asset Scraper** (I/O-intensive)

   - Parallel scraping (10+ sources)
   - Rate limit per source
   - Staggered execution

3. **API Gateway** (Request-intensive)
   - Multiple API instances
   - Nginx load balancer
   - Redis session sharing

### Performance Optimization

```python
# Example: Async asset fetching

import asyncio
import httpx

async def fetch_assets_parallel(queries: List[str]) -> List[Asset]:
    """Fetch assets from multiple sources in parallel."""
    async with httpx.AsyncClient() as client:
        tasks = [
            fetch_from_source(client, query, source)
            for query in queries
            for source in ASSET_SOURCES
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out errors, return successful fetches
        return [r for r in results if isinstance(r, Asset)]
```

### Database Optimization

```sql
-- Indexes for common queries

CREATE INDEX idx_videos_created_at ON videos(created_at DESC);
CREATE INDEX idx_videos_user_id ON videos(user_id);
CREATE INDEX idx_assets_perceptual_hash ON assets(perceptual_hash);
CREATE INDEX idx_analytics_video_platform ON analytics(video_id, platform_id, recorded_at);

-- Partitioning for analytics (large table)

CREATE TABLE analytics (
    id SERIAL,
    video_id INT,
    recorded_at TIMESTAMP,
    ...
) PARTITION BY RANGE (recorded_at);

CREATE TABLE analytics_2025_q1 PARTITION OF analytics
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');
```

---

## 🚀 DEPLOYMENT ARCHITECTURE

### Phase 1: Local Development (Current)

```
Desktop PC
├── Docker Compose
│   ├── PostgreSQL
│   ├── Redis
│   ├── MongoDB
│   └── App services
├── PyQt6 Desktop UI
└── Local file storage
```

### Phase 2: Cloud Hybrid (Month 2-3)

```
Local PC (Development)
│
└──> Cloud Infrastructure (Production)
     ├── AWS/Azure/GCP
     │   ├── Container Registry
     │   ├── Object Storage (videos)
     │   └── CDN (asset delivery)
     │
     └── Self-hosted (VPS)
         ├── PostgreSQL (managed)
         ├── Redis (managed)
         └── App servers
```

### Phase 3: Full Cloud (Month 4+)

```
Kubernetes Cluster
├── Ingress Controller (NGINX)
├── Services
│   ├── Content Generator (3 replicas)
│   ├── Video Renderer (5 replicas)
│   ├── Asset Manager (2 replicas)
│   └── API Gateway (3 replicas)
├── Databases
│   ├── PostgreSQL (RDS/CloudSQL)
│   ├── Redis Cluster
│   └── MongoDB Atlas
└── Storage
    ├── S3/Cloud Storage (videos)
    ├── CloudFront (CDN)
    └── Elastic File System (assets)
```

---

## 📊 MONITORING & OBSERVABILITY

### Metrics to Track

```python
# Prometheus metrics

from prometheus_client import Counter, Histogram, Gauge

# Video generation metrics
videos_generated_total = Counter(
    'videos_generated_total',
    'Total videos generated',
    ['niche', 'status']
)

video_generation_duration = Histogram(
    'video_generation_duration_seconds',
    'Time to generate video',
    ['niche']
)

# Asset metrics
assets_scraped_total = Counter(
    'assets_scraped_total',
    'Total assets scraped',
    ['source']
)

asset_quality_score = Gauge(
    'asset_quality_score',
    'Average asset quality',
    ['source']
)

# Revenue metrics
revenue_total = Counter(
    'revenue_total_dollars',
    'Total revenue generated',
    ['platform', 'source']
)
```

### Logging Strategy

```python
# src/utils/logger.py

import logging
import structlog

def configure_logging():
    """Configure structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Usage
logger = structlog.get_logger()

logger.info(
    "video_generation_started",
    video_id=12345,
    niche="meditation",
    duration=600
)
```

---

## 🔗 RELATED DOCUMENTATION

- **Setup Instructions:** `docs/INSTRUCTIONS.md`
- **API Reference:** `docs/API.md`
- **Deployment Guide:** `docs/DEPLOYMENT.md`
- **Contributing:** `CONTRIBUTING.md`
- **Master Directive:** `copilot_master_prompt.md`
- **Executive Summary:** `GRAND_EXECUTIVE_SUMMARY.md`

---

**END OF ARCHITECTURE DOCUMENT**

_This document will evolve as the system is built. Last updated: October 3, 2025_
