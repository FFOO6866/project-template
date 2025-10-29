"""
Input Sanitization Library - Phase 2 Security Remediation
========================================================

Comprehensive input sanitization for preventing security vulnerabilities:
- SQL injection prevention
- XSS (Cross-Site Scripting) prevention  
- Path traversal prevention
- Command injection prevention
- Size limit enforcement
- Type validation

Used by all Kailash SDK nodes to ensure secure parameter processing.
"""

import re
import os
import html
import urllib.parse
from typing import Any, Dict, List, Union, Optional, Tuple
from pathlib import Path
import hashlib
import json
import unicodedata


class SecurityViolation(Exception):
    """Raised when a security violation is detected"""
    def __init__(self, violation_type: str, original_value: str, details: str = ""):
        self.violation_type = violation_type
        self.original_value = original_value
        self.details = details
        super().__init__(f"Security violation ({violation_type}): {details}")


class InputSanitizer:
    """
    Comprehensive input sanitization for security compliance.
    
    Provides methods to sanitize various types of input to prevent
    common security vulnerabilities while maintaining functionality.
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize the input sanitizer.
        
        Args:
            strict_mode: If True, raises exceptions for serious violations.
                        If False, sanitizes and logs violations.
        """
        self.strict_mode = strict_mode
        self.violation_log = []
        
        # SQL injection patterns (compiled for performance)
        self.sql_patterns = [
            re.compile(r"'.*?(?:OR|AND).*?'.*?'", re.IGNORECASE),
            re.compile(r"'.*?UNION.*?SELECT", re.IGNORECASE),
            re.compile(r"'.*?DROP.*?TABLE", re.IGNORECASE),
            re.compile(r"'.*?INSERT.*?INTO", re.IGNORECASE),
            re.compile(r"'.*?DELETE.*?FROM", re.IGNORECASE),
            re.compile(r"'.*?UPDATE.*?SET", re.IGNORECASE),
            re.compile(r"--.*?$", re.MULTILINE),
            re.compile(r"/\*.*?\*/", re.DOTALL),
            re.compile(r"exec\s*\(", re.IGNORECASE),
            re.compile(r"sp_\w+", re.IGNORECASE),
            re.compile(r"xp_\w+", re.IGNORECASE),
            re.compile(r";\s*(?:DROP|DELETE|INSERT|UPDATE|CREATE|ALTER|EXEC)", re.IGNORECASE)
        ]
        
        # XSS patterns (compiled for performance)
        self.xss_patterns = [
            re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"on\w+\s*=", re.IGNORECASE),
            re.compile(r"<iframe[^>]*>.*?</iframe>", re.IGNORECASE | re.DOTALL),
            re.compile(r"<object[^>]*>.*?</object>", re.IGNORECASE | re.DOTALL),
            re.compile(r"<embed[^>]*>.*?</embed>", re.IGNORECASE | re.DOTALL),
            re.compile(r"<applet[^>]*>.*?</applet>", re.IGNORECASE | re.DOTALL),
            re.compile(r"<meta[^>]*http-equiv", re.IGNORECASE),
            re.compile(r"vbscript:", re.IGNORECASE),
            re.compile(r"data:\s*text/html", re.IGNORECASE),
            re.compile(r"expression\s*\(", re.IGNORECASE)
        ]
        
        # Path traversal patterns
        self.path_traversal_patterns = [
            re.compile(r"\.\.[\\/]"),
            re.compile(r"\.\.%2[fF]"),
            re.compile(r"\.\.%5[cC]"),
            re.compile(r"%2e%2e[\\/]"),
            re.compile(r"~[\\/]"),
            re.compile(r"\$\{.*?\}")  # Variable expansion
        ]
        
        # Command injection patterns
        self.command_patterns = [
            re.compile(r"[;&|`]", re.IGNORECASE),
            re.compile(r"\$\(.*?\)", re.IGNORECASE),
            re.compile(r"`.*?`", re.IGNORECASE),
            re.compile(r">\s*&", re.IGNORECASE),
            re.compile(r"2>&1", re.IGNORECASE),
            re.compile(r"\|\s*\w+", re.IGNORECASE)
        ]
        
        # Dangerous file extensions
        self.dangerous_extensions = {
            '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.vbe', '.js', '.jse',
            '.ws', '.wsf', '.wsc', '.wsh', '.ps1', '.ps1xml', '.ps2', '.ps2xml', '.psc1',
            '.psc2', '.msh', '.msh1', '.msh2', '.mshxml', '.msh1xml', '.msh2xml',
            '.scf', '.lnk', '.inf', '.reg', '.app', '.jar', '.class', '.dex', '.apk'
        }
        
        # Safe filename characters
        self.safe_filename_pattern = re.compile(r'^[a-zA-Z0-9._-]+$')
        
    def sanitize_string(self, value: str, max_length: int = 1000, 
                       context: str = "general") -> str:
        """
        Sanitize a string input for security vulnerabilities.
        
        Args:
            value: String to sanitize
            max_length: Maximum allowed length
            context: Context for sanitization (sql, xss, path, filename)
        
        Returns:
            Sanitized string
        
        Raises:
            SecurityViolation: If strict_mode is True and serious violation found
        """
        if not isinstance(value, str):
            value = str(value)
        
        original_value = value
        violations = []
        
        # 1. Length check
        if len(value) > max_length:
            value = value[:max_length]
            violations.append(f"Truncated to {max_length} characters")
        
        # 2. Unicode normalization to prevent bypass attempts
        value = unicodedata.normalize('NFKC', value)
        
        # 3. Context-specific sanitization
        if context in ["sql", "general"]:
            value, sql_violations = self._sanitize_sql(value)
            violations.extend(sql_violations)
        
        if context in ["xss", "general"]:
            value, xss_violations = self._sanitize_xss(value)
            violations.extend(xss_violations)
        
        if context in ["path", "general"]:
            value, path_violations = self._sanitize_path_traversal(value)
            violations.extend(path_violations)
        
        if context == "filename":
            value, filename_violations = self._sanitize_filename(value)
            violations.extend(filename_violations)
        
        # 4. Command injection check (for all contexts)
        value, cmd_violations = self._sanitize_command_injection(value)
        violations.extend(cmd_violations)
        
        # 5. Log violations
        if violations:
            self._log_violation("string_sanitization", original_value, violations)
            
            if self.strict_mode and self._is_serious_violation(violations):
                raise SecurityViolation(
                    "string_sanitization",
                    original_value,
                    f"Serious security violations: {'; '.join(violations)}"
                )
        
        return value
    
    def sanitize_dict(self, value: Dict[str, Any], max_depth: int = 5, 
                     max_items: int = 100) -> Dict[str, Any]:
        """
        Sanitize a dictionary recursively.
        
        Args:
            value: Dictionary to sanitize
            max_depth: Maximum recursion depth
            max_items: Maximum number of items per dictionary
        
        Returns:
            Sanitized dictionary
        """
        if not isinstance(value, dict):
            return {}
        
        if max_depth <= 0:
            return {"error": "Maximum depth exceeded"}
        
        sanitized = {}
        items_processed = 0
        
        for key, val in value.items():
            if items_processed >= max_items:
                sanitized["_truncated"] = f"Dictionary truncated at {max_items} items"
                break
            
            # Sanitize key
            clean_key = self.sanitize_string(str(key)[:100], context="general")
            
            # Sanitize value based on type
            if isinstance(val, str):
                clean_val = self.sanitize_string(val, context="general")
            elif isinstance(val, dict):
                clean_val = self.sanitize_dict(val, max_depth - 1, max_items)
            elif isinstance(val, list):
                clean_val = self.sanitize_list(val, max_depth - 1, max_items)
            elif isinstance(val, (int, float, bool)):
                clean_val = val
            else:
                clean_val = self.sanitize_string(str(val), context="general")
            
            sanitized[clean_key] = clean_val
            items_processed += 1
        
        return sanitized
    
    def sanitize_list(self, value: List[Any], max_depth: int = 5, 
                     max_items: int = 100) -> List[Any]:
        """
        Sanitize a list recursively.
        
        Args:
            value: List to sanitize
            max_depth: Maximum recursion depth
            max_items: Maximum number of items
        
        Returns:
            Sanitized list
        """
        if not isinstance(value, list):
            return []
        
        if max_depth <= 0:
            return ["Maximum depth exceeded"]
        
        sanitized = []
        
        for i, item in enumerate(value[:max_items]):
            if isinstance(item, str):
                clean_item = self.sanitize_string(item, context="general")
            elif isinstance(item, dict):
                clean_item = self.sanitize_dict(item, max_depth - 1, max_items)
            elif isinstance(item, list):
                clean_item = self.sanitize_list(item, max_depth - 1, max_items)
            elif isinstance(item, (int, float, bool)):
                clean_item = item
            else:
                clean_item = self.sanitize_string(str(item), context="general")
            
            sanitized.append(clean_item)
        
        if len(value) > max_items:
            sanitized.append(f"List truncated at {max_items} items")
        
        return sanitized
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename for safe storage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        if not isinstance(filename, str):
            filename = str(filename)
        
        original = filename
        violations = []
        
        # Basic sanitization
        filename = self.sanitize_string(filename, max_length=255, context="filename")
        
        # Extract extension safely
        try:
            name_part = Path(filename).stem
            extension = Path(filename).suffix.lower()
        except:
            name_part = filename
            extension = ""
        
        # Check for dangerous extensions
        if extension in self.dangerous_extensions:
            extension = ".txt"  # Replace with safe extension
            violations.append(f"Dangerous extension {Path(original).suffix} replaced")
        
        # Sanitize name part
        name_part = re.sub(r'[^\w.-]', '_', name_part)
        
        # Ensure it doesn't start with dot (hidden files)
        if name_part.startswith('.'):
            name_part = 'file_' + name_part[1:]
        
        # Combine parts
        sanitized = name_part + extension
        
        # Ensure minimum length
        if len(sanitized) < 1:
            sanitized = f"sanitized_file_{hashlib.md5(original.encode()).hexdigest()[:8]}.txt"
        
        if violations:
            self._log_violation("filename_sanitization", original, violations)
        
        return sanitized
    
    def sanitize_file_path(self, file_path: str, allowed_base_paths: List[str] = None) -> str:
        """
        Sanitize a file path to prevent directory traversal.
        
        Args:
            file_path: File path to sanitize
            allowed_base_paths: List of allowed base paths
            
        Returns:
            Sanitized file path
        """
        if not isinstance(file_path, str):
            file_path = str(file_path)
        
        original = file_path
        violations = []
        
        # Basic string sanitization
        file_path = self.sanitize_string(file_path, max_length=1000, context="path")
        
        try:
            # Normalize path
            normalized_path = os.path.normpath(file_path)
            
            # Check for path traversal
            if ".." in normalized_path:
                normalized_path = normalized_path.replace("..", "")
                violations.append("Path traversal attempt removed")
            
            # Convert to use forward slashes
            normalized_path = normalized_path.replace("\\", "/")
            
            # Remove leading slash to prevent absolute path access
            normalized_path = normalized_path.lstrip("/")
            
            # Validate against allowed base paths
            if allowed_base_paths:
                allowed = False
                for base_path in allowed_base_paths:
                    if normalized_path.startswith(base_path):
                        allowed = True
                        break
                
                if not allowed:
                    # If path not allowed, create safe alternative
                    safe_filename = self.sanitize_filename(os.path.basename(normalized_path))
                    normalized_path = f"safe_storage/{safe_filename}"
                    violations.append("Path restricted to safe storage area")
            
            sanitized_path = normalized_path
            
        except Exception as e:
            # If path processing fails, create safe alternative
            safe_filename = self.sanitize_filename(os.path.basename(file_path))
            sanitized_path = f"safe_storage/{safe_filename}"
            violations.append(f"Path processing failed: {str(e)}")
        
        if violations:
            self._log_violation("file_path_sanitization", original, violations)
        
        return sanitized_path
    
    def validate_parameter_size(self, value: Any, max_size_mb: float = 10.0) -> bool:
        """
        Validate that a parameter doesn't exceed size limits.
        
        Args:
            value: Value to check
            max_size_mb: Maximum size in megabytes
            
        Returns:
            True if size is acceptable, False otherwise
        """
        try:
            # Estimate size by JSON serialization
            json_str = json.dumps(value, default=str)
            size_bytes = len(json_str.encode('utf-8'))
            size_mb = size_bytes / (1024 * 1024)
            
            if size_mb > max_size_mb:
                self._log_violation(
                    "parameter_size",
                    str(type(value)),
                    [f"Parameter size {size_mb:.2f}MB exceeds limit {max_size_mb}MB"]
                )
                return False
            
            return True
            
        except Exception as e:
            self._log_violation(
                "parameter_size",
                str(type(value)),
                [f"Size validation failed: {str(e)}"]
            )
            return False
    
    def sanitize_sql_query(self, query: str) -> str:
        """
        Specialized SQL query sanitization.
        
        Args:
            query: SQL query to sanitize
            
        Returns:
            Sanitized query string
        """
        if not isinstance(query, str):
            query = str(query)
        
        original = query
        violations = []
        
        # Remove dangerous SQL patterns
        for pattern in self.sql_patterns:
            if pattern.search(query):
                query = pattern.sub("", query)
                violations.append(f"Removed SQL pattern: {pattern.pattern}")
        
        # Remove dangerous keywords
        dangerous_keywords = [
            "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE",
            "EXEC", "EXECUTE", "sp_", "xp_", "UNION", "SELECT"
        ]
        
        for keyword in dangerous_keywords:
            if keyword.upper() in query.upper():
                query = re.sub(re.escape(keyword), "", query, flags=re.IGNORECASE)
                violations.append(f"Removed dangerous keyword: {keyword}")
        
        # Limit query length
        if len(query) > 1000:
            query = query[:1000]
            violations.append("Query truncated to 1000 characters")
        
        if violations:
            self._log_violation("sql_query_sanitization", original, violations)
            
            if self.strict_mode:
                raise SecurityViolation(
                    "sql_injection",
                    original,
                    f"SQL injection detected: {'; '.join(violations)}"
                )
        
        return query.strip()
    
    def _sanitize_sql(self, value: str) -> Tuple[str, List[str]]:
        """Internal SQL sanitization"""
        violations = []
        
        for pattern in self.sql_patterns:
            if pattern.search(value):
                value = pattern.sub("", value)
                violations.append(f"SQL injection pattern removed")
        
        return value, violations
    
    def _sanitize_xss(self, value: str) -> Tuple[str, List[str]]:
        """Internal XSS sanitization"""
        violations = []
        
        # HTML encode dangerous characters
        value = html.escape(value, quote=True)
        
        # Remove dangerous patterns
        for pattern in self.xss_patterns:
            if pattern.search(value):
                value = pattern.sub("", value)
                violations.append("XSS pattern removed")
        
        return value, violations
    
    def _sanitize_path_traversal(self, value: str) -> Tuple[str, List[str]]:
        """Internal path traversal sanitization"""
        violations = []
        
        for pattern in self.path_traversal_patterns:
            if pattern.search(value):
                value = pattern.sub("", value)
                violations.append("Path traversal pattern removed")
        
        return value, violations
    
    def _sanitize_filename(self, value: str) -> Tuple[str, List[str]]:
        """Internal filename sanitization"""
        violations = []
        
        # Check for dangerous characters
        if not self.safe_filename_pattern.match(value):
            # Replace unsafe characters
            value = re.sub(r'[^\w.-]', '_', value)
            violations.append("Unsafe filename characters replaced")
        
        return value, violations
    
    def _sanitize_command_injection(self, value: str) -> Tuple[str, List[str]]:
        """Internal command injection sanitization"""
        violations = []
        
        for pattern in self.command_patterns:
            if pattern.search(value):
                value = pattern.sub("", value)
                violations.append("Command injection pattern removed")
        
        return value, violations
    
    def _is_serious_violation(self, violations: List[str]) -> bool:
        """Check if violations are serious enough to raise exception"""
        serious_keywords = [
            "SQL injection", "DROP TABLE", "DELETE FROM", "EXEC",
            "script tag", "javascript:", "Command injection"
        ]
        
        violations_text = " ".join(violations).lower()
        return any(keyword.lower() in violations_text for keyword in serious_keywords)
    
    def _log_violation(self, violation_type: str, original_value: str, details: List[str]):
        """Log a security violation"""
        violation_record = {
            "type": violation_type,
            "timestamp": str(hash(original_value + str(details))),  # Simple hash for tracking
            "original_length": len(str(original_value)),
            "violations": details,
            "severity": "high" if self._is_serious_violation(details) else "medium"
        }
        
        self.violation_log.append(violation_record)
        
        # Keep log from growing too large
        if len(self.violation_log) > 1000:
            self.violation_log = self.violation_log[-500:]  # Keep last 500 entries
    
    def get_violation_report(self) -> Dict[str, Any]:
        """Get a report of all security violations detected"""
        if not self.violation_log:
            return {"status": "clean", "violations": 0, "details": []}
        
        high_severity = [v for v in self.violation_log if v["severity"] == "high"]
        medium_severity = [v for v in self.violation_log if v["severity"] == "medium"]
        
        return {
            "status": "violations_detected",
            "total_violations": len(self.violation_log),
            "high_severity": len(high_severity),
            "medium_severity": len(medium_severity),
            "violation_types": list(set(v["type"] for v in self.violation_log)),
            "recent_violations": self.violation_log[-10:],  # Last 10 violations
        }
    
    def clear_violation_log(self):
        """Clear the violation log"""
        self.violation_log.clear()


