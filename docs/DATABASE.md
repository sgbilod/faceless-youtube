# Database Setup & Migration Guide

## Overview

This project uses **SQLAlchemy 2.0** for ORM and **Alembic** for database migrations. The database layer supports both SQLite (development) and PostgreSQL (production).

## Current Schema

### Tables (11 total)

1. **users** - User accounts and authentication
2. **videos** - Generated videos with metadata
3. **scripts** - AI-generated or manual scripts
4. **assets** - Media files (video/audio/image)
5. **video_assets** - Junction table for video-asset relationships
6. **platforms** - Publishing platform configurations (YouTube, TikTok, etc.)
7. **publishes** - Publishing history and status
8. **analytics** - Performance metrics (views, engagement, revenue)
9. **configurations** - User preferences and settings
10. **revenue** - Revenue tracking and attribution
11. **alembic_version** - Migration version tracking

### Key Features

- **Enums**: Type-safe status values (VideoStatus, AssetType, PlatformName, etc.)
- **Indexes**: Strategic indexes on frequently queried fields
- **Relationships**: Full bidirectional relationships with cascade deletes
- **JSON Fields**: Flexible metadata storage (tags, preferences, analytics)
- **Timestamps**: Automatic created_at/updated_at tracking

## Quick Start

### 1. Environment Setup

Create `.env` file in project root:

```bash
# Development (SQLite)
DATABASE_URL=sqlite:///./faceless_youtube.db

# Production (PostgreSQL)
# DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/faceless_youtube
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Migrations

```bash
# Create initial migration (first time only)
alembic revision --autogenerate -m "initial_schema"

# Apply migrations
alembic upgrade head

# Verify database
python -m scripts.test_database
```

## Database Management

### Creating Migrations

When you modify `src/core/models.py`:

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Review the generated migration file in alembic/versions/
# Edit if needed (Alembic doesn't catch everything!)

# Apply the migration
alembic upgrade head
```

### Migration Commands

```bash
# Show current migration status
alembic current

# Show migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Downgrade one migration
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision_id>

# Show SQL without executing
alembic upgrade head --sql
```

### Database Inspection

```bash
# Test database connection and schema
python -m scripts.test_database

# Check connection only
python -c "from src.core.database import check_db_connection; print(check_db_connection())"

# Interactive Python shell
python
>>> from src.core.database import get_db
>>> from src.core.models import User, Video, Asset
>>> with get_db() as db:
...     users = db.query(User).all()
...     print(f"Total users: {len(users)}")
```

## Model Reference

### User Model

```python
user = User(
    username="john_doe",
    email="john@example.com",
    password_hash=hash_password("secret"),
    is_active=True
)
```

### Video Model

```python
video = Video(
    user_id=user.id,
    script_id=script.id,
    title="10 Minute Meditation",
    description="Peaceful meditation session",
    niche="meditation",
    duration_seconds=600,
    file_path="/output/video_001.mp4",
    status=VideoStatus.COMPLETED
)
```

### Asset Model

```python
asset = Asset(
    asset_type=AssetType.VIDEO,
    file_path="/assets/nature_scene.mp4",
    source_platform="pexels",
    source_id="12345",
    duration_seconds=120,
    quality_score=0.92,
    license_type="free"
)
```

### Platform Model

```python
platform = Platform(
    name=PlatformName.YOUTUBE,
    enabled=True,
    is_configured=True,
    default_config={"visibility": "public"}
)
```

## Common Tasks

### Reset Database (Development Only)

```bash
# DANGER: This will delete all data!
rm faceless_youtube.db  # For SQLite
alembic upgrade head
python -m scripts.test_database
```

### Backup Database

```python
from src.core.database import backup_database

# SQLite - simple file copy
import shutil
shutil.copy("faceless_youtube.db", "backup.db")

# PostgreSQL - using pg_dump
backup_database("backup.sql")
```

### Seed Sample Data

```python
python -m scripts.test_database  # Creates basic test data
# Or create custom seed script in scripts/seed_data.py
```

## Production Deployment

### PostgreSQL Setup

1. **Install PostgreSQL**:

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql
```

2. **Create Database**:

```bash
sudo -u postgres psql
CREATE DATABASE faceless_youtube;
CREATE USER dev WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE faceless_youtube TO dev;
\q
```

3. **Update .env**:

```bash
DATABASE_URL=postgresql+psycopg2://dev:your_secure_password@localhost:5432/faceless_youtube
```

4. **Run Migrations**:

```bash
alembic upgrade head
```

### Connection Pooling

The database is configured with connection pooling (see `src/core/database.py`):

- Pool size: 5 connections
- Max overflow: 10 connections
- Pool timeout: 30 seconds
- Pool recycle: 3600 seconds (1 hour)

Adjust via environment variables:

```bash
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

## Troubleshooting

### "No module named 'psycopg2'"

```bash
pip install psycopg2-binary
```

### "FATAL: password authentication failed"

Check your DATABASE_URL credentials and PostgreSQL pg_hba.conf

### "metadata is reserved when using Declarative API"

Never name a column `metadata` - it's reserved by SQLAlchemy. Use `video_metadata`, `asset_metadata`, etc.

### "Table already exists"

```bash
# Option 1: Drop and recreate (DEVELOPMENT ONLY!)
alembic downgrade base
alembic upgrade head

# Option 2: Mark as already applied
alembic stamp head
```

### Migration Not Detecting Changes

1. Check that model changes are saved
2. Verify Base.metadata includes your models
3. Use `alembic revision -m "description"` to create empty migration
4. Manually write upgrade/downgrade operations

## Best Practices

### DO:

✅ Always create migrations for schema changes  
✅ Review auto-generated migrations before applying  
✅ Test migrations on development before production  
✅ Backup production database before migrations  
✅ Use descriptive migration messages  
✅ Keep models.py and database schema in sync

### DON'T:

❌ Edit applied migrations (create new ones instead)  
❌ Use `Base.metadata.create_all()` in production  
❌ Skip migration testing  
❌ Ignore migration warnings  
❌ Name columns with SQLAlchemy reserved words (`metadata`, `query`, etc.)

## Resources

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- Project Models: `src/core/models.py`
- Database Config: `src/core/database.py`
- Migration Scripts: `alembic/versions/`
