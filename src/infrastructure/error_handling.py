"""
Comprehensive Error Handling System
Implements circuit breakers, retry mechanisms, graceful degradation, and user-friendly error messages
"""

import logging
import traceback
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Type, Union
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
from functools import wraps
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    DATABASE = "database"
    NETWORK = "network"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    USER_INPUT = "user_input"
    EXTERNAL_SERVICE = "external_service"

@dataclass
class ErrorInfo:
    """Structured error information"""
    error_id: str
    message: str
    user_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    resolution_steps: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    failure_rate: float = 0.0
    average_response_time: float = 0.0
    last_failure_time: Optional[datetime] = None

class CircuitBreakerState(Enum):
    CLOSED = "closed"    # Normal operation
    OPEN = "open"        # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker implementation for resilience"""
    
    def __init__(self, name: str, failure_threshold: int = 5, 
                 timeout_seconds: int = 60, reset_timeout: int = 30,
                 success_threshold: int = 3):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.reset_timeout = reset_timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitBreakerState.CLOSED
        self.stats = CircuitBreakerStats()
        self.last_failure_time = None
        self.consecutive_successes = 0
        self._lock = threading.RLock()
        
        logger.info(f"Circuit breaker '{name}' initialized")
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
                else:
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker '{self.name}' is OPEN",
                        self.stats.last_failure_time
                    )
                    
        # Execute function
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            self._record_success(time.time() - start_time)
            return result
            
        except Exception as e:
            self._record_failure(e, time.time() - start_time)
            raise
            
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset"""
        if self.last_failure_time is None:
            return True
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.reset_timeout)
        
    def _record_success(self, response_time: float):
        """Record successful operation"""
        with self._lock:
            self.stats.total_requests += 1
            self.stats.successful_requests += 1
            
            # Update average response time
            total_time = self.stats.average_response_time * (self.stats.total_requests - 1)
            self.stats.average_response_time = (total_time + response_time) / self.stats.total_requests
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.consecutive_successes += 1
                if self.consecutive_successes >= self.success_threshold:
                    self.state = CircuitBreakerState.CLOSED
                    self.consecutive_successes = 0
                    logger.info(f"Circuit breaker '{self.name}' reset to CLOSED state")
                    
            self._update_failure_rate()
            
    def _record_failure(self, exception: Exception, response_time: float):
        """Record failed operation"""
        with self._lock:
            self.stats.total_requests += 1
            self.stats.failed_requests += 1
            self.stats.last_failure_time = datetime.now()
            self.last_failure_time = self.stats.last_failure_time
            
            if isinstance(exception, TimeoutError):
                self.stats.timeout_requests += 1
                
            self._update_failure_rate()
            
            # Check if should open circuit breaker
            if (self.state == CircuitBreakerState.CLOSED and 
                self.stats.failed_requests >= self.failure_threshold):
                self.state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' opened due to failures")
                
            elif self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.OPEN
                self.consecutive_successes = 0
                logger.warning(f"Circuit breaker '{self.name}' reopened from HALF_OPEN")
                
    def _update_failure_rate(self):
        """Update failure rate calculation"""
        if self.stats.total_requests > 0:
            self.stats.failure_rate = self.stats.failed_requests / self.stats.total_requests
            
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            'name': self.name,
            'state': self.state.value,
            'stats': {
                'total_requests': self.stats.total_requests,
                'successful_requests': self.stats.successful_requests,
                'failed_requests': self.stats.failed_requests,
                'timeout_requests': self.stats.timeout_requests,
                'failure_rate': round(self.stats.failure_rate * 100, 2),
                'average_response_time': round(self.stats.average_response_time * 1000, 2)
            },
            'last_failure_time': self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None
        }
        
    def reset(self):
        """Manually reset circuit breaker"""
        with self._lock:
            self.state = CircuitBreakerState.CLOSED
            self.consecutive_successes = 0
            logger.info(f"Circuit breaker '{self.name}' manually reset")

class ErrorHandler:
    """Centralized error handling and recovery"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_counts = defaultdict(int)
        self.fallback_strategies: Dict[str, Callable] = {}
        self._lock = threading.RLock()
        
    def register_circuit_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """Register a new circuit breaker"""
        circuit_breaker = CircuitBreaker(name, **kwargs)
        self.circuit_breakers[name] = circuit_breaker
        return circuit_breaker
        
    def register_fallback(self, operation_name: str, fallback_func: Callable):
        """Register fallback strategy for operation"""
        self.fallback_strategies[operation_name] = fallback_func
        
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """Process and categorize error"""
        context = context or {}
        
        # Generate unique error ID
        error_id = self._generate_error_id(error, context)
        
        # Categorize error
        category, severity = self._categorize_error(error)
        
        # Generate user-friendly message
        user_message = self._generate_user_message(error, category)
        
        # Generate resolution steps
        resolution_steps = self._generate_resolution_steps(error, category)
        
        error_info = ErrorInfo(
            error_id=error_id,
            message=str(error),
            user_message=user_message,
            severity=severity,
            category=category,
            context=context,
            stack_trace=traceback.format_exc(),
            resolution_steps=resolution_steps
        )
        
        # Log error
        self._log_error(error_info)
        
        # Update error statistics
        self.error_counts[f"{category.value}_{severity.value}"] += 1
        
        return error_info
        
    def _generate_error_id(self, error: Exception, context: Dict[str, Any]) -> str:
        """Generate unique error ID for tracking"""
        import hashlib
        error_str = f"{type(error).__name__}_{str(error)}_{str(context)}"
        return hashlib.md5(error_str.encode()).hexdigest()[:8]
        
    def _categorize_error(self, error: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        """Categorize error by type and determine severity"""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Database errors
        if any(keyword in error_type.lower() for keyword in ['database', 'sqlite', 'sql', 'connection']):
            severity = ErrorSeverity.HIGH if 'locked' in error_message else ErrorSeverity.MEDIUM
            return ErrorCategory.DATABASE, severity
            
        # Network errors
        if any(keyword in error_type.lower() for keyword in ['connection', 'timeout', 'network', 'http']):
            return ErrorCategory.NETWORK, ErrorSeverity.MEDIUM
            
        # Validation errors
        if any(keyword in error_type.lower() for keyword in ['value', 'validation', 'format']):
            return ErrorCategory.VALIDATION, ErrorSeverity.LOW
            
        # System errors
        if any(keyword in error_type.lower() for keyword in ['memory', 'disk', 'file', 'permission']):
            return ErrorCategory.SYSTEM, ErrorSeverity.HIGH
            
        # Default categorization
        return ErrorCategory.SYSTEM, ErrorSeverity.MEDIUM
        
    def _generate_user_message(self, error: Exception, category: ErrorCategory) -> str:
        """Generate user-friendly error message"""
        error_message = str(error).lower()
        
        if category == ErrorCategory.DATABASE:
            if 'locked' in error_message:
                return "The system is temporarily busy. Please try again in a few seconds."
            elif 'constraint' in error_message or 'unique' in error_message:
                return "This record already exists. Please check your input and try again."
            else:
                return "There was a problem accessing the database. Please try again."
                
        elif category == ErrorCategory.NETWORK:
            return "Network connection issue. Please check your internet connection and try again."
            
        elif category == ErrorCategory.VALIDATION:
            if 'required' in error_message:
                return "Some required information is missing. Please fill in all required fields."
            elif 'format' in error_message or 'invalid' in error_message:
                return "The information provided is not in the correct format. Please check and try again."
            else:
                return "Please check your input and try again."
                
        elif category == ErrorCategory.SYSTEM:
            return "A system error occurred. Our team has been notified and will resolve this soon."
            
        else:
            return "An unexpected error occurred. Please try again or contact support if the problem persists."
            
    def _generate_resolution_steps(self, error: Exception, category: ErrorCategory) -> List[str]:
        """Generate resolution steps for error"""
        steps = []
        error_message = str(error).lower()
        
        if category == ErrorCategory.DATABASE:
            if 'locked' in error_message:
                steps = [
                    "Wait 5-10 seconds and try again",
                    "If problem persists, refresh the page",
                    "Contact support if issue continues"
                ]
            elif 'constraint' in error_message:
                steps = [
                    "Check for duplicate entries",
                    "Verify all required fields are filled",
                    "Use different values and try again"
                ]
                
        elif category == ErrorCategory.NETWORK:
            steps = [
                "Check your internet connection",
                "Try refreshing the page",
                "Wait a moment and try again"
            ]
            
        elif category == ErrorCategory.VALIDATION:
            steps = [
                "Review all form fields for errors",
                "Ensure required fields are completed",
                "Check data format requirements"
            ]
            
        if not steps:
            steps = [
                "Try the operation again",
                "Refresh the page if needed",
                "Contact support if problem persists"
            ]
            
        return steps
        
    def _log_error(self, error_info: ErrorInfo):
        """Log error with appropriate level"""
        log_message = f"Error {error_info.error_id}: {error_info.message}"
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra={'error_info': error_info})
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(log_message, extra={'error_info': error_info})
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra={'error_info': error_info})
        else:
            logger.info(log_message, extra={'error_info': error_info})

