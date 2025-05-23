"""Tests for paper trading functionality."""

import pytest
from unittest.mock import MagicMock, patch

from schwab.models.base import AccountNumber, AccountNumbers
from schwab.paper_trading.account import PaperAccountManager
from schwab.paper_trading.indicators import PaperTradingIndicator
from schwab.paper_trading.client import PaperTradingClient, AsyncPaperTradingClient


class TestPaperAccountManager:
    """Test suite for paper account management."""
    
    def test_paper_account_identification(self, mock_client):
        """Test identifying paper trading accounts."""
        # Create mock accounts with different patterns
        accounts = [
            AccountNumber(account_number="PAPER123", hash_value="hash1"),
            AccountNumber(account_number="REGULAR456", hash_value="hash2"),
            AccountNumber(account_number="789-PAPER", hash_value="hash3"),
            AccountNumber(account_number="SIM-ACCT", hash_value="hash4")
        ]
        
        # Mock get_account_numbers response
        mock_accounts = AccountNumbers(accounts=accounts)
        mock_client.get_account_numbers.return_value = mock_accounts
        
        # Create paper account manager
        manager = PaperAccountManager(mock_client)
        
        # Test individual account identification
        assert manager.is_paper_account(accounts[0]) is True  # PAPER prefix
        assert manager.is_paper_account(accounts[1]) is False  # Regular account
        assert manager.is_paper_account(accounts[2]) is True  # PAPER suffix
        assert manager.is_paper_account(accounts[3]) is True  # SIM prefix
        
        # Test getting all paper accounts
        paper_accounts = manager.get_paper_accounts()
        assert len(paper_accounts) == 3
        assert accounts[0] in paper_accounts
        assert accounts[1] not in paper_accounts
        assert accounts[2] in paper_accounts
        assert accounts[3] in paper_accounts
        
    def test_get_paper_account_balances(self, mock_client):
        """Test getting paper account balances."""
        # Create mock accounts
        accounts = [
            AccountNumber(account_number="PAPER123", hash_value="hash1"),
            AccountNumber(account_number="PAPER456", hash_value="hash2")
        ]
        
        # Mock get_account_numbers response
        mock_accounts = AccountNumbers(accounts=accounts)
        mock_client.get_account_numbers.return_value = mock_accounts
        
        # Mock get_account responses
        mock_account1 = MagicMock()
        mock_account2 = MagicMock()
        mock_client.get_account.side_effect = [mock_account1, mock_account2]
        
        # Create paper account manager
        manager = PaperAccountManager(mock_client)
        
        # Get paper account balances
        balances = manager.get_paper_account_balances(include_positions=True)
        
        # Verify calls and results
        assert mock_client.get_account.call_count == 2
        assert "PAPER123" in balances
        assert "PAPER456" in balances
        assert balances["PAPER123"] == mock_account1
        assert balances["PAPER456"] == mock_account2


class TestPaperTradingIndicator:
    """Test suite for paper trading indicators."""
    
    def test_indicator_status(self):
        """Test paper trading status indicators."""
        indicator = PaperTradingIndicator(enabled=False)
        
        # Test initial status
        assert indicator.enabled is False
        assert "LIVE TRADING MODE" in indicator.status()
        
        # Test enabling paper trading
        indicator.enable()
        assert indicator.enabled is True
        assert "PAPER TRADING MODE" in indicator.status()
        
        # Test disabling paper trading
        indicator.disable()
        assert indicator.enabled is False
        assert "LIVE TRADING MODE" in indicator.status()
        
    def test_account_validation(self):
        """Test account type validation."""
        indicator = PaperTradingIndicator(enabled=True)
        
        # Test validation when paper trading is enabled
        with pytest.raises(ValueError):
            # Should raise error for trying to use live account in paper mode
            indicator.validate_account_type("live_account", is_paper_account=False)
            
        # Should not raise for paper account in paper mode
        indicator.validate_account_type("paper_account", is_paper_account=True)
        
        # Disable paper trading
        indicator.disable()
        
        # Should not raise for live account in live mode
        indicator.validate_account_type("live_account", is_paper_account=False)
        
        # Will issue a warning but not raise for paper account in live mode
        indicator.validate_account_type("paper_account", is_paper_account=True)


class TestPaperTradingClient:
    """Test suite for paper trading client."""
    
    def test_client_initialization(self, mock_auth):
        """Test paper trading client initialization."""
        with patch('requests.Session'):
            # Create client with paper trading enabled
            client = PaperTradingClient(
                client_id="test_id",
                client_secret="test_secret",
                redirect_uri="test_uri",
                auth=mock_auth,
                paper_trading_enabled=True
            )
            
            # Verify paper trading is enabled
            assert client.is_paper_trading_enabled is True
            assert "PAPER TRADING MODE" in client.paper_trading_status()
            
            # Create client with paper trading disabled
            client = PaperTradingClient(
                client_id="test_id",
                client_secret="test_secret",
                redirect_uri="test_uri",
                auth=mock_auth,
                paper_trading_enabled=False
            )
            
            # Verify paper trading is disabled
            assert client.is_paper_trading_enabled is False
            assert "LIVE TRADING MODE" in client.paper_trading_status()
    
    def test_place_order_validation(self, mock_auth):
        """Test order validation with paper trading client."""
        with patch('requests.Session'):
            # Create client with paper trading enabled
            client = PaperTradingClient(
                client_id="test_id",
                client_secret="test_secret",
                redirect_uri="test_uri",
                auth=mock_auth,
                paper_trading_enabled=True
            )
            
            # Mock the is_paper_account method
            client.is_paper_account = MagicMock()
            
            # Test with paper account
            client.is_paper_account.return_value = True
            client._make_request = MagicMock()  # Mock the request
            
            # Should not raise error for paper account in paper mode
            mock_order = MagicMock()
            client.place_order("paper_account", mock_order)
            
            # Test with live account
            client.is_paper_account.return_value = False
            
            # Should raise error for live account in paper mode
            with pytest.raises(ValueError):
                client.place_order("live_account", mock_order)
            
            # Disable paper trading
            client.disable_paper_trading()
            
            # Should not raise for live account in live mode
            client.place_order("live_account", mock_order)
            
            # Verify calls
            assert client.is_paper_account.call_count == 3
            assert client._make_request.call_count == 2


class TestAsyncPaperTradingClient:
    """Test suite for async paper trading client."""
    
    def test_async_client_initialization(self):
        """Test async paper trading client initialization."""
        with patch('aiohttp.ClientSession'):
            # Create client with paper trading enabled
            client = AsyncPaperTradingClient(
                api_key="test_api_key",
                paper_trading_enabled=True
            )
            
            # Verify paper trading is enabled
            assert client.is_paper_trading_enabled is True
            assert "PAPER TRADING MODE" in client.paper_trading_status()
            
            # Create client with paper trading disabled
            client = AsyncPaperTradingClient(
                api_key="test_api_key",
                paper_trading_enabled=False
            )
            
            # Verify paper trading is disabled
            assert client.is_paper_trading_enabled is False
            assert "LIVE TRADING MODE" in client.paper_trading_status()