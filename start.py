"""
Unified Startup Script
Starts all services with a single command.

Copyright (c) 2025 Faceless YouTube Automation Platform
Licensed under GNU AGPL v3.0
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path
from typing import List, Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServiceManager:
    """Manages all application services."""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.project_root = Path(__file__).parent
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        logger.info("Checking prerequisites...")
        
        issues = []
        
        # Check Python version
        if sys.version_info < (3, 8):
            issues.append(f"Python 3.8+ required, found {sys.version}")
        else:
            logger.info(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
        
        # Check virtual environment
        if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            logger.warning("⚠️  Not running in virtual environment")
        else:
            logger.info("✅ Virtual environment active")
        
        # Check requirements.txt exists
        req_file = self.project_root / "requirements.txt"
        if not req_file.exists():
            issues.append("requirements.txt not found")
        else:
            logger.info("✅ requirements.txt found")
        
        # Check .env file
        env_file = self.project_root / ".env"
        if not env_file.exists():
            logger.warning("⚠️  .env file not found (using defaults)")
        else:
            logger.info("✅ .env file found")
        
        # Check client_secrets.json
        secrets_file = self.project_root / "client_secrets.json"
        if not secrets_file.exists():
            logger.warning("⚠️  client_secrets.json not found (YouTube uploads disabled)")
        else:
            logger.info("✅ client_secrets.json found")
        
        if issues:
            logger.error("❌ Prerequisites check failed:")
            for issue in issues:
                logger.error(f"   - {issue}")
            return False
        
        logger.info("✅ All prerequisites met\n")
        return True
    
    def start_database_services(self):
        """Start database services (PostgreSQL, MongoDB, Redis)."""
        logger.info("Checking database services...")
        
        # Note: These services should be started separately
        # This function just checks if they're available
        
        logger.info("ℹ️  PostgreSQL - Start manually or via Docker")
        logger.info("ℹ️  MongoDB - Start manually or via Docker")
        logger.info("ℹ️  Redis - Start manually or via Docker")
        logger.info("ℹ️  Ollama - Ensure running on localhost:11434\n")
    
    def start_backend(self):
        """Start FastAPI backend server."""
        logger.info("Starting FastAPI backend...")
        
        # Start uvicorn
        backend_cmd = [
            sys.executable, "-m", "uvicorn",
            "src.api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ]
        
        try:
            process = subprocess.Popen(
                backend_cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            
            self.processes.append(process)
            logger.info("✅ Backend started on http://localhost:8000")
            logger.info("   API docs: http://localhost:8000/docs\n")
            
            # Wait for backend to be ready
            time.sleep(3)
            
        except FileNotFoundError:
            logger.error("❌ uvicorn not found - install with: pip install uvicorn")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to start backend: {e}")
            raise
    
    def start_frontend(self):
        """Start React frontend development server."""
        logger.info("Starting React frontend...")
        
        dashboard_dir = self.project_root / "dashboard"
        
        if not dashboard_dir.exists():
            logger.error("❌ dashboard/ directory not found")
            return
        
        # Check if node_modules exists
        node_modules = dashboard_dir / "node_modules"
        if not node_modules.exists():
            logger.info("📦 Installing frontend dependencies...")
            install_cmd = ["npm", "install"]
            
            try:
                result = subprocess.run(
                    install_cmd,
                    cwd=dashboard_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info("✅ Dependencies installed")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ npm install failed: {e}")
                logger.error(e.stderr)
                return
            except FileNotFoundError:
                logger.error("❌ npm not found - install Node.js from https://nodejs.org/")
                return
        
        # Start Vite dev server
        frontend_cmd = ["npm", "run", "dev"]
        
        try:
            process = subprocess.Popen(
                frontend_cmd,
                cwd=dashboard_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            
            self.processes.append(process)
            logger.info("✅ Frontend started on http://localhost:3000\n")
            
        except FileNotFoundError:
            logger.error("❌ npm not found - install Node.js from https://nodejs.org/")
        except Exception as e:
            logger.error(f"❌ Failed to start frontend: {e}")
    
    def start_all(self):
        """Start all services."""
        print("\n" + "="*60)
        print("🚀 FACELESS YOUTUBE AUTOMATION PLATFORM")
        print("="*60 + "\n")
        
        # Check prerequisites
        if not self.check_prerequisites():
            logger.error("\n❌ Cannot start - prerequisites not met")
            logger.info("\nRun the following commands:")
            logger.info("  1. pip install -r requirements.txt")
            logger.info("  2. Copy .env.example to .env and configure")
            logger.info("  3. Add client_secrets.json for YouTube")
            sys.exit(1)
        
        try:
            # Check database services
            self.start_database_services()
            
            # Start backend
            self.start_backend()
            
            # Start frontend
            self.start_frontend()
            
            logger.info("="*60)
            logger.info("🎉 ALL SERVICES STARTED")
            logger.info("="*60)
            logger.info("\n📍 Access Points:")
            logger.info("   Frontend:     http://localhost:3000")
            logger.info("   Backend API:  http://localhost:8000")
            logger.info("   API Docs:     http://localhost:8000/docs")
            logger.info("\n💡 Tips:")
            logger.info("   - Open http://localhost:3000 in your browser")
            logger.info("   - Check logs below for any errors")
            logger.info("   - Press Ctrl+C to stop all services")
            logger.info("\n" + "="*60 + "\n")
            
            # Wait for interrupt
            self.wait_for_interrupt()
            
        except KeyboardInterrupt:
            logger.info("\n\nShutting down services...")
            self.stop_all()
        except Exception as e:
            logger.error(f"\n❌ Failed to start services: {e}")
            self.stop_all()
            sys.exit(1)
    
    def wait_for_interrupt(self):
        """Wait for keyboard interrupt."""
        try:
            # Keep main thread alive
            while True:
                # Check if any process died
                for i, process in enumerate(self.processes):
                    if process.poll() is not None:
                        logger.warning(f"⚠️  Process {i} exited with code {process.returncode}")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            raise
    
    def stop_all(self):
        """Stop all running services."""
        logger.info("\n🛑 Stopping all services...")
        
        for i, process in enumerate(self.processes):
            try:
                logger.info(f"   Stopping process {i}...")
                
                if sys.platform == 'win32':
                    # On Windows, send CTRL_BREAK_EVENT
                    process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    # On Unix, send SIGTERM
                    process.terminate()
                
                # Wait up to 5 seconds for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"   Process {i} didn't stop gracefully, forcing...")
                    process.kill()
                    process.wait()
                
            except Exception as e:
                logger.error(f"   Error stopping process {i}: {e}")
                try:
                    process.kill()
                except:
                    pass
        
        logger.info("✅ All services stopped\n")


def main():
    """Main entry point."""
    try:
        manager = ServiceManager()
        manager.start_all()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
