"""
Test database setup and verify schema.
"""

from src.core.database import get_db, check_db_connection, engine
from src.core.models import Base, User, Video, Asset, Script, Platform, VideoStatus, AssetType, PlatformName
from sqlalchemy import inspect, text
from datetime import datetime


def list_all_tables():
    """List all tables in the database."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("\n📋 Database Tables:")
    print("=" * 50)
    for table in sorted(tables):
        print(f"  ✓ {table}")
    print(f"\n✅ Total: {len(tables)} tables")
    return tables


def get_table_row_counts():
    """Get row count for each table."""
    tables = [
        'users', 'videos', 'scripts', 'assets', 'video_assets',
        'platforms', 'publishes', 'analytics', 'configurations', 'revenue'
    ]
    
    print("\n📊 Table Row Counts:")
    print("=" * 50)
    
    with get_db() as db:
        for table in tables:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  {table:20} : {count:>5} rows")
            except Exception as e:
                print(f"  {table:20} : ERROR - {e}")


def create_test_data():
    """Create some test data."""
    print("\n🔨 Creating test data...")
    print("=" * 50)
    
    with get_db() as db:
        try:
            # Create test user
            test_user = User(
                username="test_user",
                email="test@example.com",
                password_hash="hashed_password",
                is_active=True,
                is_superuser=False
            )
            db.add(test_user)
            db.flush()  # Flush to get user ID
            print(f"  ✓ Created user: {test_user.username} (ID: {test_user.id})")
            
            # Create test platform
            youtube = Platform(
                name=PlatformName.YOUTUBE,
                enabled=True,
                is_configured=True
            )
            db.add(youtube)
            db.flush()
            print(f"  ✓ Created platform: YouTube (ID: {youtube.id})")
            
            # Create test script
            script = Script(
                title="Meditation for Beginners",
                content="Welcome to this peaceful meditation session...",
                niche="meditation",
                actual_word_count=150,
                target_duration_seconds=300,
                generator_model="manual"
            )
            db.add(script)
            db.flush()
            print(f"  ✓ Created script: {script.title} (ID: {script.id})")
            
            # Create test asset
            asset = Asset(
                asset_type=AssetType.VIDEO,
                file_path="/assets/meditation_video.mp4",
                source_platform="pexels",
                source_id="12345",
                duration_seconds=60,
                quality_score=0.85,
                license_type="free"
            )
            db.add(asset)
            db.flush()
            print(f"  ✓ Created asset: {asset.asset_type.value} (ID: {asset.id})")
            
            # Create test video
            video = Video(
                user_id=test_user.id,
                script_id=script.id,
                title="5 Minute Meditation for Peace",
                description="A calming meditation session for inner peace",
                niche="meditation",
                style="calm",
                duration_seconds=300,
                file_path="/output/video_001.mp4",
                status=VideoStatus.COMPLETED
            )
            db.add(video)
            db.flush()
            print(f"  ✓ Created video: {video.title} (ID: {video.id})")
            
            db.commit()
            print("\n✅ Test data created successfully!")
            
        except Exception as e:
            db.rollback()
            print(f"\n❌ Error creating test data: {e}")
            raise


def main():
    """Main test function."""
    print("\n" + "=" * 50)
    print("  DATABASE SCHEMA TEST")
    print("=" * 50)
    
    # Check connection
    print("\n🔌 Testing database connection...")
    if not check_db_connection():
        print("❌ Database connection failed!")
        return
    print("✅ Database connection successful!")
    
    # List tables
    tables = list_all_tables()
    
    # Expected tables
    expected_tables = {
        'users', 'videos', 'scripts', 'assets', 'video_assets',
        'platforms', 'publishes', 'analytics', 'configurations', 
        'revenue', 'alembic_version'
    }
    
    actual_tables = set(tables)
    if expected_tables.issubset(actual_tables):
        print("\n✅ All expected tables exist!")
    else:
        missing = expected_tables - actual_tables
        print(f"\n⚠️  Missing tables: {missing}")
    
    # Show row counts
    get_table_row_counts()
    
    # Create test data
    create_test_data()
    
    # Show row counts again
    get_table_row_counts()
    
    print("\n" + "=" * 50)
    print("  ✅ DATABASE TEST COMPLETE!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
