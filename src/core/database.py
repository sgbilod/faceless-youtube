"""
Faceless YouTube Automation Platform
Copyright © 2025 Project Contributors

This file is part of the Faceless YouTube Automation Platform.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.core.models import Base


# ============================================
# DATABASE CONFIGURATION
# ============================================

class DatabaseConfig:
    """Database configuration."""
    
    def __init__(self):
        self.database_url = os.getenv(
            "DATABASE_URL",
            "sqlite:///./faceless_youtube.db"
        )
        
        # Connection pool settings
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))
        
        # Query settings
        self.echo = os.getenv("SQL_ECHO", "false").lower() == "true"
        self.echo_pool = os.getenv("SQL_ECHO_POOL", "false").lower() == "true"
        
    def get_engine_kwargs(self) -> dict:
        """Get SQLAlchemy engine kwargs."""
        return {
            "poolclass": QueuePool,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": True,  # Test connections before using
            "echo": self.echo,
            "echo_pool": self.echo_pool,
        }


# ============================================
# DATABASE ENGINE & SESSION
# ============================================

config = DatabaseConfig()

# Create engine
engine = create_engine(
    config.database_url,
    **config.get_engine_kwargs()
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ============================================
# EVENT LISTENERS
# ============================================

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set SQLite pragmas if using SQLite."""
    if "sqlite" in config.database_url:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# ============================================
# SESSION MANAGEMENT
# ============================================

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Get database session with automatic cleanup.
    
    Usage:
        with get_db() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Generator[Session, None, None]:
    """
    Get database session (for FastAPI dependency injection).
    
    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db_session)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# DATABASE INITIALIZATION
# ============================================

def init_db(drop_all: bool = False):
    """
    Initialize database (create all tables).
    
    Args:
        drop_all: If True, drop all tables before creating
    """
    if drop_all:
        print("⚠️  Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
    
    print("🔨 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")


def check_db_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        from sqlalchemy import text
        with get_db() as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


# ============================================
# DATABASE UTILITIES
# ============================================

def get_table_row_counts() -> dict:
    """
    Get row count for all tables.
    
    Returns:
        Dictionary mapping table names to row counts
    """
    counts = {}
    with get_db() as db:
        for table in Base.metadata.sorted_tables:
            count = db.execute(f"SELECT COUNT(*) FROM {table.name}").scalar()
            counts[table.name] = count
    return counts


def vacuum_database():
    """
    Vacuum database to reclaim space (PostgreSQL only).
    """
    if "postgresql" in config.database_url:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(text("VACUUM ANALYZE"))
        print("✅ Database vacuumed successfully!")
    else:
        print("⚠️  VACUUM only supported on PostgreSQL")


# ============================================
# MIGRATION HELPERS
# ============================================

def backup_database(backup_path: str = None):
    """
    Backup database to SQL file (PostgreSQL only).
    
    Args:
        backup_path: Path to save backup (default: ./backups/db_YYYYMMDD_HHMMSS.sql)
    """
    if "postgresql" not in config.database_url:
        print("⚠️  Backup only supported on PostgreSQL")
        return
    
    from datetime import datetime
    import subprocess
    
    if not backup_path:
        backup_dir = Path("./backups")
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"db_{timestamp}.sql"
    
    # Extract connection details from URL
    # postgresql://user:password@host:port/database
    parts = config.database_url.replace("postgresql://", "").split("/")
    database = parts[1]
    user_host = parts[0].split("@")
    user_pass = user_host[0].split(":")
    
    cmd = [
        "pg_dump",
        "-U", user_pass[0],
        "-h", user_host[1].split(":")[0],
        "-d", database,
        "-f", str(backup_path)
    ]
    
    try:
        subprocess.run(cmd, check=True, env={"PGPASSWORD": user_pass[1]})
        print(f"✅ Database backed up to: {backup_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Backup failed: {e}")


if __name__ == "__main__":
    # Test database connection
    print("🔍 Testing database connection...")
    if check_db_connection():
        print("✅ Database connection successful!")
        
        # Initialize database
        init_db(drop_all=False)
        
        # Show table counts
        print("\n📊 Table row counts:")
        counts = get_table_row_counts()
        for table, count in counts.items():
            print(f"  {table}: {count}")
    else:
        print("❌ Database connection failed!")
        print(f"   URL: {config.database_url}")
