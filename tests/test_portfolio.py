"""Tests for portfolio management functionality."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from schwab.portfolio import PortfolioManager
from schwab.models.generated.trading_models import Order, Status as OrderStatus, Account, Position
from tests.helpers.model_factories import create_test_order, create_test_account, create_test_position, create_test_order_activity, create_test_execution_leg


class TestPortfolioManager:
    """Test suite for portfolio management functionality."""
    
    def test_add_account(self, mock_client):
        """Test adding an account to the portfolio."""
        # Create a test account
        test_account = create_test_account()
        test_account.securities_account.positions = []
        mock_client.get_account.return_value = test_account
        
        # Create portfolio manager
        portfolio = PortfolioManager(mock_client)
        
        # Add account
        portfolio.add_account("test_account")
        
        # Verify
        mock_client.get_account.assert_called_once_with("test_account", include_positions=True)
        assert "test_account" in portfolio._accounts
        assert "test_account" in portfolio._positions
        
    def test_refresh_positions(self, mock_client):
        """Test refreshing positions."""
        # Mock account responses
        mock_account1 = MagicMock(spec=Account)
        mock_account1.securities_account.positions = []
        mock_account2 = MagicMock(spec=Account)
        mock_account2.securities_account.positions = []
        
        mock_client.get_account.side_effect = [mock_account1, mock_account2]
        
        # Create portfolio manager and add accounts
        portfolio = PortfolioManager(mock_client)
        portfolio._accounts = {"account1": None, "account2": None}
        portfolio._positions = {"account1": {}, "account2": {}}
        portfolio._monitored_accounts = {"account1", "account2"}
        
        # Refresh positions
        portfolio.refresh_positions()
        
        # Verify
        assert mock_client.get_account.call_count == 2
        assert portfolio._accounts["account1"] == mock_account1
        assert portfolio._accounts["account2"] == mock_account2
        
    def test_place_order(self, mock_client):
        """Test placing an order."""
        # Mock account
        mock_account = MagicMock(spec=Account)
        
        # Mock order response
        mock_order = MagicMock(spec=Order)
        mock_order.order_id = 12345
        mock_order.order_type = "MARKET"
        mock_order.quantity = Decimal("100")
        
        # Mock order list response
        mock_order_list = MagicMock()
        mock_order_list.orders = [mock_order]
        
        mock_client.get_account.return_value = mock_account
        mock_client.get_orders.return_value = mock_order_list
        
        # Create portfolio manager and add account
        portfolio = PortfolioManager(mock_client)
        portfolio._accounts = {"test_account": mock_account}
        portfolio._positions = {"test_account": {}}
        
        # Create a test order
        test_order = MagicMock(spec=Order)
        test_order.order_type = "MARKET"
        test_order.quantity = Decimal("100")
        
        # Place order
        order_id = portfolio.place_order("test_account", test_order)
        
        # Verify
        mock_client.place_order.assert_called_once_with("test_account", test_order)
        assert order_id == 12345
        assert 12345 in portfolio._orders
        assert 12345 in portfolio._monitored_orders
        
    def test_get_portfolio_summary(self, mock_client):
        """Test getting portfolio summary."""
        # Create portfolio manager
        portfolio = PortfolioManager(mock_client)
        
        # Mock accounts with balances
        account1 = MagicMock(spec=Account)
        account1.securities_account.current_balances.cash_balance = Decimal("1000.00")
        
        account2 = MagicMock(spec=Account)
        account2.securities_account.current_balances.cash_balance = Decimal("2000.00")
        
        portfolio._accounts = {
            "account1": account1,
            "account2": account2
        }
        
        # Mock positions
        position1 = MagicMock(spec=Position)
        position1.market_value = Decimal("5000.00")
        position1.instrument.symbol = "AAPL"
        position1.instrument.type = "EQUITY"
        position1.long_quantity = Decimal("10")
        position1.short_quantity = Decimal("0")
        position1.average_price = Decimal("450.00")
        
        position2 = MagicMock(spec=Position)
        position2.market_value = Decimal("3000.00")
        position2.instrument.symbol = "MSFT"
        position2.instrument.type = "EQUITY"
        position2.long_quantity = Decimal("15")
        position2.short_quantity = Decimal("0")
        position2.average_price = Decimal("180.00")
        
        portfolio._positions = {
            "account1": {"AAPL": position1},
            "account2": {"MSFT": position2}
        }
        
        # Get summary
        summary = portfolio.get_portfolio_summary()
        
        # Verify
        assert summary["total_cash"] == Decimal("3000.00")
        assert summary["total_equity"] == Decimal("8000.00")
        assert summary["total_value"] == Decimal("11000.00")
        # Cash allocation should be rounded to 2 decimal places (3000/11000 * 100 = 27.27...)
        assert summary["cash_allocation"] == Decimal("27.27")
        assert summary["equity_allocation"] == Decimal("72.73")
        assert "AAPL" in summary["positions_by_symbol"]
        assert "MSFT" in summary["positions_by_symbol"]
        
    def test_get_position(self, mock_client):
        """Test getting a specific position."""
        # Create portfolio manager
        portfolio = PortfolioManager(mock_client)
        
        # Mock positions for AAPL across accounts
        position1 = MagicMock(spec=Position)
        position1.market_value = Decimal("5000.00")
        position1.long_quantity = Decimal("10")
        position1.short_quantity = Decimal("0")
        position1.average_price = Decimal("450.00")
        
        position2 = MagicMock(spec=Position)
        position2.market_value = Decimal("2500.00")
        position2.long_quantity = Decimal("5")
        position2.short_quantity = Decimal("0")
        position2.average_price = Decimal("450.00")
        
        portfolio._positions = {
            "account1": {"AAPL": position1},
            "account2": {"AAPL": position2}
        }
        
        # Get position
        position = portfolio.get_position("AAPL")
        
        # Verify
        assert position["symbol"] == "AAPL"
        assert position["quantity"] == Decimal("15")
        assert position["market_value"] == Decimal("7500.00")
        assert position["cost_basis"] == Decimal("6750.00")
        assert position["average_price"] == Decimal("450.00")
        assert position["gain_loss"] == Decimal("750.00")
        assert position["gain_loss_pct"] == Decimal("11.11111111111111")
        
    def test_order_history_filtering(self, mock_client):
        """Test filtering order history."""
        # Create portfolio manager
        portfolio = PortfolioManager(mock_client)
        
        # Mock orders with different dates and statuses
        order1 = MagicMock(spec=Order)
        order1.order_id = 1
        order1.entered_time = datetime.now() - timedelta(days=1)
        order1.status = OrderStatus.FILLED
        
        order2 = MagicMock(spec=Order)
        order2.order_id = 2
        order2.entered_time = datetime.now() - timedelta(days=5)
        order2.status = OrderStatus.CANCELED
        
        order3 = MagicMock(spec=Order)
        order3.order_id = 3
        order3.entered_time = datetime.now() - timedelta(days=10)
        order3.status = OrderStatus.FILLED
        
        portfolio._orders = {1: order1, 2: order2, 3: order3}
        
        # Test date filtering
        from_date = datetime.now() - timedelta(days=7)
        filtered_orders = portfolio.get_order_history(from_date=from_date)
        assert len(filtered_orders) == 2
        assert 1 in [o.order_id for o in filtered_orders]
        assert 2 in [o.order_id for o in filtered_orders]
        
        # Test status filtering
        filled_orders = portfolio.get_order_history(status=OrderStatus.FILLED)
        assert len(filled_orders) == 2
        assert all(o.status == OrderStatus.FILLED for o in filled_orders)