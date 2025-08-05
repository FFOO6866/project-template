"""
Production MCP Server Startup Script
===================================

Convenience script to start the production MCP server with various configurations.
Supports both standalone mode and integration with existing Nexus platform.

Usage:
    # Standalone production server
    python start_production_mcp_server.py --mode standalone
    
    # Integration with existing Nexus platform
    python start_production_mcp_server.py --mode nexus-integration
    
    # Development mode with mock DataFlow
    python start_production_mcp_server.py --mode development
"""

import os
import sys
import asyncio
import argparse
import logging
import json
from pathlib import Path
from typing import Optional

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Import our modules
from production_mcp_server import ProductionMCPServer, ServerConfig
from enhanced_nexus_mcp_integration import EnhancedNexusMCPIntegration, create_production_mcp_config

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('production_mcp_server.log')
        ]
    )

def load_config_file(config_path: str) -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config file {config_path}: {e}")
        return {}

def create_server_config(args, file_config: dict) -> ServerConfig:
    """Create server configuration from args and file"""
    
    # Start with defaults
    config_dict = {
        "port": 3001,
        "host": "0.0.0.0",
        "enable_auth": True,
        "auth_type": "jwt",
        "max_concurrent_requests": 500,
        "enable_agent_collaboration": True,
        "enable_performance_tracking": True,
        "enable_metrics": True,
        "enable_caching": True,
        "enable_http_transport": True
    }
    
    # Override with file config
    config_dict.update(file_config)
    
    # Override with command line args
    if args.port:
        config_dict["port"] = args.port
    if args.host:
        config_dict["host"] = args.host
    if args.auth_type:
        config_dict["auth_type"] = args.auth_type
    if args.no_auth:
        config_dict["enable_auth"] = False
    if args.no_http:
        config_dict["enable_http_transport"] = False
    
    # Create ServerConfig object
    return ServerConfig(**config_dict)

async def start_standalone_server(config: ServerConfig):
    """Start standalone production MCP server"""
    
    print("\n" + "="*80)
    print("🚀 STARTING PRODUCTION MCP SERVER - STANDALONE MODE")
    print("="*80)
    
    server = ProductionMCPServer(config)
    
    try:
        await server.start_async()
    except KeyboardInterrupt:
        print("\n🛑 Server shutdown requested")
        server.shutdown()
    except Exception as e:
        print(f"❌ Server failed: {e}")
        import traceback
        traceback.print_exc()
        server.shutdown()
        sys.exit(1)

