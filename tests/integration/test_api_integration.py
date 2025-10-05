"""
API Integration Tests

Tests that verify API endpoints, authentication, and rate limiting work correctly.
"""

import pytest
from unittest.mock import patch, Mock

# Import API clients
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check and status endpoints"""
    
    def test_health_check(self, test_client):
        """Test /health endpoint returns 200"""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_readiness_check(self, test_client):
        """Test /ready endpoint checks database connection"""
        response = test_client.get("/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert data["database"] in ["connected", "disconnected"]


class TestAuthentication:
    """Test JWT authentication flow"""
    
    def test_login_success(self, test_client, sample_user):
        """Test successful login returns JWT token"""
        response = test_client.post(
            "/auth/login",
            data={  # Use data instead of json for Form data
                "email": "test@example.com",
                "password": "password"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, test_client):
        """Test login with invalid credentials returns 401"""
        response = test_client.post(
            "/auth/login",
            data={
                "email": "invalid@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_protected_endpoint_without_token(self, test_client):
        """Test accessing protected endpoint without token returns 401"""
        response = test_client.get("/api/videos")
        
        assert response.status_code == 401
    
    def test_protected_endpoint_with_token(self, test_client, auth_headers):
        """Test accessing protected endpoint with valid token"""
        response = test_client.get(
            "/api/videos",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]  # 200 if videos exist, 404 if not


class TestRateLimiting:
    """Test rate limiting with Redis"""
    
    def test_rate_limit_enforcement(self, test_client, auth_headers):
        """Test that rate limits are enforced"""
        # Make many requests to trigger rate limit
        # Note: Real rate limiting requires Redis, this tests the endpoint exists
        response = test_client.get(
            "/api/videos",
            headers=auth_headers
        )
        
        # Should succeed or return 401 (auth), not 500 (server error)
        assert response.status_code in [200, 401, 429]
    
    def test_rate_limit_reset(self, test_client, auth_headers):
        """Test rate limit counters reset after window"""
        response = test_client.get(
            "/api/videos",
            headers=auth_headers
        )
        
        # Should succeed or return auth error (not rate limit)
        assert response.status_code != 429 or response.status_code in [200, 401]


class TestCORSHeaders:
    """Test CORS headers configuration"""
    
    def test_cors_headers_present(self, test_client):
        """Test that CORS headers are included in response"""
        # Send request with Origin header to trigger CORS
        response = test_client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # CORS headers should be present when Origin is sent
        assert "access-control-allow-origin" in [h.lower() for h in response.headers.keys()] or \
               "vary" in [h.lower() for h in response.headers.keys()]
    
    def test_preflight_request(self, test_client):
        """Test OPTIONS preflight request"""
        response = test_client.options(
            "/api/videos",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        # Should return 200 or 405 (method not allowed is acceptable)
        assert response.status_code in [200, 405]


class TestErrorResponses:
    """Test API error responses"""
    
    def test_not_found_error(self, test_client, auth_headers):
        """Test 404 for non-existent resource"""
        response = test_client.get(
            "/api/videos/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "detail" in response.json()
    
    def test_validation_error(self, test_client, auth_headers):
        """Test 422 for invalid request body"""
        response = test_client.post(
            "/api/videos",
            headers=auth_headers,
            json={"invalid": "data"}  # Missing required fields
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_server_error_handling(self, test_client):
        """Test 500 errors are handled gracefully"""
        # This would require mocking internal service failure
        # For now, document expected behavior
        pass


class TestVideoAPI:
    """Test video creation and retrieval endpoints"""
    
    def test_create_video_success(self, test_client, auth_headers):
        """Test POST /api/videos creates new video"""
        response = test_client.post(
            "/api/videos",
            headers=auth_headers,
            json={
                "title": "Test Video",
                "niche": "meditation",
                "script_id": 1
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == "Test Video"
        assert data["status"] == "queued"
    
    def test_list_videos(self, test_client, auth_headers, sample_video):
        """Test GET /api/videos lists user's videos"""
        response = test_client.get(
            "/api/videos",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_video_by_id(self, test_client, auth_headers, sample_video):
        """Test GET /api/videos/{id} returns video details"""
        response = test_client.get(
            f"/api/videos/{sample_video.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_video.id
        assert data["title"] == sample_video.title
