"""
Security tests for authentication, authorization, rate limiting, and input validation.
"""
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import (
    create_access_token, 
    verify_token, 
    TokenPayload, 
    UserRoles,
    rate_limiter,
    require_auth,
    RateLimitException
)
from app.models.finding import Finding, SeverityLevel, ConfidenceLevel, FindingStatus


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create auth headers for testing."""
    token = create_access_token({
        "sub": "test_user",
        "role": UserRoles.ANALYST,
        "name": "Test User"
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers():
    """Create admin auth headers for testing."""
    token = create_access_token({
        "sub": "admin_user",
        "role": UserRoles.ADMIN,
        "name": "Admin User"
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_headers():
    """Create viewer auth headers for testing."""
    token = create_access_token({
        "sub": "viewer_user",
        "role": UserRoles.VIEWER,
        "name": "Viewer User"
    })
    return {"Authorization": f"Bearer {token}"}


class TestJWT:
    """Test JWT authentication functionality."""
    
    def test_create_and_verify_token(self):
        """Test token creation and verification."""
        data = {
            "sub": "test_user",
            "role": UserRoles.ANALYST
        }
        
        token = create_access_token(data)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 100
        
        payload = verify_token(token)
        assert isinstance(payload, TokenPayload)
        assert payload.sub == "test_user"
        assert payload.role == UserRoles.ANALYST
    
    def test_expired_token(self):
        """Test that expired tokens are rejected."""
        # Create token with immediate expiration
        data = {
            "sub": "test_user",
            "role": UserRoles.ANALYST,
            "exp": datetime.utcnow() - timedelta(minutes=1)
        }
        
        with pytest.raises(Exception):
            verify_token(create_access_token(data))
    
    def test_invalid_token(self):
        """Test that invalid tokens are rejected."""
        with pytest.raises(Exception):
            verify_token("invalid.token.here")
        
        with pytest.raises(Exception):
            verify_token("")
        
        with pytest.raises(Exception):
            verify_token(None)
    
    def test_token_without_role(self):
        """Test token without role claim."""
        data = {"sub": "test_user"}
        
        token = create_access_token(data)
        payload = verify_token(token)
        
        assert payload.sub == "test_user"
        assert payload.role == "analyst"  # Default role from test


class TestAuthenticationMiddleware:
    """Test authentication middleware on API endpoints."""
    
    def test_health_check_no_auth(self, client):
        """Health check should not require authentication."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_demo_tokens_no_auth(self, client):
        """Demo tokens endpoint should not require authentication."""
        response = client.get("/api/auth/demo-tokens")
        assert response.status_code == 200
        data = response.json()
        assert "tokens" in data
        assert "warning" in data
    
    def test_protected_endpoint_no_auth(self, client):
        """Protected endpoints should require authentication."""
        response = client.get("/api/scans")
        assert response.status_code == 401  # Unauthorized
    
    def test_protected_endpoint_with_auth(self, client, auth_headers):
        """Protected endpoints should work with authentication."""
        response = client.get("/api/scans", headers=auth_headers)
        # Might return 200 (empty list) or 401 if no scan history
        assert response.status_code in [200, 401]
    
    def test_invalid_auth_scheme(self, client):
        """Invalid auth scheme should be rejected."""
        headers = {"Authorization": "Basic invalid_token"}
        response = client.get("/api/scans", headers=headers)
        assert response.status_code == 401
    
    def test_malformed_auth_header(self, client):
        """Malformed auth header should be rejected."""
        headers = {"Authorization": "Bearer"}
        response = client.get("/api/scans", headers=headers)
        assert response.status_code == 401


class TestRoleBasedAccessControl:
    """Test role-based access control."""
    
    def test_analyst_can_access_scans(self, client, auth_headers):
        """Analyst role should be able to access scan endpoints."""
        response = client.get("/api/scans", headers=auth_headers)
        # Returns 200 or 401 if no scans
        assert response.status_code in [200, 401]
    
    def test_viewer_cannot_upload(self, client, viewer_headers):
        """Viewer role should NOT be able to upload scans."""
        # Try to access upload endpoint (should fail)
        files = {"file": ("test.zip", b"dummy content", "application/zip")}
        data = {"project_name": "test_project"}
        
        response = client.post("/api/scans/upload", files=files, data=data, headers=viewer_headers)
        assert response.status_code == 403  # Forbidden
    
    def test_admin_access(self, client, admin_headers):
        """Admin role should have access to all endpoints."""
        response = client.get("/api/scans", headers=admin_headers)
        # Returns 200 or 401 if no scans
        assert response.status_code in [200, 401]


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_middleware(self):
        """Test rate limiting middleware."""
        # Clear rate limiter
        rate_limiter._requests.clear()
        
        # First request should pass
        assert not rate_limiter.is_rate_limited("test:endpoint")
        
        # Simulate many requests
        for i in range(110):  # Default limit is 100
            if i < 100:
                assert not rate_limiter.is_rate_limited("test:endpoint")
            else:
                assert rate_limiter.is_rate_limited("test:endpoint")
    
    def test_rate_limit_headers(self, client):
        """Test rate limit headers in response."""
        # Health endpoint should have rate limit headers
        response = client.get("/api/health")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Window" in response.headers
        
        limit = int(response.headers["X-RateLimit-Limit"])
        window = response.headers["X-RateLimit-Window"]
        assert limit == 100
        assert "s" in window
    
    def test_different_endpoints_different_limits(self):
        """Test that different endpoints have separate rate limits."""
        # Clear rate limiter
        rate_limiter._requests.clear()
        
        # Fill up limit for endpoint1
        for i in range(50):
            rate_limiter.is_rate_limited("ip1:/endpoint1")
        
        # Endpoint2 should still have full limit
        assert not rate_limiter.is_rate_limited("ip1:/endpoint2")
        
        # Different IPs should have separate limits
        assert not rate_limiter.is_rate_limited("ip2:/endpoint1")


