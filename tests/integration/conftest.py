"""
Integration Test Fixtures

Shared fixtures for integration tests covering database, API, and pipeline testing.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.core.database import Base, get_db
from src.core.models import User, Video, Asset, Script, AssetType, VideoStatus

# API imports will be added when FastAPI app is implemented
# from fastapi.testclient import TestClient
# from httpx import AsyncClient
# from src.api.app import app


# ============================================
# DATABASE FIXTURES
# ============================================

@pytest.fixture(scope="function")
def test_db_engine():
    """
    Create in-memory SQLite database for testing.
    
    Each test gets a fresh database that is destroyed after the test.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """
    Create database session for testing.
    
    Uses transactions that are rolled back after each test for isolation.
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    
    session = TestingSessionLocal()
    
    yield session
    
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
async def async_db_session(test_db_session):
    """
    Async wrapper for database session.
    
    Enables use of async/await in integration tests.
    """
    # Note: In real implementation, use AsyncSession from sqlalchemy.ext.asyncio
    # For now, wrap synchronous session
    yield test_db_session


@pytest.fixture(autouse=True)
def override_get_db(test_db_session):
    """
    Override the get_db dependency to use test database.
    
    Automatically applied to all tests in integration suite.
    Note: Requires FastAPI app to be implemented.
    """
    # When API is ready, uncomment:
    # def _override_get_db():
    #     try:
    #         yield test_db_session
    #     finally:
    #         pass
    #
    # app.dependency_overrides[get_db] = _override_get_db
    # yield
    # app.dependency_overrides.clear()
    
    # For now, just yield
    yield


# ============================================
# API CLIENT FIXTURES
# ============================================

@pytest.fixture(scope="function")
def test_client(test_db_session):
    """
    FastAPI synchronous test client.
    
    For testing API endpoints with real HTTP requests.
    """
    import os
    # Allow all hosts in tests (must be set before importing app)
    os.environ["ALLOWED_HOSTS"] = "*"
    
    from fastapi.testclient import TestClient
    from src.api.main import app
    from src.core.database import get_db
    
    # Override database dependency
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    
    yield client
    
    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_test_client():
    """
    FastAPI asynchronous test client.
    
    For testing API endpoints with async/await support.
    Note: Requires FastAPI app to be implemented.
    """
    # When API is ready, uncomment:
    # from httpx import AsyncClient
    # from src.api.app import app
    # async with AsyncClient(app=app, base_url="http://test") as client:
    #     yield client
    
    pytest.skip("API not yet implemented")


# ============================================
# DATA FIXTURES
# ============================================

@pytest.fixture
def sample_user(test_db_session) -> User:
    """
    Create sample user in test database.
    
    Returns:
        User object with test data
    """
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWuL8Gqo7Cy",  # "password"
        created_at=datetime.utcnow(),
        is_active=True,
        is_superuser=False  # Fixed: was is_verified
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def sample_script(test_db_session) -> Script:
    """
    Create sample script in test database.
    
    Returns:
        Script object with test content
    """
    script = Script(
        title="Test Meditation Script",
        content="Welcome to this peaceful meditation session. Take a deep breath...",
        niche="meditation",
        target_duration_seconds=300,  # Fixed: was duration_seconds
        actual_word_count=150,  # Fixed: was word_count
        created_at=datetime.utcnow()
    )
    test_db_session.add(script)
    test_db_session.commit()
    test_db_session.refresh(script)
    return script


@pytest.fixture
def sample_video(test_db_session, sample_user, sample_script) -> Video:
    """
    Create sample video in test database with relationships.
    
    Returns:
        Video object linked to user and script
    """
    video = Video(
        user_id=sample_user.id,
        script_id=sample_script.id,
        title="Test Meditation Video",
        description="A calming meditation for beginners",
        niche="meditation",
        duration_seconds=300,
        resolution="1080p",  # Fixed: was "1920x1080", should be "1080p"
        fps=30,
        status=VideoStatus.COMPLETED,
        file_path="/test/output/video_test.mp4",
        file_size_bytes=47710208,  # Fixed: was file_size_mb=45.5, now 45.5MB in bytes
        thumbnail_path="/test/output/thumbnail_test.jpg",
        created_at=datetime.utcnow()
    )
    test_db_session.add(video)
    test_db_session.commit()
    test_db_session.refresh(video)
    return video


@pytest.fixture
def sample_asset(test_db_session) -> Asset:
    """
    Create sample asset in test database.
    
    Returns:
        Asset object with test metadata
    """
    asset = Asset(
        asset_type=AssetType.VIDEO,
        source_platform="pexels",
        source_url="https://www.pexels.com/video/12345",
        source_id="pexels_12345",
        file_path="/test/assets/nature_video.mp4",
        file_size_bytes=126353408,  # Fixed: was file_size_mb=120.5, now 120.5MB in bytes
        duration_seconds=30,
        width=1920,  # Fixed: was resolution="1920x1080"
        height=1080,  # Fixed: parsed from resolution
        quality_score=0.95,
        tags=["nature", "forest", "peaceful", "meditation"],
        license_type="pexels",
        created_at=datetime.utcnow()
    )
    test_db_session.add(asset)
    test_db_session.commit()
    test_db_session.refresh(asset)
    return asset


# ============================================
# MOCK SERVICE FIXTURES
# ============================================

@pytest.fixture
def mock_youtube_service():
    """
    Mock YouTube API service.
    
    Prevents actual API calls during integration tests.
    """
    mock_service = AsyncMock()
    mock_service.upload_video = AsyncMock(return_value={
        "id": "test_video_123",
        "status": "uploaded"
    })
    mock_service.get_video_stats = AsyncMock(return_value={
        "views": 1000,
        "likes": 50,
        "comments": 10
    })
    return mock_service


@pytest.fixture
def mock_pexels_service():
    """
    Mock Pexels API service.
    
    Prevents actual API calls during asset scraping tests.
    """
    mock_service = AsyncMock()
    mock_service.search_videos = AsyncMock(return_value=[
        {
            "id": 123456,
            "url": "https://www.pexels.com/video/123456",
            "video_files": [{
                "link": "https://example.com/video.mp4",
                "quality": "hd",
                "width": 1920,
                "height": 1080
            }]
        }
    ])
    return mock_service


@pytest.fixture
def mock_claude_service():
    """
    Mock Claude API service for script generation.
    
    Returns predictable script content without API costs.
    """
    mock_service = AsyncMock()
    mock_service.generate_script = AsyncMock(return_value={
        "title": "Peaceful Morning Meditation",
        "content": "Welcome to this peaceful morning meditation...",
        "duration": 300,
        "word_count": 150
    })
    return mock_service


# ============================================
# REDIS/CACHE FIXTURES
# ============================================

@pytest.fixture
def mock_redis_client():
    """
    Mock Redis client for rate limiting tests.
    
    Simulates Redis behavior without requiring actual Redis server.
    """
    mock_redis = Mock()
    mock_redis.get = Mock(return_value=None)
    mock_redis.set = Mock(return_value=True)
    mock_redis.incr = Mock(return_value=1)
    mock_redis.expire = Mock(return_value=True)
    mock_redis.delete = Mock(return_value=1)
    return mock_redis


# ============================================
# CLEANUP FIXTURES
# ============================================

@pytest.fixture(autouse=True)
def cleanup_test_files(tmp_path):
    """
    Create temporary directory for test files and clean up after.
    
    Automatically applied to all integration tests.
    """
    test_output_dir = tmp_path / "test_output"
    test_output_dir.mkdir(exist_ok=True)
    
    yield test_output_dir
    
    # Cleanup happens automatically with tmp_path


@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for async tests.
    
    Required for pytest-asyncio to work properly.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================
# AUTHENTICATION FIXTURES
# ============================================

@pytest.fixture
def auth_headers(sample_user) -> dict:
    """
    Generate JWT authentication headers for API tests.
    
    Returns:
        Dictionary with Authorization header
    """
    from src.api.auth import create_access_token
    from datetime import timedelta
    
    # Generate real JWT token for test user
    access_token = create_access_token(
        data={"sub": sample_user.email},
        expires_delta=timedelta(hours=1)
    )
    
    return {
        "Authorization": f"Bearer {access_token}"
    }


@pytest.fixture
def admin_user(test_db_session) -> User:
    """
    Create admin user with elevated privileges.
    
    For testing admin-only endpoints.
    """
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWuL8Gqo7Cy",
        created_at=datetime.utcnow(),
        is_active=True,
        is_verified=True,
        is_admin=True
    )
    test_db_session.add(admin)
    test_db_session.commit()
    test_db_session.refresh(admin)
    return admin
