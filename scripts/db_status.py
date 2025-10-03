"""
Database Status Helper Script

Shows comprehensive database migration status including:
- Current revision
- Pending migrations
- Applied migrations history
- Database health checks
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, text, inspect

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
        # All migrations are pending
        revisions = []
        for rev in script.walk_revisions():
            revisions.append(rev)
        return list(reversed(revisions))
    elif current_rev == head_rev:
        # Up to date
        return []
    else:
        # Some migrations pending
        revisions = []
        for rev in script.iterate_revisions(current_rev, head_rev):
            revisions.append(rev)
        return list(reversed(revisions))[1:]


def get_applied_revisions(alembic_cfg: Config, current_rev: str) -> list:
    """Get list of applied migrations."""
    if not current_rev:
        return []
    
    script = ScriptDirectory.from_config(alembic_cfg)
    revisions = []
    
    for rev in script.walk_revisions():
        revisions.append(rev)
        if rev.revision == current_rev:
            break
    
    return list(reversed(revisions))


def check_database_health(engine) -> dict:
    """Perform database health checks."""
    health = {
        "connection": False,
        "tables": [],
        "table_count": 0,
        "alembic_version_exists": False
    }
    
    try:
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            health["connection"] = True
            
            # Get table list
            inspector = inspect(engine)
            health["tables"] = inspector.get_table_names()
            health["table_count"] = len(health["tables"])
            health["alembic_version_exists"] = "alembic_version" in health["tables"]
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
    
    return health


def show_status(verbose: bool = False) -> None:
    """Show comprehensive database status."""
    try:
        logger.info("="*70)
        logger.info("DATABASE MIGRATION STATUS")
        logger.info("="*70)
        logger.info(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*70)
        
        # Get database URL and create engine
        database_url = get_database_url()
        # Mask password in URL for display
        display_url = database_url.split('@')[-1] if '@' in database_url else database_url.split('///')[-1]
        logger.info(f"\n📊 Database: {display_url}")
        
        engine = create_engine(database_url)
        alembic_cfg = get_alembic_config()
        
        # Health check
        logger.info("\n🏥 HEALTH CHECK")
        logger.info("-" * 70)
        health = check_database_health(engine)
        
        if health["connection"]:
            logger.info("✅ Database connection: OK")
        else:
            logger.error("❌ Database connection: FAILED")
            sys.exit(1)
        
        logger.info(f"✅ Tables found: {health['table_count']}")
        
        if health["alembic_version_exists"]:
            logger.info("✅ Alembic version table: EXISTS")
        else:
            logger.warning("⚠️  Alembic version table: NOT FOUND (no migrations applied)")
        
        # Current revision
        current_rev = get_current_revision(engine)
        logger.info("\n📍 CURRENT STATE")
        logger.info("-" * 70)
        
        if current_rev:
            logger.info(f"Current revision: {current_rev}")
        else:
            logger.info("Current revision: None (database is empty)")
        
        # Get head revision
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_current_head()
        logger.info(f"Head revision:    {head_rev}")
        
        if current_rev == head_rev:
            logger.info("✅ Status: UP TO DATE")
        elif current_rev is None:
            logger.warning("⚠️  Status: NO MIGRATIONS APPLIED")
        else:
            logger.warning("⚠️  Status: MIGRATIONS PENDING")
        
        # Applied migrations
        applied = get_applied_revisions(alembic_cfg, current_rev)
        logger.info(f"\n✅ APPLIED MIGRATIONS ({len(applied)})")
        logger.info("-" * 70)
        
        if applied:
            for i, rev in enumerate(reversed(applied), 1):
                marker = "👉" if rev.revision == current_rev else "  "
                logger.info(f"{marker} {i}. {rev.revision[:12]} - {rev.doc}")
        else:
            logger.info("No migrations applied yet")
        
        # Pending migrations
        pending = get_pending_revisions(alembic_cfg, current_rev)
        logger.info(f"\n⏳ PENDING MIGRATIONS ({len(pending)})")
        logger.info("-" * 70)
        
        if pending:
            for i, rev in enumerate(pending, 1):
                logger.info(f"  {i}. {rev.revision[:12]} - {rev.doc}")
            logger.info(f"\n💡 Run 'python scripts/db_migrate.py' to apply pending migrations")
        else:
            logger.info("No pending migrations")
        
        # Verbose mode - show all tables
        if verbose and health["tables"]:
            logger.info(f"\n📋 DATABASE TABLES ({len(health['tables'])})")
            logger.info("-" * 70)
            for table in sorted(health["tables"]):
                logger.info(f"  • {table}")
        
        logger.info("\n" + "="*70)
        
    except Exception as e:
        logger.error(f"❌ Failed to show status: {e}")
        logger.exception("Full error details:")
        sys.exit(1)


def show_quick_status() -> None:
    """Show quick one-line status."""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url)
        alembic_cfg = get_alembic_config()
        
        current_rev = get_current_revision(engine)
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_current_head()
        pending = get_pending_revisions(alembic_cfg, current_rev)
        
        if current_rev == head_rev:
            print(f"✅ UP TO DATE - Revision: {current_rev[:8] if current_rev else 'None'}")
        elif not current_rev:
            print(f"⚠️  NO MIGRATIONS - {len(pending)} pending")
        else:
            print(f"⚠️  NEEDS UPDATE - {len(pending)} pending - Current: {current_rev[:8]}")
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Show database migration status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show full status report
  python scripts/db_status.py
  
  # Show verbose status with all tables
  python scripts/db_status.py --verbose
  
  # Show quick one-line status
  python scripts/db_status.py --quick
        """
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output with all database tables"
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Show quick one-line status"
    )
    
    args = parser.parse_args()
    
    if args.quick:
        show_quick_status()
    else:
        show_status(verbose=args.verbose)


if __name__ == "__main__":
    main()
