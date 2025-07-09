"""Authentication module for Schwab API."""
import base64
import urllib.parse
from typing import Optional, Dict
import requests
from datetime import datetime, timedelta

class SchwabAuth:
    """Handles OAuth 2.0 authentication for Schwab API."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        auth_base_url: str = "https://api.schwabapi.com/v1/oauth"
    ):
        """Initialize authentication handler.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth callback URL
            auth_base_url: Base URL for authentication endpoints
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_base_url = auth_base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
    @property
    def authorization_header(self) -> Dict[str, str]:
        """Get the authorization header for API requests."""
        if not self.access_token:
            raise ValueError("No access token available. Please authenticate first.")
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def get_authorization_url(self) -> str:
        """Get the URL for the authorization step."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri
        }
        return f"{self.auth_base_url}/authorize?{urllib.parse.urlencode(params)}"
    
    def get_basic_auth_header(self) -> str:
        """Get Basic Auth header for token requests."""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def exchange_code_for_tokens(self, authorization_code: str) -> Dict:
        """Exchange authorization code for access and refresh tokens.
        
        Args:
            authorization_code: The authorization code from the callback
            
        Returns:
            Dict containing tokens and expiry information
        """
        headers = {
            "Authorization": self.get_basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri
        }
        
        response = requests.post(
            f"{self.auth_base_url}/token",
            headers=headers,
            data=data
        )
        response.raise_for_status()
        
        token_data = response.json()
        self._update_tokens(token_data)
        return token_data
    
    def refresh_access_token(self) -> Dict:
        """Refresh the access token using the refresh token.
        
        Returns:
            Dict containing new tokens and expiry information
        """
        if not self.refresh_token:
            raise ValueError("No refresh token available")
            
        headers = {
            "Authorization": self.get_basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        
        response = requests.post(
            f"{self.auth_base_url}/token",
            headers=headers,
            data=data
        )
        response.raise_for_status()
        
        token_data = response.json()
        self._update_tokens(token_data)
        return token_data
    
    def get_client_credentials_token(self) -> Dict:
        """Get access token using client credentials grant (for market data API).
        
        Returns:
            Dict containing token and expiry information
        """
        headers = {
            "Authorization": self.get_basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "client_credentials"
        }
        
        response = requests.post(
            f"{self.auth_base_url}/token",
            headers=headers,
            data=data
        )
        response.raise_for_status()
        
        token_data = response.json()
        self._update_tokens(token_data)
        return token_data
    
    def _update_tokens(self, token_data: Dict) -> None:
        """Update stored tokens and expiry time.
        
        Args:
            token_data: Response from token endpoint
        """
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token")  # May not be present in refresh response
        expires_in = token_data["expires_in"]
        
        # Ensure expires_in is an integer
        if isinstance(expires_in, str):
            expires_in = int(expires_in)
        
        self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
    
    def ensure_valid_token(self) -> None:
        """Ensure we have a valid access token, refreshing if necessary."""
        if not self.access_token or not self.token_expiry:
            raise ValueError("No access token available. Please authenticate first.")
            
        # Refresh if token is expired or will expire in the next minute
        if datetime.now() + timedelta(minutes=1) >= self.token_expiry:
            self.refresh_access_token()