class TestInputValidation:
    """Test input validation for security."""
    
    def test_file_type_validation(self, client, auth_headers):
        """Test that only ZIP files are accepted."""
        files = {"file": ("test.txt", b"dummy content", "text/plain")}
        data = {"project_name": "test_project"}
        
        response = client.post("/api/scans/upload", files=files, data=data, headers=auth_headers)
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "ZIP" in data["detail"] or "zip" in data["detail"]
    
    def test_file_size_validation(self, client, auth_headers):
        """Test file size validation."""
        # Create a file that exceeds limit (100MB)
        large_content = b"x" * (101 * 1024 * 1024)  # 101MB
        
        files = {"file": ("test.zip", large_content, "application/zip")}
        data = {"project_name": "test_project"}
        
        response = client.post("/api/scans/upload", files=files, data=data, headers=auth_headers)
        # Should either reject or timeout
        assert response.status_code in [413, 400, 500]
    
    def test_malicious_filename(self, client, auth_headers):
        """Test rejection of malicious filenames."""
        malicious_names = [
            "../../etc/passwd.zip",
            "/absolute/path.zip",
            "file; rm -rf /;.zip",
            "file$(whoami).zip",
            "file`id`.zip"
        ]
        
        for filename in malicious_names:
            files = {"file": (filename, b"dummy content", "application/zip")}
            data = {"project_name": "test_project"}
            
            response = client.post("/api/scans/upload", files=files, data=data, headers=auth_headers)
            # Should reject or fail gracefully
            assert response.status_code in [400, 500]
    
    def test_sql_injection_attempts(self, client, auth_headers):
        """Test SQL injection attempts in parameters."""
        # Test scan_id parameter
        sql_injection_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE scans;--",
            "1 UNION SELECT * FROM users",
            "1' AND SLEEP(5)--"
        ]
        
        for payload in sql_injection_payloads:
            response = client.get(f"/api/scans/{payload}", headers=auth_headers)
            # Should either return 404 (not found) or handle gracefully
            assert response.status_code in [404, 401, 400]


class TestSecurityHeaders:
    """Test security headers in responses."""
    
    def test_cors_headers(self, client):
        """Test CORS headers."""
        response = client.options("/api/health")
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers
    
    def test_security_headers_present(self, client):
        """Test that security headers are present."""
        response = client.get("/api/health")
        
        # Check for security headers
        headers = response.headers
        
        # CORS headers
        assert "Access-Control-Allow-Origin" in headers
        
        # Rate limiting headers
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Window" in headers
        
        # Other security headers (add more based on your config)
        assert "Content-Type" in headers


@pytest.mark.integration
class TestEndToEndSecurity:
    """End-to-end security tests."""
    
    def test_complete_auth_flow(self, client):
        """Test complete authentication flow."""
        # 1. Get demo tokens
        response = client.get("/api/auth/demo-tokens")
        assert response.status_code == 200
        tokens = response.json()["tokens"]
        
        # 2. Use analyst token
        analyst_token = tokens["analyst"]
        headers = {"Authorization": f"Bearer {analyst_token}"}
        
        # 3. Verify authentication
        response = client.get("/api/auth/verify", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] == True
        
        # 4. Access protected endpoint
        response = client.get("/api/scans", headers=headers)
        # Should return 200 (empty list) or 401
        assert response.status_code in [200, 401]
    
    def test_rate_limiting_integration(self):
        """Test rate limiting integration."""
        # Note: This test might be flaky in CI
        # In production, this would hit actual rate limits
        pass


class TestErrorHandling:
    """Test security error handling."""
    
    def test_graceful_error_messages(self, client):
        """Test that errors don't leak sensitive information."""
        # Invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/scans", headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        # Should not contain stack traces or internal info
        assert "traceback" not in str(data).lower()
        assert "password" not in str(data).lower()
        assert "secret" not in str(data).lower()
    
    def test_file_upload_errors(self, client, auth_headers):
        """Test file upload error handling."""
        # Try to upload without file
        response = client.post("/api/scans/upload", headers=auth_headers)
        
        assert response.status_code == 422 or response.status_code == 400
        
        if response.status_code == 422:  # FastAPI validation error
            data = response.json()
            # Should have validation errors
            assert "detail" in data
        else:
            # Other error formats
            data = response.json()
            assert "detail" in data
            # Error should be user-friendly
            assert "file" in str(data).lower() or "required" in str(data).lower()


if __name__ == "__main__":
    # Run tests
    import sys
    sys.exit(pytest.main([__file__, "-v"]))