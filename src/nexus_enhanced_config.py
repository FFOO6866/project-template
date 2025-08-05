"""
Enhanced Nexus Configuration for Multi-Channel Frontend Integration
================================================================

Optimized configuration for Nexus platform focusing on:
- Performance optimization and caching strategies
- Enhanced CORS and security headers for Next.js integration
- WebSocket optimization for real-time features
- Production-ready monitoring and health checks
- Multi-channel deployment configuration
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from functools import lru_cache
from dataclasses import dataclass, field

from nexus_config import NexusConfiguration, config as base_config


@dataclass
class PerformanceConfig:
    """Performance optimization configuration"""
    # Request handling
    request_timeout: int = field(default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT", "30")))
    max_concurrent_requests: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_REQUESTS", "100")))
    
    # Caching
    cache_ttl_seconds: int = field(default_factory=lambda: int(os.getenv("CACHE_TTL_SECONDS", "300")))
    cache_max_entries: int = field(default_factory=lambda: int(os.getenv("CACHE_MAX_ENTRIES", "1000")))
    
    # Response compression
    gzip_minimum_size: int = field(default_factory=lambda: int(os.getenv("GZIP_MIN_SIZE", "1000")))
    enable_brotli: bool = field(default_factory=lambda: os.getenv("ENABLE_BROTLI", "true").lower() == "true")
    
    # Connection pooling
    database_pool_size: int = field(default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "20")))
    database_pool_max_overflow: int = field(default_factory=lambda: int(os.getenv("DB_POOL_MAX_OVERFLOW", "30")))
    
    # JWT optimization
    jwt_refresh_threshold_minutes: int = field(default_factory=lambda: int(os.getenv("JWT_REFRESH_THRESHOLD", "30")))
    jwt_refresh_token_days: int = field(default_factory=lambda: int(os.getenv("JWT_REFRESH_DAYS", "7")))


@dataclass
class CORSConfig:
    """Enhanced CORS configuration for frontend integration"""
    # Development origins
    development_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:3000",    # Next.js default
        "http://localhost:3001",    # Next.js alternative
        "http://127.0.0.1:3000",    # IPv4 localhost
        "http://0.0.0.0:3000",      # All interfaces
    ])
    
    # Production origins
    production_origins: List[str] = field(default_factory=lambda: json.loads(
        os.getenv("PRODUCTION_ORIGINS", '["https://yourdomain.com", "https://*.yourdomain.com"]')
    ))
    
    # CORS settings
    allow_credentials: bool = True
    allow_methods: List[str] = field(default_factory=lambda: [
        "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"
    ])
    allow_headers: List[str] = field(default_factory=lambda: [
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRF-Token",
        "Cache-Control",
        "X-Total-Count",
        "X-Page-Count"
    ])
    expose_headers: List[str] = field(default_factory=lambda: [
        "X-Total-Count", "X-Page-Count", "Link", "X-RateLimit-Remaining"
    ])
    max_age: int = field(default_factory=lambda: int(os.getenv("CORS_MAX_AGE", "3600")))


@dataclass
class SecurityConfig:
    """Enhanced security configuration"""
    # Security headers
    security_headers: Dict[str, str] = field(default_factory=lambda: {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    })
    
    # Rate limiting
    rate_limit_per_minute: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "1000")))
    rate_limit_burst: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_BURST", "100")))
    
    # Request validation
    max_request_size_mb: int = field(default_factory=lambda: int(os.getenv("MAX_REQUEST_SIZE_MB", "50")))
    enable_request_logging: bool = field(default_factory=lambda: os.getenv("ENABLE_REQUEST_LOGGING", "true").lower() == "true")


@dataclass
class WebSocketConfig:
    """Enhanced WebSocket configuration"""
    # Connection settings
    max_connections: int = field(default_factory=lambda: int(os.getenv("WS_MAX_CONNECTIONS", "1000")))
    heartbeat_interval: int = field(default_factory=lambda: int(os.getenv("WS_HEARTBEAT_INTERVAL", "30")))
    ping_timeout: int = field(default_factory=lambda: int(os.getenv("WS_PING_TIMEOUT", "20")))
    close_timeout: int = field(default_factory=lambda: int(os.getenv("WS_CLOSE_TIMEOUT", "10")))
    
    # Message handling
    message_queue_size: int = field(default_factory=lambda: int(os.getenv("WS_MESSAGE_QUEUE_SIZE", "100")))
    max_message_size: int = field(default_factory=lambda: int(os.getenv("WS_MAX_MESSAGE_SIZE", "1024000")))  # 1MB
    
    # Compression and optimization
    enable_compression: bool = field(default_factory=lambda: os.getenv("WS_COMPRESSION", "true").lower() == "true")
    compression_threshold: int = field(default_factory=lambda: int(os.getenv("WS_COMPRESSION_THRESHOLD", "1024")))
    
    # Authentication
    token_validation_interval: int = field(default_factory=lambda: int(os.getenv("WS_TOKEN_VALIDATION_INTERVAL", "300")))  # 5 minutes


@dataclass
class HealthCheckConfig:
    """Health check and monitoring configuration"""
    # Health check endpoints
    enable_health_checks: bool = field(default_factory=lambda: os.getenv("ENABLE_HEALTH_CHECKS", "true").lower() == "true")
    health_check_interval: int = field(default_factory=lambda: int(os.getenv("HEALTH_CHECK_INTERVAL", "60")))
    
    # Dependency checks
    check_database: bool = field(default_factory=lambda: os.getenv("HEALTH_CHECK_DATABASE", "true").lower() == "true")
    check_redis: bool = field(default_factory=lambda: os.getenv("HEALTH_CHECK_REDIS", "true").lower() == "true")
    check_external_apis: bool = field(default_factory=lambda: os.getenv("HEALTH_CHECK_EXTERNAL_APIS", "false").lower() == "true")
    
    # Timeouts
    database_timeout: int = field(default_factory=lambda: int(os.getenv("HEALTH_DB_TIMEOUT", "5")))
    redis_timeout: int = field(default_factory=lambda: int(os.getenv("HEALTH_REDIS_TIMEOUT", "3")))
    external_api_timeout: int = field(default_factory=lambda: int(os.getenv("HEALTH_API_TIMEOUT", "10")))


class EnhancedNexusConfiguration(NexusConfiguration):
    """Enhanced Nexus configuration with frontend integration optimizations"""
    
    def __init__(self):
        super().__init__()
        
        # Enhanced configurations
        self.performance = PerformanceConfig()
        self.cors = CORSConfig()
        self.enhanced_security = SecurityConfig()
        self.enhanced_websocket = WebSocketConfig()
        self.health_check = HealthCheckConfig()
        
        # Response cache for performance
        self.response_cache: Dict[str, tuple] = {}
        
        # Validate enhanced configuration
        self._validate_enhanced_config()
    
    def _validate_enhanced_config(self):
        """Validate enhanced configuration settings"""
        errors = []
        
        # Validate performance settings
        if self.performance.request_timeout <= 0:
            errors.append("Request timeout must be positive")
        
        if self.performance.cache_ttl_seconds <= 0:
            errors.append("Cache TTL must be positive")
        
        # Validate CORS origins
        if not self.cors.development_origins and not self.cors.production_origins:
            errors.append("At least one CORS origin must be configured")
        
        # Validate WebSocket settings
        if self.enhanced_websocket.max_connections <= 0:
            errors.append("WebSocket max connections must be positive")
        
        if errors:
            raise ValueError(f"Enhanced configuration validation failed: {'; '.join(errors)}")
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins based on environment"""
        if self.environment == "production":
            return self.cors.production_origins
        else:
            return self.cors.development_origins + self.cors.production_origins
    
    def get_nexus_enhanced_config(self) -> Dict[str, Any]:
        """Get enhanced configuration for Nexus initialization"""
        base_nexus_config = self.get_nexus_config()
        
        return {
            **base_nexus_config,
            # Performance settings
            "request_timeout": self.performance.request_timeout,
            "max_concurrent_requests": self.performance.max_concurrent_requests,
            "enable_compression": True,
            "compression_threshold": self.performance.gzip_minimum_size,
            
            # Enhanced CORS
            "cors_origins": self.get_cors_origins(),
            "cors_methods": self.cors.allow_methods,
            "cors_headers": self.cors.allow_headers,
            "cors_max_age": self.cors.max_age,
            
            # WebSocket optimization
            "websocket_max_connections": self.enhanced_websocket.max_connections,
            "websocket_heartbeat_interval": self.enhanced_websocket.heartbeat_interval,
            "websocket_compression": self.enhanced_websocket.enable_compression,
            
            # Security
            "security_headers": self.enhanced_security.security_headers,
            "rate_limit_per_minute": self.enhanced_security.rate_limit_per_minute,
            "max_request_size_mb": self.enhanced_security.max_request_size_mb,
            
            # Health checks
            "enable_health_checks": self.health_check.enable_health_checks,
            "health_check_interval": self.health_check.health_check_interval,
        }
    
    def create_cache_key(self, endpoint: str, params: dict = None, user_id: int = None) -> str:
        """Create cache key for response caching"""
        key_data = {
            "endpoint": endpoint,
            "params": params or {},
            "user_id": user_id
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_cached_response(self, cache_key: str) -> Union[dict, None]:
        """Get cached response if valid"""
        if cache_key in self.response_cache:
            response_data, timestamp = self.response_cache[cache_key]
            if datetime.now().timestamp() - timestamp < self.performance.cache_ttl_seconds:
                return response_data
            else:
                # Remove expired cache entry
                del self.response_cache[cache_key]
        return None
    
    def set_cached_response(self, cache_key: str, response_data: dict):
        """Cache response data"""
        self.response_cache[cache_key] = (response_data, datetime.now().timestamp())
        
        # Simple cache cleanup - remove old entries if cache gets too large
        if len(self.response_cache) > self.performance.cache_max_entries:
            # Remove oldest entries
            oldest_keys = sorted(
                self.response_cache.keys(), 
                key=lambda k: self.response_cache[k][1]
            )[:100]
            for key in oldest_keys:
                del self.response_cache[key]
    
    def clear_cache(self, pattern: str = None):
        """Clear cache entries, optionally matching a pattern"""
        if pattern:
            keys_to_remove = [k for k in self.response_cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.response_cache[key]
        else:
            self.response_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = datetime.now().timestamp()
        expired_count = sum(
            1 for _, timestamp in self.response_cache.values()
            if now - timestamp >= self.performance.cache_ttl_seconds
        )
        
        return {
            "total_entries": len(self.response_cache),
            "expired_entries": expired_count,
            "valid_entries": len(self.response_cache) - expired_count,
            "cache_hit_ratio": getattr(self, '_cache_hits', 0) / max(getattr(self, '_cache_requests', 1), 1),
            "ttl_seconds": self.performance.cache_ttl_seconds
        }
    
    def get_multi_channel_config(self) -> Dict[str, Any]:
        """Get configuration for multi-channel deployment"""
        return {
            "api": {
                "enabled": True,
                "host": self.server.api_host,
                "port": self.server.api_port,
                "https": self.server.enable_https,
                "cors_origins": self.get_cors_origins(),
                "rate_limit": self.enhanced_security.rate_limit_per_minute,
                "timeout": self.performance.request_timeout
            },
            "cli": {
                "enabled": True,
                "commands": [
                    "create-user",
                    "sync-erp-products", 
                    "generate-reports",
                    "health-check",
                    "cache-stats"
                ]
            },
            "mcp": {
                "enabled": True,
                "host": self.server.mcp_host,
                "port": self.server.mcp_port,
                "tools": [
                    "get_customer_info",
                    "create_quote",
                    "search_products",
                    "upload_document",
                    "get_health_status"
                ]
            },
            "websocket": {
                "enabled": self.websocket.enabled,
                "endpoint": "/ws/{client_id}",
                "authentication": "jwt_token_required",
                "max_connections": self.enhanced_websocket.max_connections,
                "heartbeat_interval": self.enhanced_websocket.heartbeat_interval
            }
        }
    
    def export_frontend_config(self) -> Dict[str, Any]:
        """Export configuration for frontend applications"""
        return {
            "api": {
                "base_url": f"{'https' if self.server.enable_https else 'http'}://{self.server.api_host}:{self.server.api_port}",
                "timeout": self.performance.request_timeout * 1000,  # Convert to milliseconds
                "max_retries": 3,
                "retry_delay": 1000  # 1 second
            },
            "websocket": {
                "url": f"{'wss' if self.server.enable_https else 'ws'}://{self.server.api_host}:{self.server.api_port}/ws",
                "heartbeat_interval": self.enhanced_websocket.heartbeat_interval * 1000,
                "reconnect_interval": 5000,  # 5 seconds
                "max_reconnect_attempts": 5
            },
            "auth": {
                "token_refresh_threshold": self.performance.jwt_refresh_threshold_minutes * 60 * 1000,  # milliseconds
                "login_endpoint": "/api/auth/login",
                "refresh_endpoint": "/api/auth/refresh",
                "logout_endpoint": "/api/auth/logout"
            },
            "features": {
                "file_upload": {
                    "max_size": self.file_upload.max_file_size,
                    "allowed_types": self.file_upload.allowed_extensions,
                    "endpoint": "/api/files/upload"
                },
                "real_time": {
                    "enabled": self.websocket.enabled,
                    "notifications": True,
                    "chat": True
                }
            }
        }


# Global enhanced configuration instance
enhanced_config = EnhancedNexusConfiguration()


def get_frontend_config_json() -> str:
    """Get frontend configuration as JSON string"""
    return json.dumps(enhanced_config.export_frontend_config(), indent=2)


def save_frontend_config(file_path: str = "frontend-config.json"):
    """Save frontend configuration to JSON file"""
    with open(file_path, 'w') as f:
        f.write(get_frontend_config_json())
    print(f"Frontend configuration saved to: {file_path}")


if __name__ == "__main__":
    # Validate enhanced configuration
    try:
        print("✅ Enhanced Nexus configuration is valid")
        print(f"🌍 Environment: {enhanced_config.environment}")
        print(f"🔌 API: {enhanced_config.server.api_host}:{enhanced_config.server.api_port}")
        print(f"🔗 MCP: {enhanced_config.server.mcp_host}:{enhanced_config.server.mcp_port}")
        print(f"🚀 WebSocket: {enhanced_config.websocket.enabled}")
        print(f"⚡ Performance: {enhanced_config.performance.request_timeout}s timeout, {enhanced_config.performance.cache_ttl_seconds}s cache TTL")
        print(f"🛡️  Security: {len(enhanced_config.enhanced_security.security_headers)} headers, {enhanced_config.enhanced_security.rate_limit_per_minute}/min rate limit")
        print(f"🌐 CORS Origins: {len(enhanced_config.get_cors_origins())} configured")
        
        # Save frontend configuration
        save_frontend_config()
        
    except Exception as e:
        print(f"❌ Enhanced configuration validation failed: {e}")