#!/usr/bin/env python3
"""
Production Authentication Middleware for FastAPI
Secures all API endpoints with JWT/API Key authentication
"""

import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.base import BaseHTTPMiddleware
from typing import List, Optional

from ..core.auth import auth_system, authenticate_websocket, get_api_key_user, rate_limiter

logger = logging.getLogger(__name__)

class ProductionAuthMiddleware(BaseHTTPMiddleware):
    """
    Production authentication middleware with comprehensive security
    """
    
    def __init__(
        self, 
        app, 
        excluded_paths: List[str] = None,
        require_https: bool = False,
        enable_rate_limiting: bool = True
    ):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/", "/health", "/docs", "/redoc", "/openapi.json",
            "/api/v1/auth/login", "/api/v1/auth/register"
        ]
        self.require_https = require_https
        self.enable_rate_limiting = enable_rate_limiting
        
        logger.info(f"Production auth middleware initialized with {len(self.excluded_paths)} excluded paths")
    
    async def dispatch(self, request: Request, call_next):
        """Main middleware dispatch logic"""
        
        # Skip authentication for excluded paths
        if request.url.path in self.excluded_paths:
            response = await call_next(request)
            return self._add_security_headers(response)
        
        # HTTPS enforcement
        if self.require_https and request.url.scheme != "https":
            return JSONResponse(
                status_code=403,
                content={"error": "HTTPS required"}
            )
        
        # Rate limiting
        if self.enable_rate_limiting:
            client_ip = self._get_client_ip(request)
            if not rate_limiter.is_allowed(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "retry_after": rate_limiter.time_window
                    }
                )
        
        # Authentication
        auth_result = await self._authenticate_request(request)
        if not auth_result["success"]:
            return JSONResponse(
                status_code=auth_result["status_code"],
                content={"error": auth_result["error"]}
            )
        
        # Add authenticated user to request state
        request.state.user = auth_result["user"]
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        return self._add_security_headers(response)
    
    async def _authenticate_request(self, request: Request) -> dict:
        """Authenticate request using various methods"""
        
        # Try Authorization header (Bearer token)
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            # Try JWT token
            payload = auth_system.verify_token(token)
            if payload:
                username = payload.get("sub")
                user = auth_system.users.get(username)
                if user and user.is_active:
                    return {"success": True, "user": user}
            
            # Try API key
            user = auth_system.authenticate_api_key(token)
            if user:
                return {"success": True, "user": user}
        
        # Try X-API-Key header
        api_key = request.headers.get("x-api-key")
        if api_key:
            user = auth_system.authenticate_api_key(api_key)
            if user:
                return {"success": True, "user": user}
        
        # Authentication failed
        return {
            "success": False,
            "status_code": 401,
            "error": "Authentication required"
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address for rate limiting"""
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    def _add_security_headers(self, response):
        """Add security headers to response"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

class WebSocketAuthMiddleware:
    """
    WebSocket authentication middleware for MCP servers
    """
    
    @staticmethod
    async def authenticate_websocket(websocket, auth_token: Optional[str] = None):
        """Authenticate WebSocket connection"""
        if not auth_token:
            await websocket.close(code=1008, reason="Authentication required")
            raise HTTPException(status_code=401, detail="Authentication required")
        
        try:
            user = authenticate_websocket(auth_token)
            return user
        except Exception as e:
            logger.error(f"WebSocket authentication failed: {e}")
            await websocket.close(code=1008, reason="Authentication failed")
            raise HTTPException(status_code=401, detail="Authentication failed")

# Export main components
__all__ = ['ProductionAuthMiddleware', 'WebSocketAuthMiddleware']