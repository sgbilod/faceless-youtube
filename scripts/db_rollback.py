"""
Database Rollback Helper Script

Rolls back Alembic migrations to a previous state.
Provides safety checks and confirmation prompts for production environments.
"""

import sys
import logging
from pathlib import Path
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine

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


def get_revision_history(alembic_cfg: Config, current_rev: str, steps: int = 5) -> list:
    """Get revision history for context."""
    script = ScriptDirectory.from_config(alembic_cfg)
    revisions = []
    
    for rev in script.walk_revisions():
        revisions.append(rev)
        if len(revisions) >= steps:
            break
    
    return revisions


def rollback(steps: int = 1, target_revision: str = None, force: bool = False) -> None:
    """
    Rollback database migrations.
    
    Args:
        steps: Number of migrations to rollback (default: 1)
        target_revision: Specific revision to rollback to (overrides steps)
        force: Skip confirmation prompt
    """
    try:
        logger.info("🔄 Starting database rollback...")
        
        # Get database URL and create engine
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        # Get Alembic config
        alembic_cfg = get_alembic_config()
        
        # Check current revision
        current_rev = get_current_revision(engine)
        if not current_rev:
            logger.error("❌ No migrations to rollback (database is empty)")
            sys.exit(1)
        
        logger.info(f"📍 Current revision: {current_rev}")
        
        # Determine target revision
        if target_revision:
            target = target_revision
            logger.info(f"🎯 Target revision: {target}")
        else:
            target = f"-{steps}"
            logger.info(f"🎯 Rolling back {steps} migration(s)")
        
        # Show revision history for context
        logger.info("\n📚 Recent revision history:")
        history = get_revision_history(alembic_cfg, current_rev, steps=5)
        for i, rev in enumerate(history):
            marker = "👉" if rev.revision == current_rev else "  "
            logger.info(f"{marker} {rev.revision[:8]} - {rev.doc}")
        
        # Safety confirmation
        if not force:
            logger.warning("\n⚠️  WARNING: Rollback may result in data loss!")
            logger.warning("Make sure you have a database backup before proceeding.")
            response = input("\nDo you want to continue? (yes/no): ").strip().lower()
            
            if response != "yes":
                logger.info("❌ Rollback cancelled by user")
                sys.exit(0)
        
        # Apply rollback
        logger.info(f"⚡ Rolling back to: {target}")
        command.downgrade(alembic_cfg, target)
        
        # Verify new revision
        new_rev = get_current_revision(engine)
        logger.info(f"✅ Rollback complete! New revision: {new_rev or 'None (empty database)'}")
        
        # Show rollback summary
        logger.info("\n" + "="*60)
        logger.info("ROLLBACK SUMMARY")
        logger.info("="*60)
        logger.info(f"Previous revision: {current_rev}")
        logger.info(f"Current revision:  {new_rev or 'None'}")
        logger.info(f"Steps rolled back:  {steps if not target_revision else 'N/A'}")
        logger.info("="*60)
        logger.warning("\n⚠️  Remember to verify application functionality after rollback!")
        
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        logger.exception("Full error details:")
        sys.exit(1)


def show_history(limit: int = 10) -> None:
    """Show migration history."""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url)
        alembic_cfg = get_alembic_config()
        
        current_rev = get_current_revision(engine)
        logger.info(f"📍 Current revision: {current_rev or 'None'}")
        
        logger.info(f"\n📚 Migration history (last {limit}):")
        logger.info("="*60)
        
        history = get_revision_history(alembic_cfg, current_rev, steps=limit)
        for i, rev in enumerate(history, 1):
            marker = "👉 CURRENT" if rev.revision == current_rev else ""
            logger.info(f"{i}. {rev.revision[:8]} - {rev.doc} {marker}")
        
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Failed to show history: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Rollback database migrations using Alembic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Rollback last migration (with confirmation)
  python scripts/db_rollback.py
  
  # Rollback last 3 migrations
  python scripts/db_rollback.py --steps 3
  
  # Rollback to specific revision
  python scripts/db_rollback.py --revision abc123
  
  # Force rollback without confirmation (use with caution!)
  python scripts/db_rollback.py --force
  
  # Show migration history
  python scripts/db_rollback.py --history
        """
    )
    
    parser.add_argument(
        "--steps",
        type=int,
        default=1,
        help="Number of migrations to rollback (default: 1)"
    )
    parser.add_argument(
        "--revision",
        help="Specific revision to rollback to"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt (use with caution!)"
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="Show migration history"
    )
    
    args = parser.parse_args()
    
    if args.history:
        show_history()
    else:
        rollback(
            steps=args.steps,
            target_revision=args.revision,
            force=args.force
        )


if __name__ == "__main__":
    main()
