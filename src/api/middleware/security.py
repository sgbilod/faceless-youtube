"""
Security middleware for FastAPI application

Adds comprehensive security headers to protect against common web vulnerabilities:
- HSTS (Strict-Transport-Security)
- Clickjacking protection (X-Frame-Options)
- MIME sniffing prevention (X-Content-Type-Options)
- XSS protection
- Content Security Policy
- Referrer Policy
- Permissions Policy
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all HTTP responses"""
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable
    ) -> Response:
        """
        Process request and add security headers to response
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            Response with security headers added
        """
        response = await call_next(request)
        
        # Strict Transport Security (Force HTTPS)
        # max-age: 1 year, includeSubDomains, preload for HSTS preload list
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        
        # Prevent clickjacking attacks
        # DENY: page cannot be displayed in frame/iframe/embed/object
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME sniffing
        # Forces browser to respect declared Content-Type
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection (legacy browsers)
        # 1: enable filter, mode=block: block page if XSS detected
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content Security Policy
        # Restricts resource loading to prevent XSS and data injection
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "  # Only load resources from same origin
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Allow inline scripts (needed for some frameworks)
            "style-src 'self' 'unsafe-inline'; "  # Allow inline styles
            "img-src 'self' data: https:; "  # Allow images from self, data URIs, and HTTPS
            "font-src 'self' data:; "  # Allow fonts from self and data URIs
            "connect-src 'self' ws: wss:; "  # Allow WebSocket connections
            "frame-ancestors 'none';"  # Prevent framing (redundant with X-Frame-Options)
        )
        
        # Referrer Policy
        # Control how much referrer information is sent with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy (formerly Feature-Policy)
        # Disable unnecessary browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "  # Disable geolocation
            "microphone=(), "  # Disable microphone
            "camera=(), "  # Disable camera
            "payment=(), "  # Disable payment
            "usb=(), "  # Disable USB
            "magnetometer=()"  # Disable magnetometer
        )
        
        # Remove server identification
        # Prevents information leakage about server software
        response.headers["Server"] = "Unknown"
        
        return response
