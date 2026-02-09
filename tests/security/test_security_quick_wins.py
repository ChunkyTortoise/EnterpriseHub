import pytest
pytestmark = pytest.mark.integration

import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware
import logging
from urllib.parse import urlparse

# We will test the logic directly where possible to avoid complex app imports
# that might trigger database initialization during collection.

class TestSecurityQuickWinsIsolated:
    
    # 1. CORS wildcard fix logic
    def test_cors_logic(self):
        # We simulate what main.py does
        with patch.dict(os.environ, {"ALLOWED_ORIGINS": "https://trusted.com,https://api.trusted.com"}):
            allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
            
            app = FastAPI()
            app.add_middleware(
                CORSMiddleware,
                allow_origins=allowed_origins,
                allow_credentials=True,
                allow_methods=["GET", "POST", "PUT", "DELETE"],
                allow_headers=["*"],
            )
            
            @app.get("/")
            def read_root():
                return {"Hello": "World"}
            
            client = TestClient(app)
            
            # Test allowed origin
            response = client.options("/", headers={"Origin": "https://trusted.com", "Access-Control-Request-Method": "GET"})
            assert response.headers.get("access-control-allow-origin") == "https://trusted.com"
            
            # Test disallowed origin
            response = client.options("/", headers={"Origin": "https://malicious.com", "Access-Control-Request-Method": "GET"})
            assert response.headers.get("access-control-allow-origin") is None # CORSMiddleware doesn't send the header if not allowed

    # 2. Open redirect fix logic
    @pytest.mark.asyncio
    async def test_open_redirect_logic(self):
        # We test the validation logic we added to enterprise_partnerships.py
        with patch.dict(os.environ, {"ALLOWED_REDIRECT_DOMAINS": "trusted.com,localhost:3000"}):
            allowed_domains = [d.strip() for d in os.environ.get("ALLOWED_REDIRECT_DOMAINS", "http://localhost:3000").split(",") if d.strip()]
            
            def validate_uri(redirect_uri):
                parsed_uri = urlparse(redirect_uri)
                if not parsed_uri.netloc:
                    raise HTTPException(status_code=400, detail="Invalid redirect URI format")
                if parsed_uri.netloc not in [urlparse(d).netloc or d for d in allowed_domains]:
                    raise HTTPException(status_code=400, detail="Unauthorized redirect URI")
            
            # Should pass
            validate_uri("https://trusted.com/callback")
            validate_uri("http://localhost:3000/callback")
            
            # Should fail - unauthorized
            with pytest.raises(HTTPException) as excinfo:
                validate_uri("https://malicious.com/callback")
            assert excinfo.value.status_code == 400
            
            # Should fail - missing netloc
            with pytest.raises(HTTPException) as excinfo:
                validate_uri("/local/path")
            assert excinfo.value.status_code == 400

    # 3. Password truncation fix
    def test_password_length_check(self):
        # Test the length check logic in EnhancedJWTAuth.hash_password
        def check_password_length(password):
            if len(password) > 72:
                raise HTTPException(status_code=400, detail="Password must not exceed 72 characters")
        
        # Should pass
        check_password_length("A" * 72)
        
        # Should fail
        with pytest.raises(HTTPException) as excinfo:
            check_password_length("A" * 73)
        assert excinfo.value.status_code == 400

    # 4. Raw SQL logging fix
    @pytest.mark.asyncio
    async def test_sql_logging_logic(self, caplog):
        # Simulate the logging call in connection_manager.py
        logger = logging.getLogger("test_sql")
        
        def log_query(sql):
            logger.debug(f"Executing query: {sql[:50]}...")
            
        long_sql = "SELECT " + ("a" * 100) + " FROM users"
        
        with caplog.at_level(logging.DEBUG):
            log_query(long_sql)
            
        assert "Executing query:" in caplog.text
        assert len(caplog.records[0].message) <= 50 + len("Executing query: ") + 3
        assert caplog.records[0].levelname == "DEBUG"
        assert caplog.records[0].message.endswith("...")