# Global sanitizer instance for easy access
_global_sanitizer = InputSanitizer(strict_mode=True)

def sanitize_input(value: Any, context: str = "general", **kwargs) -> Any:
    """
    Convenience function to sanitize input using global sanitizer.
    
    Args:
        value: Value to sanitize
        context: Sanitization context
        **kwargs: Additional arguments for sanitization
        
    Returns:
        Sanitized value
    """
    if isinstance(value, str):
        return _global_sanitizer.sanitize_string(value, context=context, **kwargs)
    elif isinstance(value, dict):
        return _global_sanitizer.sanitize_dict(value, **kwargs)
    elif isinstance(value, list):
        return _global_sanitizer.sanitize_list(value, **kwargs)
    else:
        return _global_sanitizer.sanitize_string(str(value), context=context, **kwargs)


def validate_node_parameters(parameters: Dict[str, Any], node_name: str = "unknown") -> Dict[str, Any]:
    """
    Validate and sanitize node parameters for security compliance.
    
    Args:
        parameters: Dictionary of node parameters
        node_name: Name of the node for logging
        
    Returns:
        Sanitized parameters dictionary
    """
    sanitizer = InputSanitizer(strict_mode=False)  # Don't raise exceptions for node params
    
    # Validate overall parameter size
    if not sanitizer.validate_parameter_size(parameters, max_size_mb=5.0):
        raise SecurityViolation(
            "parameter_size",
            node_name,
            "Node parameters exceed 5MB size limit"
        )
    
    # Sanitize all parameters
    sanitized_params = {}
    
    for param_name, param_value in parameters.items():
        # Sanitize parameter name
        clean_param_name = sanitizer.sanitize_string(param_name, max_length=100, context="general")
        
        # Sanitize parameter value based on type
        if isinstance(param_value, str):
            # Determine context based on parameter name
            if "query" in param_name.lower():
                context = "sql"
            elif "file" in param_name.lower() or "path" in param_name.lower():
                context = "path"
            elif "name" in param_name.lower():
                context = "filename"
            else:
                context = "general"
            
            clean_param_value = sanitizer.sanitize_string(param_value, context=context)
        elif isinstance(param_value, dict):
            clean_param_value = sanitizer.sanitize_dict(param_value)
        elif isinstance(param_value, list):
            clean_param_value = sanitizer.sanitize_list(param_value)
        else:
            clean_param_value = param_value
        
        sanitized_params[clean_param_name] = clean_param_value
    
    # Add security metadata
    sanitized_params["_security_metadata"] = {
        "sanitized": True,
        "node_name": node_name,
        "violations_detected": len(sanitizer.violation_log),
        "sanitization_timestamp": hash(str(parameters))  # Simple timestamp
    }
    
    return sanitized_params