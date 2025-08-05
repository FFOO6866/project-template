#!/usr/bin/env python3
"""
Production Startup Script for Nexus Multi-Channel Platform
==========================================================

Comprehensive production startup with:
- Environment validation
- Database initialization
- Cache warming
- Health checks
- Performance monitoring
- Graceful shutdown handling
"""

import os
import sys
import asyncio
import signal
import logging
import time
from typing import Optional
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/logs/nexus-production.log') if os.path.exists('/app/logs') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductionStartupManager:
    """Manages production startup process"""
    
    def __init__(self):
        self.startup_start_time = time.time()
        self.nexus_app = None
        self.startup_tasks = []
        self.shutdown_requested = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown_signal)
        signal.signal(signal.SIGINT, self._handle_shutdown_signal)
    
    def _handle_shutdown_signal(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received shutdown signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
        
        if self.nexus_app:
            try:
                # Graceful shutdown of Nexus platform
                logger.info("Shutting down Nexus platform...")
                # The actual shutdown will be handled by the main loop
            except Exception as e:
                logger.error(f"Error during Nexus shutdown: {e}")
    
    def validate_environment(self) -> bool:
        """Validate production environment"""
        logger.info("🔍 Validating production environment...")
        
        validation_errors = []
        
        # Check required environment variables
        required_env_vars = [
            'NEXUS_ENV',
            'DATABASE_URL', 
            'NEXUS_JWT_SECRET',
            'NEXUS_JWT_REFRESH_SECRET'
        ]
        
        for var in required_env_vars:
            if not os.getenv(var):
                validation_errors.append(f"Missing required environment variable: {var}")
        
        # Check JWT secrets are not default values
        jwt_secret = os.getenv('NEXUS_JWT_SECRET', '')
        refresh_secret = os.getenv('NEXUS_JWT_REFRESH_SECRET', '')
        
        if 'change-me' in jwt_secret.lower() or len(jwt_secret) < 32:
            validation_errors.append("JWT_SECRET appears to be default or too short (minimum 32 characters)")
        
        if 'change-me' in refresh_secret.lower() or len(refresh_secret) < 32:
            validation_errors.append("JWT_REFRESH_SECRET appears to be default or too short (minimum 32 characters)")
        
        # Check database connectivity
        try:
            import psycopg2
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                conn = psycopg2.connect(database_url)
                conn.close()
                logger.info("✅ Database connection validated")
            else:
                validation_errors.append("DATABASE_URL not configured")
        except ImportError:
            logger.warning("⚠️  psycopg2 not available, skipping database validation")
        except Exception as e:
            validation_errors.append(f"Database connection failed: {str(e)}")
        
        # Check Redis connectivity (optional)
        redis_enabled = os.getenv('REDIS_ENABLED', 'false').lower() == 'true'
        if redis_enabled:
            try:
                import redis
                redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
                r = redis.from_url(redis_url)
                r.ping()
                logger.info("✅ Redis connection validated")
            except ImportError:
                logger.warning("⚠️  Redis library not available")
            except Exception as e:
                logger.warning(f"⚠️  Redis connection failed: {str(e)} (continuing without Redis)")
        
        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            free_gb = free // (1024**3)
            if free_gb < 1:  # Less than 1GB free
                validation_errors.append(f"Low disk space: {free_gb}GB free")
            else:
                logger.info(f"✅ Disk space: {free_gb}GB free")
        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")
        
        # Check memory
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                for line in meminfo.split('\\n'):
                    if line.startswith('MemAvailable:'):
                        available_kb = int(line.split()[1])
                        available_mb = available_kb // 1024
                        if available_mb < 512:  # Less than 512MB available
                            validation_errors.append(f"Low memory: {available_mb}MB available")
                        else:
                            logger.info(f"✅ Memory: {available_mb}MB available")
                        break
        except Exception as e:
            logger.warning(f"Could not check memory: {e}")
        
        if validation_errors:
            logger.error("❌ Environment validation failed:")
            for error in validation_errors:
                logger.error(f"  • {error}")
            return False
        
        logger.info("✅ Environment validation completed successfully")
        return True
    
    def check_dependencies(self) -> bool:
        """Check that all required dependencies are available"""
        logger.info("📦 Checking dependencies...")
        
        required_packages = [
            'fastapi',
            'uvicorn', 
            'websockets',
            'redis',
            'psycopg2',
            'jwt',
            'nexus',  # Our Nexus package
            'dataflow'  # DataFlow package
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                if package == 'nexus':
                    from nexus import Nexus
                elif package == 'dataflow':
                    from dataflow import DataFlow
                elif package == 'jwt':
                    import jwt
                elif package == 'psycopg2':
                    import psycopg2
                else:
                    __import__(package)
                logger.debug(f"✅ {package} available")
            except ImportError as e:
                missing_packages.append(f"{package}: {str(e)}")
                logger.error(f"❌ {package} not available: {e}")
        
        if missing_packages:
            logger.error("❌ Missing required dependencies:")
            for package in missing_packages:
                logger.error(f"  • {package}")
            return False
        
        logger.info("✅ All dependencies available")
        return True
    
    async def initialize_database(self) -> bool:
        """Initialize database with production optimizations"""
        logger.info("🗄️  Initializing database...")
        
        try:
            # Import the production platform to trigger database setup
            from nexus_production_platform import setup_production_database
            
            if setup_production_database():
                logger.info("✅ Database initialization completed")
                return True
            else:
                logger.error("❌ Database initialization failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            return False
    
    async def warm_caches(self) -> bool:
        """Warm production caches"""
        logger.info("🔥 Warming production caches...")
        
        try:
            # Import production optimizer
            from dataflow_production_optimizations import production_optimizer
            
            cache_warming_enabled = os.getenv('CACHE_WARMING_ENABLED', 'true').lower() == 'true'
            
            if cache_warming_enabled:
                result = await production_optimizer.warm_all_caches()
                if result['success']:
                    logger.info(f"✅ Caches warmed: {result['total_warmed_records']:,} records across {result['successful_models']} models")
                    return True
                else:
                    logger.warning("⚠️  Cache warming completed with some failures")
                    return True  # Don't fail startup for cache warming issues
            else:
                logger.info("ℹ️  Cache warming disabled")
                return True
                
        except Exception as e:
            logger.warning(f"⚠️  Cache warming error: {e} (continuing startup)")
            return True  # Don't fail startup for cache warming issues
    
    async def perform_health_checks(self) -> bool:
        """Perform initial health checks"""
        logger.info("🏥 Performing health checks...")
        
        try:
            # Import configuration
            from nexus_production_platform import config
            
            # Check metrics initialization
            if hasattr(config, 'metrics'):
                logger.info("✅ Metrics system initialized")
            else:
                logger.error("❌ Metrics system not initialized")
                return False
            
            # Check WebSocket manager
            from nexus_production_platform import websocket_manager
            if websocket_manager:
                logger.info("✅ WebSocket manager initialized")
            else:
                logger.error("❌ WebSocket manager not initialized")
                return False
            
            # Check session manager
            from nexus_production_platform import session_manager
            if session_manager:
                logger.info("✅ Session manager initialized")
            else:
                logger.error("❌ Session manager not initialized")
                return False
            
            logger.info("✅ Health checks completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False
    
    def display_startup_summary(self):
        """Display startup summary"""
        startup_time = time.time() - self.startup_start_time
        
        logger.info("\\n" + "="*80)
        logger.info("🎯 NEXUS PRODUCTION PLATFORM - STARTUP COMPLETE")
        logger.info("="*80)
        logger.info(f"🕐 Startup time: {startup_time:.2f} seconds")
        logger.info(f"🏭 Environment: {os.getenv('NEXUS_ENV', 'production')}")
        logger.info(f"🌐 API Port: {os.getenv('NEXUS_API_PORT', '8000')}")
        logger.info(f"🔌 WebSocket Port: {os.getenv('NEXUS_WEBSOCKET_PORT', '8001')}")
        logger.info(f"🤖 MCP Port: {os.getenv('NEXUS_MCP_PORT', '3001')}")
        logger.info(f"💾 Redis: {'enabled' if os.getenv('REDIS_ENABLED') == 'true' else 'disabled'}")
        logger.info(f"🔄 Cache Warming: {'enabled' if os.getenv('CACHE_WARMING_ENABLED') == 'true' else 'disabled'}")
        logger.info(f"⚡ Max Concurrent: {os.getenv('MAX_CONCURRENT_REQUESTS', '500')} requests")
        logger.info(f"📊 Batch Limit: {os.getenv('BATCH_SIZE_LIMIT', '2000')} records")
        logger.info("")
        logger.info("🚀 Platform ready for high-performance operations:")
        logger.info("  • Multi-channel access (API + WebSocket + CLI + MCP)")
        logger.info("  • Real-time notifications and updates")
        logger.info("  • Enhanced JWT security with refresh tokens")
        logger.info("  • Production-optimized DataFlow operations")
        logger.info("  • Comprehensive monitoring and alerting")
        logger.info("")
        logger.info("🔗 Endpoints:")
        logger.info(f"  • API: http://0.0.0.0:{os.getenv('NEXUS_API_PORT', '8000')}")
        logger.info(f"  • WebSocket: ws://0.0.0.0:{os.getenv('NEXUS_WEBSOCKET_PORT', '8001')}/ws")
        logger.info(f"  • Health: http://0.0.0.0:{os.getenv('NEXUS_API_PORT', '8000')}/api/v2/health/comprehensive")
        logger.info(f"  • Metrics: http://0.0.0.0:{os.getenv('NEXUS_API_PORT', '8000')}/api/v2/metrics/production")
        logger.info("="*80)
    
    async def start_platform(self):
        """Start the Nexus platform"""
        logger.info("🚀 Starting Nexus production platform...")
        
        try:
            # Import and start the main platform
            from nexus_production_platform import main, app
            
            # Store reference to app for graceful shutdown
            self.nexus_app = app
            
            # Start the platform (this will block)
            main()
            
        except KeyboardInterrupt:
            logger.info("🛑 Startup interrupted by user")
        except Exception as e:
            logger.error(f"❌ Platform startup failed: {e}")
            raise
    
    async def run_startup_sequence(self):
        """Run the complete startup sequence"""
        logger.info("\\n" + "="*80)
        logger.info("🏭 NEXUS PRODUCTION PLATFORM STARTUP")
        logger.info("="*80)
        
        startup_steps = [
            ("Environment Validation", self.validate_environment),
            ("Dependency Check", self.check_dependencies),
            ("Database Initialization", self.initialize_database),
            ("Cache Warming", self.warm_caches),
            ("Health Checks", self.perform_health_checks)
        ]
        
        for step_name, step_function in startup_steps:
            if self.shutdown_requested:
                logger.info("🛑 Shutdown requested during startup")
                return False
                
            logger.info(f"\\n📋 Step: {step_name}")
            try:
                if asyncio.iscoroutinefunction(step_function):
                    success = await step_function()
                else:
                    success = step_function()
                
                if not success:
                    logger.error(f"❌ Startup failed at step: {step_name}")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Error in step {step_name}: {e}")
                return False
        
        # Display startup summary
        self.display_startup_summary()
        
        # Start the platform
        await self.start_platform()
        
        return True

async def main():
    """Main production startup function"""
    startup_manager = ProductionStartupManager()
    
    try:
        success = await startup_manager.run_startup_sequence()
        if not success:
            logger.error("❌ Production startup failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Startup interrupted")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Unexpected startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Set production environment if not already set
    if not os.getenv('NEXUS_ENV'):
        os.environ['NEXUS_ENV'] = 'production'
    
    # Run the startup sequence
    asyncio.run(main())