class RetryManager:
    """Advanced retry mechanism with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 0.1, 
                 max_delay: float = 60.0, exponential_base: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        
    def retry_with_backoff(self, func: Callable, retryable_exceptions: tuple = None,
                          context: Dict[str, Any] = None) -> Any:
        """Execute function with exponential backoff retry"""
        retryable_exceptions = retryable_exceptions or (Exception,)
        context = context or {}
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func()
            except retryable_exceptions as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (self.exponential_base ** attempt),
                        self.max_delay
                    )
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s")
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries + 1} attempts failed")
                    
        raise last_exception

# Custom exceptions
class CircuitBreakerOpenException(Exception):
    """Circuit breaker is open"""
    def __init__(self, message: str, last_failure_time: Optional[datetime] = None):
        super().__init__(message)
        self.last_failure_time = last_failure_time

class GracefulDegradationException(Exception):
    """Service degraded but functioning"""
    pass

# Decorators for error handling
def with_circuit_breaker(breaker_name: str, **breaker_kwargs):
    """Decorator to apply circuit breaker to function"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = get_error_handler()
            
            # Get or create circuit breaker
            if breaker_name not in handler.circuit_breakers:
                handler.register_circuit_breaker(breaker_name, **breaker_kwargs)
                
            circuit_breaker = handler.circuit_breakers[breaker_name]
            return circuit_breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator

