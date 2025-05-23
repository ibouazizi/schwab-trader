"""Tests for authentication module."""

import pytest
from unittest.mock import MagicMock, patch
import base64
import time
from datetime import datetime, timedelta

from schwab.auth import SchwabAuth


class TestSchwabAuth:
    """Test suite for SchwabAuth class."""
    
    def test_init(self):
        """Test initialization of SchwabAuth."""
        auth = SchwabAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="test_redirect_uri"
        )
        
        assert auth.client_id == "test_client_id"
        assert auth.client_secret == "test_client_secret"
        assert auth.redirect_uri == "test_redirect_uri"
        assert auth.auth_base_url == "https://api.schwabapi.com/v1/oauth"
        assert auth.access_token is None
        assert auth.refresh_token is None
        assert auth.token_expiry is None
    
    def test_get_authorization_url(self):
        """Test getting authorization URL."""
        auth = SchwabAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="test_redirect_uri"
        )
        
        url = auth.get_authorization_url()
        
        assert "test_client_id" in url
        assert "test_redirect_uri" in url
        assert "response_type=code" in url
        assert url.startswith("https://api.schwabapi.com/v1/oauth/authorize")
    
    def test_get_basic_auth_header(self):
        """Test generating basic auth header."""
        auth = SchwabAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="test_redirect_uri"
        )
        
        header = auth.get_basic_auth_header()
        
        expected_credentials = "test_client_id:test_client_secret"
        expected_encoded = base64.b64encode(expected_credentials.encode()).decode()
        assert header == f"Basic {expected_encoded}"
    
    def test_authorization_header_property(self):
        """Test authorization header property."""
        auth = SchwabAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="test_redirect_uri"
        )
        
        # Should raise ValueError if no access token
        with pytest.raises(ValueError):
            _ = auth.authorization_header
        
        # Set access token and test again
        auth.access_token = "test_token"
        assert auth.authorization_header == {"Authorization": "Bearer test_token"}
    
    @patch('requests.post')
    def test_exchange_code_for_tokens(self, mock_post):
        """Test exchanging auth code for tokens."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        auth = SchwabAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="test_redirect_uri"
        )
        
        result = auth.exchange_code_for_tokens("test_code")
        
        assert result == {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600
        }
        assert auth.access_token == "test_access_token"
        assert auth.refresh_token == "test_refresh_token"
        assert auth.token_expiry is not None
        
        # Verify correct parameters were used
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.schwabapi.com/v1/oauth/token"
        assert "Authorization" in kwargs["headers"]
        assert kwargs["data"]["grant_type"] == "authorization_code"
        assert kwargs["data"]["code"] == "test_code"
        assert kwargs["data"]["redirect_uri"] == "test_redirect_uri"
    
    @patch('requests.post')
    def test_refresh_access_token(self, mock_post):
        """Test refreshing access token."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        auth = SchwabAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="test_redirect_uri"
        )
        auth.refresh_token = "test_refresh_token"
        
        result = auth.refresh_access_token()
        
        assert result == {
            "access_token": "new_access_token",
            "expires_in": 3600
        }
        assert auth.access_token == "new_access_token"
        
        # Verify correct parameters were used
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.schwabapi.com/v1/oauth/token"
        assert "Authorization" in kwargs["headers"]
        assert kwargs["data"]["grant_type"] == "refresh_token"
        assert kwargs["data"]["refresh_token"] == "test_refresh_token"
    
    def test_refresh_token_missing(self):
        """Test error when refresh token is missing."""
        auth = SchwabAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="test_redirect_uri"
        )
        
        with pytest.raises(ValueError):
            auth.refresh_access_token()
    
    def test_ensure_valid_token(self):
        """Test ensuring token is valid."""
        auth = SchwabAuth(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="test_redirect_uri"
        )
        
        # Should raise ValueError if no access token
        with pytest.raises(ValueError):
            auth.ensure_valid_token()
        
        # Set token but with expiry in past
        auth.access_token = "test_token"
        auth.token_expiry = datetime.now() - timedelta(seconds=60)
        auth.refresh_token = "test_refresh_token"
        
        # Mock refresh_access_token
        auth.refresh_access_token = MagicMock()
        
        # Call ensure_valid_token
        auth.ensure_valid_token()
        
        # Should have called refresh
        auth.refresh_access_token.assert_called_once()
        
        # Reset and test with valid token
        auth.refresh_access_token.reset_mock()
        auth.token_expiry = datetime.now() + timedelta(minutes=10)
        
        # Call ensure_valid_token
        auth.ensure_valid_token()
        
        # Should not have called refresh
        auth.refresh_access_token.assert_not_called()