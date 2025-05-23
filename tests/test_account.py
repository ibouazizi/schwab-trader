"""Tests for account management functionality."""

import pytest
from unittest.mock import MagicMock, patch

from schwab.models.generated.trading_models import AccountNumberHash, Account, Position
from tests.helpers.model_factories import create_test_account, create_test_position


class TestAccountManagement:
    """Test suite for account management functionality."""
    
    def test_get_account_numbers(self, mock_client):
        """Test getting account numbers."""
        # Mock the _make_request method to return sample data
        sample_data = [
            {"account_number": "123456789", "hash_value": "encrypted123"},
            {"account_number": "987654321", "hash_value": "encrypted987"}
        ]
        mock_client._make_request.return_value = sample_data
        
        # Call the method
        result = mock_client.get_account_numbers()
        
        # Verify result
        # Expect a list of generated AccountNumberHash
        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], AccountNumberHash)
        assert result[0].account_number == "123456789"
        assert result[0].hash_value == "encrypted123"
        assert result[1].account_number == "987654321"
        assert result[1].hash_value == "encrypted987"
        
        # Verify API call
        # Verify correct API endpoint was called
        mock_client._make_request.assert_called_once_with(
            "GET", "/accounts/accountNumbers"
        )
    
    def test_get_accounts(self, mock_client):
        """Test getting all accounts."""
        # Mock the _make_request method to return sample data
        sample_data = [
            {
                "securities_account": {
                    "account_number": "123456789",
                    "round_trips": 0,
                    "is_day_trader": False,
                    "is_closing_only_restricted": False,
                    "pfcb_flag": False,
                    "initial_balances": {
                        "accrued_interest": 0,
                        "available_funds_non_marginable_trade": 10000,
                        "bond_value": 0,
                        "buying_power": 20000,
                        "cash_balance": 10000,
                        "cash_available_for_trading": 10000,
                        "cash_receipts": 0,
                        "day_trading_buying_power": 0,
                        "day_trading_buying_power_call": 0,
                        "day_trading_equity_call": 0,
                        "equity": 10000,
                        "equity_percentage": 100,
                        "liquidation_value": 10000,
                        "long_margin_value": 0,
                        "long_option_market_value": 0,
                        "long_stock_value": 0,
                        "maintenance_call": 0,
                        "maintenance_requirement": 0,
                        "margin": 0,
                        "margin_equity": 0,
                        "money_market_fund": 0,
                        "mutual_fund_value": 0,
                        "reg_t_call": 0,
                        "short_margin_value": 0,
                        "short_option_market_value": 0,
                        "short_stock_value": 0,
                        "total_cash": 10000,
                        "is_in_call": False,
                        "unsettled_cash": 0,
                        "pending_deposits": 0,
                        "margin_balance": 0,
                        "short_balance": 0,
                        "account_value": 10000
                    },
                    "current_balances": {
                        "available_funds": 10000,
                        "available_funds_non_marginable_trade": 10000,
                        "buying_power": 20000,
                        "buying_power_non_marginable_trade": 10000,
                        "day_trading_buying_power": 0,
                        "day_trading_buying_power_call": 0,
                        "equity": 10000,
                        "equity_percentage": 100,
                        "long_margin_value": 0,
                        "maintenance_call": 0,
                        "maintenance_requirement": 0,
                        "margin_balance": 0,
                        "reg_t_call": 0,
                        "short_balance": 0,
                        "short_margin_value": 0,
                        "sma": 0,
                        "is_in_call": False,
                        "stock_buying_power": 20000,
                        "option_buying_power": 20000
                    },
                    "projected_balances": {
                        "available_funds": 10000,
                        "available_funds_non_marginable_trade": 10000,
                        "buying_power": 20000,
                        "buying_power_non_marginable_trade": 10000,
                        "day_trading_buying_power": 0,
                        "day_trading_buying_power_call": 0,
                        "equity": 10000,
                        "equity_percentage": 100,
                        "long_margin_value": 0,
                        "maintenance_call": 0,
                        "maintenance_requirement": 0,
                        "margin_balance": 0,
                        "reg_t_call": 0,
                        "short_balance": 0,
                        "short_margin_value": 0,
                        "sma": 0,
                        "is_in_call": False,
                        "stock_buying_power": 20000,
                        "option_buying_power": 20000
                    }
                }
            }
        ]
        mock_client._make_request.return_value = sample_data
        
        # Call the method without positions
        result = mock_client.get_accounts(include_positions=False)
        
        # Verify result
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Account)
        assert result[0].securities_account.account_number == "123456789"
        assert result[0].securities_account.current_balances.buying_power == 20000
        
        # Verify API call
        mock_client._make_request.assert_called_once_with(
            "GET", "/accounts", params=None
        )
        
        # Reset mock and test with positions
        mock_client._make_request.reset_mock()
        
        # Call the method with positions
        result = mock_client.get_accounts(include_positions=True)
        
        # Verify API call
        mock_client._make_request.assert_called_once_with(
            "GET", "/accounts/positions" if True else "/accounts",
            params={"fields": "positions"} if True else None
        )
    
    def test_get_account(self, mock_client):
        """Test getting specific account."""
        # Mock the _make_request method to return sample data
        sample_data = {
            "securities_account": {
                "account_number": "123456789",
                "round_trips": 0,
                "is_day_trader": False,
                "is_closing_only_restricted": False,
                "pfcb_flag": False,
                "positions": [
                    {
                        "short_quantity": 0,
                        "average_price": 150.0,
                        "current_day_profit_loss": 500.0,
                        "current_day_profit_loss_percentage": 5.0,
                        "long_quantity": 10,
                        "settled_long_quantity": 10,
                        "settled_short_quantity": 0,
                        "aged_quantity": 10,
                        "instrument": {
                            "cusip": "037833100",
                            "symbol": "AAPL",
                            "description": "APPLE INC",
                            "instrument_id": 123,
                            "net_change": 5.0,
                            "type": "EQUITY"
                        },
                        "market_value": 1550.0,
                        "maintenance_requirement": 0.0,
                        "average_long_price": 150.0,
                        "average_short_price": 0.0,
                        "tax_lot_average_long_price": 150.0,
                        "tax_lot_average_short_price": 0.0,
                        "long_open_profit_loss": 50.0,
                        "short_open_profit_loss": 0.0,
                        "previous_session_long_quantity": 10,
                        "previous_session_short_quantity": 0,
                        "current_day_cost": 1500.0
                    }
                ],
                "initial_balances": {
                    "accrued_interest": 0,
                    "available_funds_non_marginable_trade": 10000,
                    "bond_value": 0,
                    "buying_power": 20000,
                    "cash_balance": 10000,
                    "cash_available_for_trading": 10000,
                    "cash_receipts": 0,
                    "day_trading_buying_power": 0,
                    "day_trading_buying_power_call": 0,
                    "day_trading_equity_call": 0,
                    "equity": 10000,
                    "equity_percentage": 100,
                    "liquidation_value": 10000,
                    "long_margin_value": 0,
                    "long_option_market_value": 0,
                    "long_stock_value": 0,
                    "maintenance_call": 0,
                    "maintenance_requirement": 0,
                    "margin": 0,
                    "margin_equity": 0,
                    "money_market_fund": 0,
                    "mutual_fund_value": 0,
                    "reg_t_call": 0,
                    "short_margin_value": 0,
                    "short_option_market_value": 0,
                    "short_stock_value": 0,
                    "total_cash": 10000,
                    "is_in_call": False,
                    "unsettled_cash": 0,
                    "pending_deposits": 0,
                    "margin_balance": 0,
                    "short_balance": 0,
                    "account_value": 10000
                },
                "current_balances": {
                    "available_funds": 10000,
                    "available_funds_non_marginable_trade": 10000,
                    "buying_power": 20000,
                    "buying_power_non_marginable_trade": 10000,
                    "day_trading_buying_power": 0,
                    "day_trading_buying_power_call": 0,
                    "equity": 10000,
                    "equity_percentage": 100,
                    "long_margin_value": 0,
                    "maintenance_call": 0,
                    "maintenance_requirement": 0,
                    "margin_balance": 0,
                    "reg_t_call": 0,
                    "short_balance": 0,
                    "short_margin_value": 0,
                    "sma": 0,
                    "is_in_call": False,
                    "stock_buying_power": 20000,
                    "option_buying_power": 20000
                },
                "projected_balances": {
                    "available_funds": 10000,
                    "available_funds_non_marginable_trade": 10000,
                    "buying_power": 20000,
                    "buying_power_non_marginable_trade": 10000,
                    "day_trading_buying_power": 0,
                    "day_trading_buying_power_call": 0,
                    "equity": 10000,
                    "equity_percentage": 100,
                    "long_margin_value": 0,
                    "maintenance_call": 0,
                    "maintenance_requirement": 0,
                    "margin_balance": 0,
                    "reg_t_call": 0,
                    "short_balance": 0,
                    "short_margin_value": 0,
                    "sma": 0,
                    "is_in_call": False,
                    "stock_buying_power": 20000,
                    "option_buying_power": 20000
                }
            }
        }
        mock_client._make_request.return_value = sample_data
        
        # Call the method with positions
        result = mock_client.get_account(
            account_number="encrypted123", include_positions=True
        )
        
        # Verify result
        assert isinstance(result, Account)
        assert result.securities_account.account_number == "123456789"
        assert len(result.securities_account.positions) == 1
        assert result.securities_account.positions[0].instrument.symbol == "AAPL"
        assert result.securities_account.positions[0].long_quantity == 10
        assert result.securities_account.positions[0].market_value == 1550.0
        
        # Verify API call uses correct endpoint and params
        mock_client._make_request.assert_called_once_with(
            "GET", "/accounts/encrypted123", params={"fields": "positions"}
        )