"""
Database Migration Helper Script

Applies pending Alembic migrations to the database.
Provides detailed feedback on migration status and errors.
"""

import sys
import logging
from pathlib import Path
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, text

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import get_database_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_alembic_config() -> Config:
    """Create and configure Alembic configuration."""
    alembic_cfg = Config(str(project_root / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))
    return alembic_cfg


def get_current_revision(engine) -> str:
    """Get current database revision."""
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        return context.get_current_revision()


def get_pending_revisions(alembic_cfg: Config, current_rev: str) -> list:
    """Get list of pending migrations."""
    script = ScriptDirectory.from_config(alembic_cfg)
    head_rev = script.get_current_head()
    
    if current_rev is None:
        # Database is empty, all migrations are pending
        revisions = []
        for rev in script.walk_revisions():
            revisions.append(rev)
        return list(reversed(revisions))  # Return in chronological order
    elif current_rev == head_rev:
        # Database is up to date
        return []
    else:
        # Some migrations are pending
        revisions = []
        for rev in script.iterate_revisions(current_rev, head_rev):
            revisions.append(rev)
        return list(reversed(revisions))[1:]  # Exclude current revision


def migrate(target_revision: str = "head", dry_run: bool = False) -> None:
    """
    Apply database migrations.
    
    Args:
        target_revision: Target revision (default: "head" for latest)
        dry_run: If True, show what would be done without applying
    """
    try:
        logger.info("🚀 Starting database migration...")
        
        # Get database URL and create engine
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        # Get Alembic config
        alembic_cfg = get_alembic_config()
        
        # Check current revision
        current_rev = get_current_revision(engine)
        if current_rev:
            logger.info(f"📍 Current revision: {current_rev}")
        else:
            logger.info("📍 Database is empty (no migrations applied)")
        
        # Check pending migrations
        pending = get_pending_revisions(alembic_cfg, current_rev)
        
        if not pending:
            logger.info("✅ Database is already up to date!")
            return
        
        logger.info(f"📋 Found {len(pending)} pending migration(s):")
        for i, rev in enumerate(pending, 1):
            logger.info(f"  {i}. {rev.revision[:8]} - {rev.doc}")
        
        if dry_run:
            logger.info("🔍 Dry run mode - no changes will be applied")
            logger.info(f"Would migrate to: {target_revision}")
            return
        
        # Apply migrations
        logger.info(f"⚡ Applying migrations to: {target_revision}")
        command.upgrade(alembic_cfg, target_revision)
        
        # Verify new revision
        new_rev = get_current_revision(engine)
        logger.info(f"✅ Migration complete! New revision: {new_rev}")
        
        # Show migration summary
        logger.info("\n" + "="*60)
        logger.info("MIGRATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Previous revision: {current_rev or 'None'}")
        logger.info(f"Current revision:  {new_rev}")
        logger.info(f"Migrations applied: {len(pending)}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        logger.exception("Full error details:")
        sys.exit(1)


def check_database_connection() -> bool:
    """Test database connection."""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Apply database migrations using Alembic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply all pending migrations
  python scripts/db_migrate.py
  
  # Apply migrations up to specific revision
  python scripts/db_migrate.py --revision abc123
  
  # Dry run (show what would be done)
  python scripts/db_migrate.py --dry-run
  
  # Check database connection
  python scripts/db_migrate.py --check
        """
    )
    
    parser.add_argument(
        "--revision",
        default="head",
        help="Target revision (default: head for latest)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show pending migrations without applying"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check database connection only"
    )
    
    args = parser.parse_args()
    
    if args.check:
        if check_database_connection():
            sys.exit(0)
        else:
            sys.exit(1)
    
    migrate(target_revision=args.revision, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
