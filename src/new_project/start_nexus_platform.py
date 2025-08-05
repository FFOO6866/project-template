"""
Nexus DataFlow Platform Startup Script
======================================

Windows-compatible startup script for the Nexus multi-channel platform.
Handles environment setup, dependency checking, and graceful startup/shutdown.
"""

import os
import sys
import subprocess
import signal
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def check_python_version():
    """Check Python version compatibility"""
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        "nexus",
        "kailash", 
        "dataflow",
        "fastapi",
        "uvicorn",
        "pyjwt",
        "psycopg2-binary"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"OK {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"MISSING {package}")
    
    if missing_packages:
        print(f"\nInstall missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def setup_environment():
    """Setup environment variables for the platform"""
    env_vars = {
        "NEXUS_ENV": "development",
        "NEXUS_API_PORT": "8000",
        "NEXUS_MCP_PORT": "3001", 
        "NEXUS_API_HOST": "0.0.0.0",
        "NEXUS_JWT_SECRET": "nexus-dataflow-development-secret-key",
        "PYTHONPATH": str(Path(__file__).parent)
    }
    
    for key, default_value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = default_value
            print(f"Set {key}={default_value}")
    
    # Windows-specific path adjustments
    if sys.platform == "win32":
        # Ensure proper PATH for Windows
        current_path = os.environ.get("PATH", "")
        python_path = str(Path(sys.executable).parent)
        if python_path not in current_path:
            os.environ["PATH"] = f"{python_path};{current_path}"
    
    return True

def check_database_config():
    """Check and configure database settings"""
    
    # Check if PostgreSQL is available
    try:
        import psycopg2
        
        # Try to connect to PostgreSQL
        test_connection = "postgresql://horme_user:horme_password@localhost:5432/horme_classification_db"
        try:
            conn = psycopg2.connect(test_connection)
            conn.close()
            print("PostgreSQL connection available")
            return "postgresql"
        except psycopg2.OperationalError:
            print("PostgreSQL not available, using SQLite for development")
            return "sqlite"
    except ImportError:
        print("psycopg2 not available, using SQLite for development")
        return "sqlite"

def create_development_config():
    """Create development configuration file"""
    config = {
        "environment": "development",
        "server": {
            "api_host": "0.0.0.0",
            "api_port": 8000,
            "mcp_port": 3001,
            "enable_https": False,
            "enable_compression": True
        },
        "database": {
            "type": "sqlite",
            "url": "sqlite:///nexus_development.db",
            "pool_size": 10,
            "auto_migrate": True
        },
        "security": {
            "jwt_secret": "nexus-dataflow-development-secret-key",
            "jwt_expiration_hours": 24,
            "enable_cors": True,
            "cors_origins": [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001", 
                "http://127.0.0.1:8080"
            ]
        },
        "performance": {
            "cache_ttl_seconds": 300,
            "max_concurrent_requests": 100,
            "request_timeout": 30,
            "enable_gzip": True
        },
        "monitoring": {
            "enable_metrics": True,
            "metrics_interval": 30,
            "log_level": "INFO"
        }
    }
    
    config_path = Path(__file__).parent / "nexus_config.json"
    
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"Configuration saved to {config_path}")
    return config_path

def start_platform():
    """Start the Nexus DataFlow platform"""
    
    print("\n" + "="*60)
    print("STARTING NEXUS DATAFLOW PLATFORM")
    print("="*60)
    
    # Pre-flight checks
    print("\nPre-flight checks:")
    
    if not check_python_version():
        return False
    
    if not check_dependencies():
        print("\nDependency check failed")
        print("Install dependencies and try again")
        return False
    
    setup_environment()
    db_type = check_database_config()
    config_path = create_development_config()
    
    print(f"\nConfiguration:")
    print(f"   - Database: {db_type}")
    print(f"   - Config file: {config_path}")
    print(f"   - Environment: {os.environ.get('NEXUS_ENV')}")
    
    # Import and start the platform
    try:
        print("\nImporting platform modules...")
        from nexus_dataflow_platform import main
        
        print("Platform modules loaded successfully")
        print("\nStarting multi-channel platform...")
        print("   Press Ctrl+C to stop the platform")
        
        # Start the platform
        main()
        
    except KeyboardInterrupt:
        print("\n\nPlatform shutdown requested...")
        return True
    except ImportError as e:
        print(f"\nImport error: {e}")
        print("Check that all dependencies are installed")
        return False
    except Exception as e:
        print(f"\nPlatform startup failed: {e}")
        return False

def show_help():
    """Show help information"""
    help_text = """
Nexus DataFlow Platform Startup Script
======================================

Usage:
    python start_nexus_platform.py [command]

Commands:
    start       Start the platform (default)
    check       Check dependencies and configuration
    config      Show current configuration
    help        Show this help message

Environment Variables:
    NEXUS_ENV              Environment (development/production)
    NEXUS_API_PORT         API server port (default: 8000)
    NEXUS_MCP_PORT         MCP server port (default: 3001)
    NEXUS_API_HOST         API host (default: 0.0.0.0)
    NEXUS_JWT_SECRET       JWT secret key

Examples:
    python start_nexus_platform.py
    python start_nexus_platform.py start
    python start_nexus_platform.py check

Platform Features:
    • Multi-channel access (API + CLI + MCP)
    • 13 DataFlow models with 117 auto-generated nodes
    • Real-time performance monitoring
    • Unified session management
    • Classification workflows
    • Bulk operations support
    • Production-ready deployment

Access Points:
    • REST API: http://localhost:8000/docs
    • Health Check: http://localhost:8000/api/health
    • MCP Server: http://localhost:3001
    • CLI: nexus --help
"""
    print(help_text)

def check_command():
    """Run dependency and configuration checks"""
    print("DEPENDENCY AND CONFIGURATION CHECK")
    print("="*50)
    
    print("\nPython Environment:")
    check_python_version()
    
    print(f"\nSystem Information:")
    print(f"   - Platform: {sys.platform}")
    print(f"   - Python executable: {sys.executable}")
    print(f"   - Working directory: {os.getcwd()}")
    
    print("\nRequired Dependencies:")
    deps_ok = check_dependencies()
    
    print("\nEnvironment Variables:")
    env_vars = [
        "NEXUS_ENV", "NEXUS_API_PORT", "NEXUS_MCP_PORT", 
        "NEXUS_API_HOST", "NEXUS_JWT_SECRET", "PYTHONPATH"
    ]
    
    for var in env_vars:
        value = os.environ.get(var, "Not set")
        print(f"   - {var}: {value}")
    
    print("\nDatabase Configuration:")
    db_type = check_database_config()
    
    if deps_ok:
        print("\nAll checks passed - platform ready to start")
        return True
    else:
        print("\nSome checks failed - fix issues before starting")
        return False

def config_command():
    """Show current configuration"""
    config_path = Path(__file__).parent / "nexus_config.json"
    
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
        
        print("CURRENT CONFIGURATION")
        print("="*40)
        print(json.dumps(config, indent=2))
    else:
        print("Configuration file not found")
        print("Run 'python start_nexus_platform.py start' to create it")

def main():
    """Main entry point"""
    
    # Handle command line arguments
    command = sys.argv[1] if len(sys.argv) > 1 else "start"
    
    if command == "help" or command == "--help" or command == "-h":
        show_help()
    elif command == "check":
        check_command()
    elif command == "config":
        config_command()
    elif command == "start":
        start_platform()
    else:
        print(f"Unknown command: {command}")
        print("Use 'python start_nexus_platform.py help' for usage information")

if __name__ == "__main__":
    main()