async def start_nexus_integration(config: ServerConfig):
    """Start MCP server with Nexus integration"""
    
    print("\n" + "="*80)
    print("🔗 STARTING PRODUCTION MCP SERVER - NEXUS INTEGRATION MODE")
    print("="*80)
    
    try:
        # Try to import existing Nexus app
        try:
            from nexus_dataflow_platform import app as nexus_app
            print("✅ Found existing Nexus DataFlow platform")
        except ImportError:
            print("⚠️  Nexus DataFlow platform not found, creating basic integration")
            nexus_app = None
        
        # Create enhanced integration
        integration = EnhancedNexusMCPIntegration(nexus_app, config)
        integration.start()
        
        print("🎯 Integration started successfully!")
        print("📱 Access methods:")
        print(f"   • MCP Protocol: STDIO transport")
        print(f"   • HTTP API: http://{config.host}:{config.port + 1}/api/mcp/*")
        if nexus_app:
            print(f"   • Nexus Platform: Integrated workflows available")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Integration shutdown requested")
            integration.shutdown()
        
    except Exception as e:
        print(f"❌ Integration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def start_development_mode(config: ServerConfig):
    """Start in development mode with mock DataFlow"""
    
    print("\n" + "="*80)
    print("🛠️  STARTING PRODUCTION MCP SERVER - DEVELOPMENT MODE")
    print("="*80)
    
    print("⚠️  Development mode features:")
    print("   • Mock DataFlow models (SQLite)")
    print("   • Reduced security settings")
    print("   • Enhanced logging")
    print("   • Development-friendly defaults")
    
    # Override config for development
    config.enable_auth = False  # Disable auth for easier testing
    config.cache_ttl_seconds = 60  # Shorter cache TTL
    config.rate_limit_per_minute = 10000  # Higher rate limit
    
    server = ProductionMCPServer(config)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n🛑 Development server shutdown")
        server.shutdown()
    except Exception as e:
        print(f"❌ Development server failed: {e}")
        import traceback
        traceback.print_exc()
        server.shutdown()
        sys.exit(1)

def main():
    """Main startup function"""
    
    parser = argparse.ArgumentParser(
        description="Production MCP Server with AI Agent Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standalone production server
  python start_production_mcp_server.py --mode standalone --port 3001
  
  # Integration with Nexus platform
  python start_production_mcp_server.py --mode nexus-integration
  
  # Development mode
  python start_production_mcp_server.py --mode development --no-auth
  
  # Custom configuration
  python start_production_mcp_server.py --config mcp_server_config.json
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=["standalone", "nexus-integration", "development"],
        default="standalone",
        help="Server mode"
    )
    
    parser.add_argument("--port", type=int, help="Server port (default: 3001)")
    parser.add_argument("--host", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--auth-type", choices=["jwt", "api_key", "bearer"], help="Authentication type")
    parser.add_argument("--no-auth", action="store_true", help="Disable authentication")
    parser.add_argument("--no-http", action="store_true", help="Disable HTTP transport")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Load configuration file if provided
    file_config = {}
    if args.config:
        if Path(args.config).exists():
            file_config = load_config_file(args.config)
            print(f"✅ Loaded configuration from {args.config}")
        else:
            print(f"❌ Configuration file not found: {args.config}")
            sys.exit(1)
    elif Path("mcp_server_config.json").exists():
        file_config = load_config_file("mcp_server_config.json")
        print("✅ Loaded default configuration from mcp_server_config.json")
    
    # Create server configuration
    config = create_server_config(args, file_config)
    
    # Display startup information
    print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PRODUCTION MCP SERVER STARTUP                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ Mode: {args.mode:<20} Port: {config.port:<10} Host: {config.host:<15} │
│ Auth: {config.auth_type if config.enable_auth else 'disabled':<20} HTTP: {str(config.enable_http_transport):<10} Collaboration: {str(config.enable_agent_collaboration):<5} │
│ Max Concurrent: {config.max_concurrent_requests:<10} Cache: {str(config.enable_caching):<10} Metrics: {str(config.enable_metrics):<10} │
└─────────────────────────────────────────────────────────────────────────────┘
    """)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    
    try:
        from dataflow_classification_models import db
        print("   ✅ DataFlow models available")
    except ImportError:
        print("   ⚠️  DataFlow models not available (using mock)")
    
    try:
        import jwt
        print("   ✅ JWT support available")
    except ImportError:
        if config.auth_type == "jwt":
            print("   ❌ JWT support not available but JWT auth requested")
            print("      Install PyJWT: pip install PyJWT")
            sys.exit(1)
        else:
            print("   ⚠️  JWT support not available")
    
    try:
        import uvicorn
        print("   ✅ HTTP transport available")
    except ImportError:
        if config.enable_http_transport:
            print("   ⚠️  HTTP transport not available but requested")
            print("      Install uvicorn: pip install uvicorn")
            config.enable_http_transport = False
        else:
            print("   ⚠️  HTTP transport not available")
    
    print("\n🚀 Starting server...")
    
    # Start in appropriate mode
    try:
        if args.mode == "standalone":
            asyncio.run(start_standalone_server(config))
        elif args.mode == "nexus-integration":
            asyncio.run(start_nexus_integration(config))
        elif args.mode == "development":
            start_development_mode(config)
    
    except KeyboardInterrupt:
        print("\n🛑 Startup interrupted")
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
