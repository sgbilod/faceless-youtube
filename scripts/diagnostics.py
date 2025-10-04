"""
System Diagnostics Script
Checks all critical components for issues.

Copyright (c) 2025 Faceless YouTube Automation Platform
Licensed under GNU AGPL v3.0
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.config.master_config import config
except ImportError as e:
    print(f"❌ Failed to import config: {e}")
    print("   Make sure you're running from project root and dependencies are installed")
    sys.exit(1)


class DiagnosticResult:
    """Stores diagnostic test results."""
    
    def __init__(self, component: str):
        self.component = component
        self.passed: List[str] = []
        self.failed: List[str] = []
        self.warnings: List[str] = []
    
    def add_pass(self, test: str):
        self.passed.append(test)
    
    def add_fail(self, test: str, error: str):
        self.failed.append(f"{test}: {error}")
    
    def add_warning(self, test: str, message: str):
        self.warnings.append(f"{test}: {message}")
    
    def is_healthy(self) -> bool:
        return len(self.failed) == 0
    
    def print_results(self):
        print(f"\n{'='*60}")
        print(f"Component: {self.component}")
        print(f"{'='*60}")
        
        if self.passed:
            print(f"\n✅ PASSED ({len(self.passed)}):")
            for test in self.passed:
                print(f"   {test}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if self.failed:
            print(f"\n❌ FAILED ({len(self.failed)}):")
            for failure in self.failed:
                print(f"   {failure}")
        
        status = "HEALTHY ✅" if self.is_healthy() else "UNHEALTHY ❌"
        print(f"\nStatus: {status}\n")


async def test_database_connections():
    """Test all database connections."""
    result = DiagnosticResult("Database Connections")
    
    # PostgreSQL
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(config.database.postgres_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        result.add_pass("PostgreSQL connection")
    except ImportError:
        result.add_warning("PostgreSQL connection", "SQLAlchemy not installed")
    except Exception as e:
        result.add_fail("PostgreSQL connection", str(e))
    
    # MongoDB
    try:
        from pymongo import MongoClient
        client = MongoClient(config.database.mongodb_url, serverSelectionTimeoutMS=5000)
        client.server_info()
        result.add_pass("MongoDB connection")
    except ImportError:
        result.add_warning("MongoDB connection", "pymongo not installed")
    except Exception as e:
        result.add_fail("MongoDB connection", str(e))
    
    # Redis
    try:
        import redis
        r = redis.Redis(
            host=config.database.redis_host,
            port=config.database.redis_port,
            db=config.database.redis_db,
            socket_connect_timeout=5
        )
        r.ping()
        result.add_pass("Redis connection")
    except ImportError:
        result.add_warning("Redis connection", "redis not installed")
    except Exception as e:
        result.add_fail("Redis connection", str(e))
    
    return result


async def test_api_dependencies():
    """Test external API availability."""
    result = DiagnosticResult("External APIs")
    
    # Ollama
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"http://{config.api.ollama_host}:{config.api.ollama_port}/api/tags"
            )
            if response.status_code == 200:
                result.add_pass("Ollama connection")
            else:
                result.add_fail("Ollama connection", f"Status {response.status_code}")
    except ImportError:
        result.add_warning("Ollama connection", "httpx not installed")
    except Exception as e:
        result.add_fail("Ollama connection", str(e))
    
    # API Keys
    if config.api.pexels_api_key:
        result.add_pass("Pexels API key configured")
    else:
        result.add_warning("Pexels API key", "Not configured (asset scraping limited)")
    
    if config.api.pixabay_api_key:
        result.add_pass("Pixabay API key configured")
    else:
        result.add_warning("Pixabay API key", "Not configured (asset scraping limited)")
    
    # YouTube credentials
    youtube_secrets_path = config.paths.project_root / config.api.youtube_client_secrets
    if youtube_secrets_path.exists():
        result.add_pass("YouTube client secrets found")
    else:
        result.add_fail("YouTube client secrets", f"File not found: {youtube_secrets_path}")
    
    return result


async def test_file_system():
    """Test file system setup."""
    result = DiagnosticResult("File System")
    
    # Check critical directories
    dirs_to_check = [
        ("Assets directory", config.paths.assets_dir),
        ("Output directory", config.paths.output_dir),
        ("Temp directory", config.paths.temp_dir),
        ("Cache directory", config.paths.cache_dir),
        ("Scripts directory", config.paths.scripts_dir),
    ]
    
    for name, path in dirs_to_check:
        if path.exists():
            result.add_pass(f"{name} exists: {path}")
        else:
            result.add_warning(f"{name}", f"Creating: {path}")
            path.mkdir(parents=True, exist_ok=True)
    
    # Check write permissions
    try:
        test_file = config.paths.temp_dir / "test_write.txt"
        test_file.write_text("test")
        test_file.unlink()
        result.add_pass("Write permissions OK")
    except Exception as e:
        result.add_fail("Write permissions", str(e))
    
    return result


async def test_python_imports():
    """Test critical Python imports."""
    result = DiagnosticResult("Python Dependencies")
    
    required_modules = {
        "fastapi": "FastAPI framework",
        "uvicorn": "ASGI server",
        "sqlalchemy": "Database ORM",
        "pydantic": "Data validation",
        "redis": "Redis client",
        "pymongo": "MongoDB client",
        "httpx": "Async HTTP client",
        "moviepy.editor": "Video editing",
        "PIL": "Image processing",
        "google.oauth2": "Google OAuth",
    }
    
    for module, description in required_modules.items():
        try:
            __import__(module)
            result.add_pass(f"Import {module} - {description}")
        except ImportError as e:
            result.add_fail(f"Import {module}", f"{description} - {str(e)}")
    
    return result


async def test_services():
    """Test service availability."""
    result = DiagnosticResult("Application Services")
    
    # Test each service can be imported
    services = {
        "src.services.script_generator": "AI Script Generation",
        "src.services.video_assembler": "Video Assembly",
        "src.services.youtube_uploader": "YouTube Upload",
        "src.services.scheduler": "Job Scheduling",
    }
    
    for service, description in services.items():
        try:
            __import__(service)
            result.add_pass(f"Import {service} - {description}")
        except Exception as e:
            result.add_fail(f"Import {service}", f"{description} - {str(e)}")
    
    return result


async def test_configuration():
    """Test configuration validity."""
    result = DiagnosticResult("Configuration")
    
    # Test config loading
    try:
        validation = config.validate()
        
        if not validation['errors']:
            result.add_pass("Configuration loaded successfully")
        else:
            for error in validation['errors']:
                result.add_fail("Configuration validation", error)
        
        if validation['warnings']:
            for warning in validation['warnings']:
                result.add_warning("Configuration", warning)
        
    except Exception as e:
        result.add_fail("Configuration loading", str(e))
    
    return result


async def run_all_diagnostics():
    """Run all diagnostic tests."""
    print("\n" + "="*60)
    print("SYSTEM DIAGNOSTICS - FACELESS YOUTUBE AUTOMATION")
    print("="*60)
    print(f"Date: {os.popen('date /t').read().strip() if sys.platform == 'win32' else os.popen('date').read().strip()}")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    print("="*60)
    
    results = []
    
    # Run all tests
    tests = [
        test_configuration(),
        test_python_imports(),
        test_file_system(),
        test_database_connections(),
        test_api_dependencies(),
        test_services(),
    ]
    
    for test_result in await asyncio.gather(*tests):
        test_result.print_results()
        results.append(test_result)
    
    # Overall summary
    print("="*60)
    print("OVERALL SUMMARY")
    print("="*60)
    
    total_passed = sum(len(r.passed) for r in results)
    total_warnings = sum(len(r.warnings) for r in results)
    total_failed = sum(len(r.failed) for r in results)
    
    healthy_components = sum(1 for r in results if r.is_healthy())
    total_components = len(results)
    
    print(f"\nComponents: {healthy_components}/{total_components} healthy")
    print(f"Tests Passed: {total_passed} ✅")
    print(f"Warnings: {total_warnings} ⚠️")
    print(f"Tests Failed: {total_failed} ❌")
    
    # Detailed recommendations
    if total_failed > 0:
        print("\n" + "="*60)
        print("RECOMMENDED ACTIONS")
        print("="*60)
        
        print("\n1. Install missing Python packages:")
        print("   pip install -r requirements.txt")
        
        print("\n2. Start required services:")
        print("   - PostgreSQL (port 5432)")
        print("   - MongoDB (port 27017)")
        print("   - Redis (port 6379)")
        print("   - Ollama (port 11434)")
        
        print("\n3. Configure API keys in .env file:")
        print("   - PEXELS_API_KEY")
        print("   - PIXABAY_API_KEY")
        print("   - YOUTUBE_CLIENT_SECRETS")
        
        print("\n4. Install Node.js dependencies:")
        print("   cd dashboard && npm install")
    
    if total_failed == 0:
        print("\n✅ SYSTEM READY FOR PACKAGING\n")
        return 0
    else:
        print("\n❌ CRITICAL ISSUES MUST BE RESOLVED\n")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_all_diagnostics())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnostics interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Diagnostic script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