def with_retry(max_retries: int = 3, retryable_exceptions: tuple = None):
    """Decorator to add retry logic to function"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_manager = RetryManager(max_retries=max_retries)
            return retry_manager.retry_with_backoff(
                lambda: func(*args, **kwargs),
                retryable_exceptions=retryable_exceptions
            )
        return wrapper
    return decorator

def with_error_handling(operation_name: str = None):
    """Decorator to add comprehensive error handling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = get_error_handler()
                context = {
                    'function': func.__name__,
                    'operation': operation_name or func.__name__,
                    'args': str(args)[:200],
                    'kwargs': str(kwargs)[:200]
                }
                error_info = handler.handle_error(e, context)
                
                # Try fallback if available
                fallback_name = operation_name or func.__name__
                if fallback_name in handler.fallback_strategies:
                    logger.info(f"Attempting fallback for {fallback_name}")
                    try:
                        return handler.fallback_strategies[fallback_name](*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(f"Fallback also failed: {fallback_error}")
                        
                raise e
        return wrapper
    return decorator

# Global error handler instance
_error_handler: Optional[ErrorHandler] = None

def get_error_handler() -> ErrorHandler:
    """Get global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler

def setup_error_handling():
    """Setup default error handling configuration"""
    handler = get_error_handler()
    
    # Register default circuit breakers
    handler.register_circuit_breaker("database", failure_threshold=5, timeout_seconds=30)
    handler.register_circuit_breaker("external_api", failure_threshold=3, timeout_seconds=60)
    
    # Register fallback strategies
    def database_fallback(*args, **kwargs):
        """Fallback for database operations"""
        logger.warning("Using database fallback - returning cached/default data")
        return {"status": "degraded", "message": "Using cached data"}
        
    def api_fallback(*args, **kwargs):
        """Fallback for API operations"""
        logger.warning("Using API fallback - returning minimal functionality")
        return {"status": "limited", "message": "Limited functionality available"}
        
    handler.register_fallback("database_operation", database_fallback)
    handler.register_fallback("api_operation", api_fallback)
    
    logger.info("Error handling system initialized")

# Initialize error handling on module import
setup_error_handling()