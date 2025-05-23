"""Test configuration and fixtures for Schwab Trader tests."""

import pytest
from unittest.mock import MagicMock, patch

from schwab import SchwabClient, AsyncSchwabClient
from schwab.auth import SchwabAuth
from tests.helpers.model_factories import (create_test_order, create_test_account, 
                                         create_test_position, create_test_execution_leg,
                                         create_test_order_activity)


@pytest.fixture
def mock_auth():
    """Mock SchwabAuth instance."""
    auth = MagicMock(spec=SchwabAuth)
    auth.ensure_valid_token.return_value = None
    auth.authorization_header = {"Authorization": "Bearer mock_token"}
    return auth


@pytest.fixture
def mock_client(mock_auth):
    """Mock SchwabClient instance with mocked auth."""
    with patch('requests.Session') as mock_session:
        # Mock the session's request method
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_session.return_value.request.return_value = mock_response
        
        client = SchwabClient(
            client_id="mock_client_id",
            client_secret="mock_client_secret",
            redirect_uri="mock_redirect_uri",
            auth=mock_auth
        )
        
        # Replace _make_request with a mock
        client._make_request = MagicMock(return_value={})
        # Wrap get_account_numbers to allow test override (return_value/side_effect) but default to real method
        # Wrap get_account_numbers and get_account with MagicMocks that call the real methods by default
        orig_get_numbers = client.get_account_numbers
        client.get_account_numbers = MagicMock(wraps=orig_get_numbers)
        orig_get_account = client.get_account
        client.get_account = MagicMock(wraps=orig_get_account)
        # Wrap get_orders and place_order to allow test override and call count
        if hasattr(client, 'get_orders'):
            orig_get_orders = client.get_orders
            client.get_orders = MagicMock(wraps=orig_get_orders)
        if hasattr(client, 'place_order'):
            orig_place_order = client.place_order
            client.place_order = MagicMock(wraps=orig_place_order)
        
        yield client


@pytest.fixture
def mock_async_client(mock_auth):
    """Mock AsyncSchwabClient instance with mocked auth."""
    with patch('aiohttp.ClientSession') as mock_session:
        client = AsyncSchwabClient(api_key="mock_api_key")
        
        # Replace _make_request with a mock
        async def mock_make_request(*args, **kwargs):
            return {}
            
        client._make_request = mock_make_request
        
        yield client