"""
Nexus Configuration Management
=============================

Centralized configuration for the Nexus Sales Assistant Platform including:
- Environment-specific settings
- Database configuration
- Authentication settings
- WebSocket configuration
- File upload settings
- AI/ML model configuration
- ERP integration settings
- Monitoring and logging configuration
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL", 
        "postgresql://sales_user:sales_password@localhost:5432/sales_assistant"
    ))
    pool_size: int = field(default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "20")))
    pool_max_overflow: int = field(default_factory=lambda: int(os.getenv("DB_MAX_OVERFLOW", "30")))
    pool_recycle: int = field(default_factory=lambda: int(os.getenv("DB_POOL_RECYCLE", "3600")))
    echo: bool = field(default_factory=lambda: os.getenv("DB_ECHO", "false").lower() == "true")
    auto_migrate: bool = field(default_factory=lambda: os.getenv("DB_AUTO_MIGRATE", "true").lower() == "true")
    monitoring: bool = field(default_factory=lambda: os.getenv("DB_MONITORING", "true").lower() == "true")

@dataclass
class AuthConfig:
    """Authentication and authorization settings"""
    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET", "your-secret-key-change-in-production"))
    jwt_algorithm: str = field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    jwt_expiration_hours: int = field(default_factory=lambda: int(os.getenv("JWT_EXPIRATION_HOURS", "24")))
    enable_2fa: bool = field(default_factory=lambda: os.getenv("ENABLE_2FA", "false").lower() == "true")
    password_policy: Dict[str, Any] = field(default_factory=lambda: {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special": True
    })
    session_timeout_minutes: int = field(default_factory=lambda: int(os.getenv("SESSION_TIMEOUT", "1440")))
    max_login_attempts: int = field(default_factory=lambda: int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")))
    lockout_duration_minutes: int = field(default_factory=lambda: int(os.getenv("LOCKOUT_DURATION", "30")))

@dataclass
class ServerConfig:
    """Server and network configuration"""
    api_host: str = field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    api_port: int = field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))
    mcp_host: str = field(default_factory=lambda: os.getenv("MCP_HOST", "0.0.0.0"))
    mcp_port: int = field(default_factory=lambda: int(os.getenv("MCP_PORT", "3001")))
    enable_https: bool = field(default_factory=lambda: os.getenv("ENABLE_HTTPS", "false").lower() == "true")
    ssl_cert_path: Optional[str] = field(default_factory=lambda: os.getenv("SSL_CERT_PATH"))
    ssl_key_path: Optional[str] = field(default_factory=lambda: os.getenv("SSL_KEY_PATH"))
    cors_origins: List[str] = field(default_factory=lambda: json.loads(
        os.getenv("CORS_ORIGINS", '["http://localhost:3000", "https://yourdomain.com"]')
    ))
    rate_limit: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT", "1000")))
    max_request_size: int = field(default_factory=lambda: int(os.getenv("MAX_REQUEST_SIZE", "50")))  # MB

@dataclass
class WebSocketConfig:
    """WebSocket configuration for real-time features"""
    enabled: bool = field(default_factory=lambda: os.getenv("WEBSOCKET_ENABLED", "true").lower() == "true")
    max_connections: int = field(default_factory=lambda: int(os.getenv("WS_MAX_CONNECTIONS", "1000")))
    heartbeat_interval: int = field(default_factory=lambda: int(os.getenv("WS_HEARTBEAT_INTERVAL", "30")))
    message_queue_size: int = field(default_factory=lambda: int(os.getenv("WS_MESSAGE_QUEUE_SIZE", "100")))
    compression: bool = field(default_factory=lambda: os.getenv("WS_COMPRESSION", "true").lower() == "true")
    ping_timeout: int = field(default_factory=lambda: int(os.getenv("WS_PING_TIMEOUT", "20")))
    close_timeout: int = field(default_factory=lambda: int(os.getenv("WS_CLOSE_TIMEOUT", "10")))

@dataclass
class FileUploadConfig:
    """File upload and storage configuration"""
    upload_dir: Path = field(default_factory=lambda: Path(os.getenv("UPLOAD_DIR", "uploads")))
    max_file_size: int = field(default_factory=lambda: int(os.getenv("MAX_FILE_SIZE", "52428800")))  # 50MB in bytes
    allowed_extensions: List[str] = field(default_factory=lambda: json.loads(
        os.getenv("ALLOWED_EXTENSIONS", '["pdf", "docx", "xlsx", "pptx", "txt", "csv", "jpg", "png"]')
    ))
    virus_scan_enabled: bool = field(default_factory=lambda: os.getenv("VIRUS_SCAN_ENABLED", "false").lower() == "true")
    storage_backend: str = field(default_factory=lambda: os.getenv("STORAGE_BACKEND", "local"))  # local, s3, azure
    retention_days: int = field(default_factory=lambda: int(os.getenv("FILE_RETENTION_DAYS", "365")))
    
    # Cloud storage settings
    s3_bucket: Optional[str] = field(default_factory=lambda: os.getenv("S3_BUCKET"))
    s3_region: Optional[str] = field(default_factory=lambda: os.getenv("S3_REGION"))
    azure_container: Optional[str] = field(default_factory=lambda: os.getenv("AZURE_CONTAINER"))

@dataclass
class AIConfig:
    """AI and ML model configuration"""
    default_model: str = field(default_factory=lambda: os.getenv("AI_DEFAULT_MODEL", "gpt-4"))
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    anthropic_api_key: Optional[str] = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    azure_openai_endpoint: Optional[str] = field(default_factory=lambda: os.getenv("AZURE_OPENAI_ENDPOINT"))
    azure_openai_key: Optional[str] = field(default_factory=lambda: os.getenv("AZURE_OPENAI_KEY"))
    
    # Processing settings
    max_tokens: int = field(default_factory=lambda: int(os.getenv("AI_MAX_TOKENS", "4000")))
    temperature: float = field(default_factory=lambda: float(os.getenv("AI_TEMPERATURE", "0.7")))
    timeout_seconds: int = field(default_factory=lambda: int(os.getenv("AI_TIMEOUT", "120")))
    retry_attempts: int = field(default_factory=lambda: int(os.getenv("AI_RETRY_ATTEMPTS", "3")))
    
    # Document processing
    enable_ocr: bool = field(default_factory=lambda: os.getenv("ENABLE_OCR", "true").lower() == "true")
    ocr_language: str = field(default_factory=lambda: os.getenv("OCR_LANGUAGE", "en"))
    extract_tables: bool = field(default_factory=lambda: os.getenv("EXTRACT_TABLES", "true").lower() == "true")
    
    # Quote generation
    enable_smart_pricing: bool = field(default_factory=lambda: os.getenv("ENABLE_SMART_PRICING", "false").lower() == "true")
    pricing_confidence_threshold: float = field(default_factory=lambda: float(os.getenv("PRICING_CONFIDENCE_THRESHOLD", "0.8")))

@dataclass
class ERPConfig:
    """ERP integration configuration"""
    enabled: bool = field(default_factory=lambda: os.getenv("ERP_ENABLED", "false").lower() == "true")
    system_type: str = field(default_factory=lambda: os.getenv("ERP_SYSTEM", "sap"))  # sap, oracle, netsuite, custom
    
    # Connection settings
    endpoint: Optional[str] = field(default_factory=lambda: os.getenv("ERP_ENDPOINT"))
    username: Optional[str] = field(default_factory=lambda: os.getenv("ERP_USERNAME"))
    password: Optional[str] = field(default_factory=lambda: os.getenv("ERP_PASSWORD"))
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("ERP_API_KEY"))
    
    # Sync settings
    sync_interval_hours: int = field(default_factory=lambda: int(os.getenv("ERP_SYNC_INTERVAL", "24")))
    batch_size: int = field(default_factory=lambda: int(os.getenv("ERP_BATCH_SIZE", "100")))
    timeout_seconds: int = field(default_factory=lambda: int(os.getenv("ERP_TIMEOUT", "300")))
    retry_attempts: int = field(default_factory=lambda: int(os.getenv("ERP_RETRY_ATTEMPTS", "3")))
    
    # Data mapping
    product_mapping: Dict[str, str] = field(default_factory=lambda: json.loads(
        os.getenv("ERP_PRODUCT_MAPPING", '{"id": "product_id", "name": "product_name", "price": "list_price"}')
    ))
    customer_mapping: Dict[str, str] = field(default_factory=lambda: json.loads(
        os.getenv("ERP_CUSTOMER_MAPPING", '{"id": "customer_id", "name": "customer_name", "email": "email"}')
    ))

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    enabled: bool = field(default_factory=lambda: os.getenv("MONITORING_ENABLED", "true").lower() == "true")
    metrics_interval: int = field(default_factory=lambda: int(os.getenv("METRICS_INTERVAL", "30")))
    
    # Prometheus settings
    prometheus_enabled: bool = field(default_factory=lambda: os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true")
    prometheus_port: int = field(default_factory=lambda: int(os.getenv("PROMETHEUS_PORT", "9090")))
    
    # Logging configuration
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_format: str = field(default_factory=lambda: os.getenv("LOG_FORMAT", "structured"))  # structured, text
    log_file: Optional[str] = field(default_factory=lambda: os.getenv("LOG_FILE"))
    
    # Health check settings
    health_check_interval: int = field(default_factory=lambda: int(os.getenv("HEALTH_CHECK_INTERVAL", "60")))
    
    # Alert settings
    alert_webhook_url: Optional[str] = field(default_factory=lambda: os.getenv("ALERT_WEBHOOK_URL"))
    alert_email_recipients: List[str] = field(default_factory=lambda: json.loads(
        os.getenv("ALERT_EMAIL_RECIPIENTS", "[]")
    ))

@dataclass
class RedisConfig:
    """Redis configuration for caching and sessions"""
    enabled: bool = field(default_factory=lambda: os.getenv("REDIS_ENABLED", "false").lower() == "true")
    url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    password: Optional[str] = field(default_factory=lambda: os.getenv("REDIS_PASSWORD"))
    max_connections: int = field(default_factory=lambda: int(os.getenv("REDIS_MAX_CONNECTIONS", "20")))
    
    # Cache settings
    default_ttl: int = field(default_factory=lambda: int(os.getenv("REDIS_DEFAULT_TTL", "3600")))
    session_ttl: int = field(default_factory=lambda: int(os.getenv("REDIS_SESSION_TTL", "86400")))
    
    # Key prefixes
    session_prefix: str = field(default_factory=lambda: os.getenv("REDIS_SESSION_PREFIX", "session:"))
    cache_prefix: str = field(default_factory=lambda: os.getenv("REDIS_CACHE_PREFIX", "cache:"))

@dataclass 
class EmailConfig:
    """Email configuration for notifications"""
    enabled: bool = field(default_factory=lambda: os.getenv("EMAIL_ENABLED", "false").lower() == "true")
    smtp_host: Optional[str] = field(default_factory=lambda: os.getenv("SMTP_HOST"))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "587")))
    smtp_username: Optional[str] = field(default_factory=lambda: os.getenv("SMTP_USERNAME"))
    smtp_password: Optional[str] = field(default_factory=lambda: os.getenv("SMTP_PASSWORD"))
    use_tls: bool = field(default_factory=lambda: os.getenv("SMTP_USE_TLS", "true").lower() == "true")
    
    # Email settings
    from_address: str = field(default_factory=lambda: os.getenv("EMAIL_FROM", "noreply@company.com"))
    from_name: str = field(default_factory=lambda: os.getenv("EMAIL_FROM_NAME", "Sales Assistant"))
    
    # Templates
    template_dir: Path = field(default_factory=lambda: Path(os.getenv("EMAIL_TEMPLATE_DIR", "templates/email")))

@dataclass
class SecurityConfig:
    """Security configuration"""
    encryption_key: str = field(default_factory=lambda: os.getenv("ENCRYPTION_KEY", "your-encryption-key-32-chars"))
    
    # Data protection
    enable_field_encryption: bool = field(default_factory=lambda: os.getenv("ENABLE_FIELD_ENCRYPTION", "true").lower() == "true")
    enable_audit_log: bool = field(default_factory=lambda: os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true")
    
    # Request security
    enable_request_signing: bool = field(default_factory=lambda: os.getenv("ENABLE_REQUEST_SIGNING", "false").lower() == "true")
    trusted_proxies: List[str] = field(default_factory=lambda: json.loads(
        os.getenv("TRUSTED_PROXIES", '["127.0.0.1", "::1"]')
    ))
    
    # Content Security Policy
    csp_enabled: bool = field(default_factory=lambda: os.getenv("CSP_ENABLED", "true").lower() == "true")
    csp_policy: str = field(default_factory=lambda: os.getenv("CSP_POLICY", 
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    ))

class NexusConfiguration:
    """Main configuration class that aggregates all settings"""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.auth = AuthConfig()
        self.server = ServerConfig()
        self.websocket = WebSocketConfig()
        self.file_upload = FileUploadConfig()
        self.ai = AIConfig()
        self.erp = ERPConfig()
        self.monitoring = MonitoringConfig()
        self.redis = RedisConfig()
        self.email = EmailConfig()
        self.security = SecurityConfig()
        
        # Environment
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.testing = os.getenv("TESTING", "false").lower() == "true"
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration settings"""
        errors = []
        
        # Validate required settings
        if not self.database.url:
            errors.append("DATABASE_URL is required")
        
        if not self.auth.jwt_secret or self.auth.jwt_secret == "your-secret-key-change-in-production":
            if self.environment == "production":
                errors.append("JWT_SECRET must be set in production")
        
        if self.server.enable_https and (not self.server.ssl_cert_path or not self.server.ssl_key_path):
            errors.append("SSL certificate and key paths required when HTTPS is enabled")
        
        if self.ai.default_model.startswith("gpt") and not self.ai.openai_api_key:
            errors.append("OpenAI API key required for GPT models")
        
        if self.erp.enabled and not self.erp.endpoint:
            errors.append("ERP endpoint required when ERP integration is enabled")
        
        # Validate file upload directory
        if not self.file_upload.upload_dir.exists():
            try:
                self.file_upload.upload_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create upload directory: {e}")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)"""
        sensitive_fields = {"jwt_secret", "password", "api_key", "encryption_key"}
        
        config_dict = {}
        for attr_name in dir(self):
            if not attr_name.startswith("_"):
                attr_value = getattr(self, attr_name)
                if hasattr(attr_value, "__dict__"):
                    # Handle dataclass attributes
                    section_dict = {}
                    for field_name, field_value in attr_value.__dict__.items():
                        if any(sensitive in field_name.lower() for sensitive in sensitive_fields):
                            section_dict[field_name] = "***"
                        else:
                            section_dict[field_name] = field_value
                    config_dict[attr_name] = section_dict
                elif not callable(attr_value):
                    config_dict[attr_name] = attr_value
        
        return config_dict
    
    def get_nexus_config(self) -> Dict[str, Any]:
        """Get configuration specifically for Nexus initialization"""
        return {
            "api_port": self.server.api_port,
            "mcp_port": self.server.mcp_port,
            "enable_auth": True,
            "enable_monitoring": self.monitoring.enabled,
            "rate_limit": self.server.rate_limit,
            "auto_discovery": False,  # We manage workflows manually
            "cors_origins": self.server.cors_origins,
            "max_request_size": self.server.max_request_size,
            "debug": self.debug
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get DataFlow database configuration"""
        return {
            "database_url": self.database.url,
            "pool_size": self.database.pool_size,
            "pool_max_overflow": self.database.pool_max_overflow,
            "pool_recycle": self.database.pool_recycle,
            "monitoring": self.database.monitoring,
            "echo": self.database.echo,
            "auto_migrate": self.database.auto_migrate
        }
    
    def save_to_file(self, file_path: str):
        """Save configuration to JSON file (excluding sensitive data)"""
        config_dict = self.to_dict()
        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'NexusConfiguration':
        """Load configuration from JSON file"""
        with open(file_path, 'r') as f:
            config_data = json.load(f)
        
        config = cls()
        
        # Update configuration from file data
        for section_name, section_data in config_data.items():
            if hasattr(config, section_name) and isinstance(section_data, dict):
                section_obj = getattr(config, section_name)
                if hasattr(section_obj, "__dict__"):
                    for field_name, field_value in section_data.items():
                        if hasattr(section_obj, field_name):
                            setattr(section_obj, field_name, field_value)
        
        return config

# Global configuration instance
config = NexusConfiguration()

# Configuration validation and environment setup functions
def validate_environment():
    """Validate that all required environment variables are set"""
    try:
        config._validate_config()
        return True, []
    except ValueError as e:
        return False, [str(e)]

def create_sample_env_file(file_path: str = ".env.example"):
    """Create a sample environment file with all configuration options"""
    env_content = """# Nexus Sales Assistant Configuration
# Copy this file to .env and update the values

# Environment
ENVIRONMENT=development
DEBUG=true
TESTING=false

# Database Configuration
DATABASE_URL=postgresql://sales_user:sales_password@localhost:5432/sales_assistant
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_RECYCLE=3600
DB_ECHO=false
DB_AUTO_MIGRATE=true
DB_MONITORING=true

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
MCP_HOST=0.0.0.0
MCP_PORT=3001
ENABLE_HTTPS=false
SSL_CERT_PATH=
SSL_KEY_PATH=
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
RATE_LIMIT=1000
MAX_REQUEST_SIZE=50

# Authentication
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ENABLE_2FA=false
SESSION_TIMEOUT=1440
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION=30

# WebSocket Configuration
WEBSOCKET_ENABLED=true
WS_MAX_CONNECTIONS=1000
WS_HEARTBEAT_INTERVAL=30
WS_MESSAGE_QUEUE_SIZE=100
WS_COMPRESSION=true
WS_PING_TIMEOUT=20
WS_CLOSE_TIMEOUT=10

# File Upload
UPLOAD_DIR=uploads
MAX_FILE_SIZE=52428800
ALLOWED_EXTENSIONS=["pdf", "docx", "xlsx", "pptx", "txt", "csv", "jpg", "png"]
VIRUS_SCAN_ENABLED=false
STORAGE_BACKEND=local
FILE_RETENTION_DAYS=365
S3_BUCKET=
S3_REGION=
AZURE_CONTAINER=

# AI Configuration
AI_DEFAULT_MODEL=gpt-4
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_KEY=
AI_MAX_TOKENS=4000
AI_TEMPERATURE=0.7
AI_TIMEOUT=120
AI_RETRY_ATTEMPTS=3
ENABLE_OCR=true
OCR_LANGUAGE=en
EXTRACT_TABLES=true
ENABLE_SMART_PRICING=false
PRICING_CONFIDENCE_THRESHOLD=0.8

# ERP Integration
ERP_ENABLED=false
ERP_SYSTEM=sap
ERP_ENDPOINT=
ERP_USERNAME=
ERP_PASSWORD=
ERP_API_KEY=
ERP_SYNC_INTERVAL=24
ERP_BATCH_SIZE=100
ERP_TIMEOUT=300
ERP_RETRY_ATTEMPTS=3
ERP_PRODUCT_MAPPING={"id": "product_id", "name": "product_name", "price": "list_price"}
ERP_CUSTOMER_MAPPING={"id": "customer_id", "name": "customer_name", "email": "email"}

# Monitoring
MONITORING_ENABLED=true
METRICS_INTERVAL=30
PROMETHEUS_ENABLED=false
PROMETHEUS_PORT=9090
LOG_LEVEL=INFO
LOG_FORMAT=structured
LOG_FILE=
HEALTH_CHECK_INTERVAL=60
ALERT_WEBHOOK_URL=
ALERT_EMAIL_RECIPIENTS=[]

# Redis (Optional)
REDIS_ENABLED=false
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
REDIS_MAX_CONNECTIONS=20
REDIS_DEFAULT_TTL=3600
REDIS_SESSION_TTL=86400
REDIS_SESSION_PREFIX=session:
REDIS_CACHE_PREFIX=cache:

# Email (Optional)
EMAIL_ENABLED=false
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true
EMAIL_FROM=noreply@company.com
EMAIL_FROM_NAME=Sales Assistant
EMAIL_TEMPLATE_DIR=templates/email

# Security
ENCRYPTION_KEY=your-encryption-key-32-chars-long
ENABLE_FIELD_ENCRYPTION=true
ENABLE_AUDIT_LOG=true
ENABLE_REQUEST_SIGNING=false
TRUSTED_PROXIES=["127.0.0.1", "::1"]
CSP_ENABLED=true
CSP_POLICY=default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'
"""
    
    with open(file_path, 'w') as f:
        f.write(env_content)
    
    print(f"Sample environment file created at: {file_path}")
    print("Copy this file to .env and update the values for your environment")

if __name__ == "__main__":
    # Create sample environment file
    create_sample_env_file()
    
    # Validate current configuration
    is_valid, errors = validate_environment()
    if is_valid:
        print("✅ Configuration is valid")
        print(f"🌍 Environment: {config.environment}")
        print(f"🔌 API Port: {config.server.api_port}")
        print(f"🔗 MCP Port: {config.server.mcp_port}")
        print(f"💾 Database: {config.database.url.split('@')[-1] if '@' in config.database.url else config.database.url}")
    else:
        print("❌ Configuration validation failed:")
        for error in errors:
            print(f"   • {error}")