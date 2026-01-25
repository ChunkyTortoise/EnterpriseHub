#!/usr/bin/env python3
"""
Security Agent - Implement authentication and rate limiting
Adds JWT auth, API key auth, and rate limiting middleware
"""

from pathlib import Path
from typing import Dict, Any, List


class SecurityAgent:
    """Implements security features for the API."""
    
    def __init__(self, base_dir: str = "ghl_real_estate_ai"):
        self.base_dir = Path(base_dir)
        self.features_implemented = []
    
    def create_jwt_middleware(self) -> str:
        """Generate JWT authentication middleware."""
        return '''"""
JWT Authentication Middleware

SECURITY: This module enforces fail-fast validation for JWT secrets.
No weak fallback secrets are permitted in any environment.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
import sys

# Configuration - SECURITY: Fail-fast validation, no weak fallbacks
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    print("=" * 60)
    print("CRITICAL SECURITY ERROR: JWT_SECRET_KEY must be set")
    print("=" * 60)
    print("Generate a secure secret: openssl rand -hex 32")
    print("Set via environment: export JWT_SECRET_KEY='your-secret'")
    print("=" * 60)
    sys.exit(1)
if len(SECRET_KEY) < 32:
    print(f"SECURITY ERROR: JWT_SECRET_KEY must be >= 32 characters (got {len(SECRET_KEY)})")
    sys.exit(1)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class JWTAuth:
    """JWT Authentication handler."""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create a new JWT token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user."""
    token = credentials.credentials
    payload = JWTAuth.verify_token(token)
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    return {"user_id": user_id, "payload": payload}
'''
    
    def create_api_key_middleware(self) -> str:
        """Generate API key authentication middleware."""
        return '''"""
API Key Authentication Middleware
"""

from fastapi import Header, HTTPException, status
from typing import Optional
import os
import hashlib
import secrets

# Store API keys in environment or database
# Format: location_id -> hashed_api_key
API_KEYS_DB = {}  # In production, use a database


class APIKeyAuth:
    """API Key authentication handler."""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a new API key."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def verify_api_key(api_key: str, location_id: str) -> bool:
        """Verify an API key against stored hash."""
        if location_id not in API_KEYS_DB:
            return False
        
        hashed = APIKeyAuth.hash_api_key(api_key)
        return hashed == API_KEYS_DB[location_id]


async def verify_api_key(
    x_api_key: Optional[str] = Header(None),
    x_location_id: Optional[str] = Header(None)
):
    """Dependency to verify API key."""
    if not x_api_key or not x_location_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key and location ID required",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if not APIKeyAuth.verify_api_key(x_api_key, x_location_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return {"location_id": x_location_id}
'''
    
    def create_rate_limit_middleware(self) -> str:
        """Generate rate limiting middleware."""
        return '''"""
Rate Limiting Middleware
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import asyncio


class RateLimiter:
    """Rate limiter using token bucket algorithm."""
    
    def __init__(self, requests_per_minute: int = 60, burst: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.buckets: Dict[str, Tuple[int, datetime]] = {}
        self.lock = asyncio.Lock()
    
    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        async with self.lock:
            now = datetime.now()
            
            if key not in self.buckets:
                self.buckets[key] = (self.burst - 1, now)
                return True
            
            tokens, last_update = self.buckets[key]
            
            # Refill tokens based on time passed
            time_passed = (now - last_update).total_seconds()
            tokens_to_add = int(time_passed * (self.requests_per_minute / 60))
            tokens = min(self.burst, tokens + tokens_to_add)
            
            if tokens > 0:
                self.buckets[key] = (tokens - 1, now)
                return True
            else:
                self.buckets[key] = (0, last_update)
                return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute=requests_per_minute)
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Use IP address as key (or user_id if authenticated)
        client_ip = request.client.host
        
        # Check rate limit
        if not await self.limiter.is_allowed(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        response = await call_next(request)
        return response
'''
    
    def create_security_headers_middleware(self) -> str:
        """Generate security headers middleware."""
        return '''"""
Security Headers Middleware
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
'''
    
    def implement_all_features(self) -> Dict[str, Any]:
        """Implement all security features."""
        results = {
            "features": [],
            "files_created": []
        }
        
        # Create middleware directory
        middleware_dir = self.base_dir / "api" / "middleware"
        middleware_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. JWT Authentication
        jwt_file = middleware_dir / "jwt_auth.py"
        jwt_file.write_text(self.create_jwt_middleware())
        results["files_created"].append(str(jwt_file))
        results["features"].append("JWT Authentication")
        
        # 2. API Key Authentication
        apikey_file = middleware_dir / "api_key_auth.py"
        apikey_file.write_text(self.create_api_key_middleware())
        results["files_created"].append(str(apikey_file))
        results["features"].append("API Key Authentication")
        
        # 3. Rate Limiting
        ratelimit_file = middleware_dir / "rate_limiter.py"
        ratelimit_file.write_text(self.create_rate_limit_middleware())
        results["files_created"].append(str(ratelimit_file))
        results["features"].append("Rate Limiting")
        
        # 4. Security Headers
        headers_file = middleware_dir / "security_headers.py"
        headers_file.write_text(self.create_security_headers_middleware())
        results["files_created"].append(str(headers_file))
        results["features"].append("Security Headers")
        
        # 5. Create __init__.py
        init_file = middleware_dir / "__init__.py"
        init_content = '''"""
Security middleware package
"""

from .jwt_auth import JWTAuth, get_current_user
from .api_key_auth import APIKeyAuth, verify_api_key
from .rate_limiter import RateLimitMiddleware
from .security_headers import SecurityHeadersMiddleware

__all__ = [
    "JWTAuth",
    "get_current_user",
    "APIKeyAuth",
    "verify_api_key",
    "RateLimitMiddleware",
    "SecurityHeadersMiddleware"
]
'''
        init_file.write_text(init_content)
        results["files_created"].append(str(init_file))
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate security implementation report."""
        report = []
        report.append("=" * 80)
        report.append("SECURITY AGENT REPORT")
        report.append("=" * 80)
        report.append("")
        
        report.append("🔒 Security Features Implemented:")
        report.append("")
        for feature in results["features"]:
            report.append(f"  ✅ {feature}")
        report.append("")
        
        report.append("📁 Files Created:")
        report.append("")
        for file_path in results["files_created"]:
            report.append(f"  • {file_path}")
        report.append("")
        
        report.append("=" * 80)
        report.append("📝 INTEGRATION INSTRUCTIONS:")
        report.append("")
        report.append("1. Install required packages:")
        report.append("   pip install python-jose[cryptography] passlib[bcrypt] python-multipart")
        report.append("")
        report.append("2. Add to your FastAPI app (api/main.py):")
        report.append("")
        report.append("   from fastapi import FastAPI, Depends")
        report.append("   from api.middleware import (")
        report.append("       RateLimitMiddleware,")
        report.append("       SecurityHeadersMiddleware,")
        report.append("       get_current_user,")
        report.append("       verify_api_key")
        report.append("   )")
        report.append("")
        report.append("   app = FastAPI()")
        report.append("")
        report.append("   # Add middleware")
        report.append("   app.add_middleware(RateLimitMiddleware, requests_per_minute=60)")
        report.append("   app.add_middleware(SecurityHeadersMiddleware)")
        report.append("")
        report.append("   # Protect endpoints with JWT:")
        report.append("   @app.get('/protected')")
        report.append("   async def protected_route(current_user: dict = Depends(get_current_user)):")
        report.append("       return {'message': 'Authenticated!', 'user': current_user}")
        report.append("")
        report.append("   # Or protect with API key:")
        report.append("   @app.get('/api-protected')")
        report.append("   async def api_protected(auth: dict = Depends(verify_api_key)):")
        report.append("       return {'message': 'API key valid!', 'location': auth['location_id']}")
        report.append("")
        report.append("3. Set environment variables:")
        report.append("   export JWT_SECRET_KEY='your-secret-key-here'")
        report.append("")
        report.append("4. Test the endpoints:")
        report.append("   curl -H 'Authorization: Bearer <token>' http://localhost:8000/protected")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Run security agent."""
    print("🔒 Security Agent Starting...\n")
    
    agent = SecurityAgent()
    
    print("Implementing security features...\n")
    results = agent.implement_all_features()
    
    report = agent.generate_report(results)
    print(report)
    
    # Save report
    report_path = Path("ghl_real_estate_ai") / "SECURITY_IMPLEMENTATION_REPORT.md"
    report_path.write_text(report)
    print(f"\n📄 Report saved to: {report_path}")


if __name__ == "__main__":
    main()
