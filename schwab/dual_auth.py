"""Dual authentication module for Schwab Trading and Market Data APIs."""
from typing import Optional, Dict
from datetime import datetime, timedelta
from .auth import SchwabAuth


class DualSchwabAuth:
    """Handles authentication for both Trading and Market Data APIs."""
    
    def __init__(
        self,
        trading_client_id: str,
        trading_client_secret: str,
        redirect_uri: str,
        market_data_client_id: Optional[str] = None,
        market_data_client_secret: Optional[str] = None
    ):
        """Initialize dual authentication handler.
        
        Args:
            trading_client_id: OAuth client ID for Trading API
            trading_client_secret: OAuth client secret for Trading API
            redirect_uri: OAuth callback URL
            market_data_client_id: OAuth client ID for Market Data API (optional)
            market_data_client_secret: OAuth client secret for Market Data API (optional)
        """
        # Trading API auth (requires user authorization)
        self.trading_auth = SchwabAuth(trading_client_id, trading_client_secret, redirect_uri)
        
        # Market Data API auth (uses client credentials if provided)
        self.market_data_auth = None
        if market_data_client_id and market_data_client_secret:
            self.market_data_auth = SchwabAuth(market_data_client_id, market_data_client_secret, redirect_uri)
    
    def load_market_data_token(self, access_token: str, expiry: Optional[datetime] = None):
        """Load a saved market data token.
        
        Args:
            access_token: The saved access token
            expiry: Token expiry time (optional)
        """
        if self.market_data_auth:
            self.market_data_auth.access_token = access_token
            self.market_data_auth.token_expiry = expiry or (datetime.now() + timedelta(hours=1))
    
    def get_auth_for_endpoint(self, endpoint: str) -> SchwabAuth:
        """Get the appropriate auth handler for an endpoint.
        
        Args:
            endpoint: The API endpoint being called
            
        Returns:
            The appropriate SchwabAuth instance
        """
        if "/marketdata/" in endpoint and self.market_data_auth:
            return self.market_data_auth
        return self.trading_auth
    
    def ensure_market_data_token(self) -> None:
        """Ensure we have a valid market data API token."""
        if not self.market_data_auth:
            return
            
        # Check if we need to get a new token
        if (not self.market_data_auth.access_token or 
            not self.market_data_auth.token_expiry or
            datetime.now() >= self.market_data_auth.token_expiry):
            # Use client credentials grant for market data API
            try:
                self.market_data_auth.get_client_credentials_token()
            except Exception:
                # If token refresh fails, it might be expired, try getting a new one
                self.market_data_auth.get_client_credentials_token()
    
    @property
    def trading_auth_header(self) -> Dict[str, str]:
        """Get authorization header for Trading API."""
        return self.trading_auth.authorization_header
    
    @property
    def market_data_auth_header(self) -> Dict[str, str]:
        """Get authorization header for Market Data API."""
        if self.market_data_auth:
            self.ensure_market_data_token()
            return self.market_data_auth.authorization_header
        # Fallback to trading auth if no separate market data auth
        return self.trading_auth.authorization_header