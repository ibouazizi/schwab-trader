"""Tests for order management functionality."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from schwab.models.generated.trading_models import Order, OrderType, Status as OrderStatus, Instruction as OrderInstruction
from schwab.models.order_validation import OrderValidationError
from tests.helpers.model_factories import create_test_order


class TestOrderManagement:
    """Test suite for order management functionality."""
    
    def test_place_order(self, mock_client):
        """Test placing an order."""
        # Create a sample order
        order = mock_client.create_market_order(
            symbol="AAPL",
            quantity=100,
            instruction=OrderInstruction.BUY,
            description="APPLE INC"
        )
        
        # Mock _make_request to return empty dict (success)
        mock_client._make_request.return_value = {}
        
        # Call place_order
        mock_client.place_order(account_number="encrypted123", order=order)
        
        # Verify API call
        mock_client._make_request.assert_called_once_with(
            "POST", 
            "/accounts/encrypted123/orders/place", 
            json=order.model_dump(by_alias=True)
        )
    
    def test_get_orders(self, mock_client):
        """Test getting orders history."""
        # Sample data
        sample_data = {
            "orders": [
                {
                    "session": "NORMAL",
                    "duration": "DAY",
                    "order_type": "MARKET",
                    "complex_order_strategy_type": "NONE",
                    "quantity": 100,
                    "filled_quantity": 100,
                    "remaining_quantity": 0,
                    "order_strategy_type": "SINGLE",
                    "order_id": 12345,
                    "status": "FILLED",
                    "entered_time": "2023-06-01T10:00:00.000Z",
                    "order_leg_collection": [
                        {
                            "order_leg_type": "EQUITY",
                            "leg_id": 1,
                            "instrument": {
                                "symbol": "AAPL",
                                "description": "APPLE INC",
                                "instrument_id": 123,
                                "net_change": 0,
                                "type": "EQUITY"
                            },
                            "instruction": "BUY",
                            "position_effect": "OPENING",
                            "quantity": 100,
                            "quantity_type": "ALL_SHARES",
                            "div_cap_gains": "REINVEST"
                        }
                    ]
                }
            ]
        }
        mock_client._make_request.return_value = sample_data
        
        # Call get_orders
        from_date = datetime.now() - timedelta(days=7)
        to_date = datetime.now()
        result = mock_client.get_orders(
            account_number="encrypted123",
            from_entered_time=from_date,
            to_entered_time=to_date,
            max_results=10,
            status="WORKING"
        )
        
        # Verify result
        assert isinstance(result, OrderList)
        assert len(result.orders) == 1
        assert result.orders[0].order_id == 12345
        assert result.orders[0].status == "FILLED"
        
        # Verify API call
        mock_client._make_request.assert_called_once()
        args, kwargs = mock_client._make_request.call_args
        assert args[0] == "GET"
        assert args[1] == "/accounts/encrypted123/orders/history"
        assert "fromDate" in kwargs["params"]
        assert "toDate" in kwargs["params"]
        assert kwargs["params"]["maxResults"] == 10
        assert kwargs["params"]["status"] == "WORKING"
    
    def test_get_order(self, mock_client):
        """Test getting a specific order."""
        # Sample data
        sample_data = {
            "session": "NORMAL",
            "duration": "DAY",
            "order_type": "MARKET",
            "complex_order_strategy_type": "NONE",
            "quantity": 100,
            "filled_quantity": 100,
            "remaining_quantity": 0,
            "order_strategy_type": "SINGLE",
            "order_id": 12345,
            "status": "FILLED",
            "entered_time": "2023-06-01T10:00:00.000Z",
            "order_leg_collection": [
                {
                    "order_leg_type": "EQUITY",
                    "leg_id": 1,
                    "instrument": {
                        "symbol": "AAPL",
                        "description": "APPLE INC",
                        "instrument_id": 123,
                        "net_change": 0,
                        "type": "EQUITY"
                    },
                    "instruction": "BUY",
                    "position_effect": "OPENING",
                    "quantity": 100,
                    "quantity_type": "ALL_SHARES",
                    "div_cap_gains": "REINVEST"
                }
            ]
        }
        mock_client._make_request.return_value = sample_data
        
        # Call get_order
        result = mock_client.get_order(
            account_number="encrypted123",
            order_id=12345
        )
        
        # Verify result
        assert isinstance(result, Order)
        assert result.order_id == 12345
        assert result.status == "FILLED"
        
        # Verify API call
        mock_client._make_request.assert_called_once_with(
            "GET", "/accounts/encrypted123/orders/12345/details"
        )
    
    def test_replace_order(self, mock_client):
        """Test replacing an order."""
        # Create a sample replacement order
        new_order = mock_client.create_limit_order(
            symbol="AAPL",
            quantity=150,
            limit_price=155.00,
            instruction=OrderInstruction.BUY,
            description="APPLE INC"
        )
        
        # Mock _make_request to return empty dict (success)
        mock_client._make_request.return_value = {}
        
        # Call replace_order
        mock_client.replace_order(
            account_number="encrypted123",
            order_id=12345,
            new_order=new_order
        )
        
        # Verify API call
        mock_client._make_request.assert_called_once_with(
            "PUT", 
            "/accounts/encrypted123/orders/12345/replace", 
            json=new_order.model_dump(by_alias=True)
        )
    
    def test_cancel_order(self, mock_client):
        """Test cancelling an order."""
        # Mock _make_request to return empty dict (success)
        mock_client._make_request.return_value = {}
        
        # Call cancel_order
        mock_client.cancel_order(
            account_number="encrypted123",
            order_id=12345
        )
        
        # Verify API call
        mock_client._make_request.assert_called_once_with(
            "DELETE", "/accounts/encrypted123/orders/12345/cancel"
        )
    
    def test_modify_order_price(self, mock_client):
        """Test modifying order price."""
        # Mock get_order to return a sample order
        sample_order = Order(
            session="NORMAL",
            duration="DAY",
            order_type=OrderType.LIMIT,
            complex_order_strategy_type="NONE",
            quantity=Decimal("100"),
            filled_quantity=Decimal("0"),
            remaining_quantity=Decimal("100"),
            price=Decimal("150.00"),
            order_strategy_type="SINGLE",
            order_id=12345,
            status="WORKING",
            order_leg_collection=[
                {
                    "order_leg_type": "EQUITY",
                    "leg_id": 1,
                    "instrument": {
                        "symbol": "AAPL",
                        "description": "APPLE INC",
                        "instrument_id": 123,
                        "net_change": 0,
                        "type": "EQUITY"
                    },
                    "instruction": "BUY",
                    "position_effect": "OPENING",
                    "quantity": 100,
                    "quantity_type": "ALL_SHARES",
                    "div_cap_gains": "REINVEST"
                }
            ]
        )
        mock_client.get_order = MagicMock(return_value=sample_order)
        
        # Mock replace_order
        mock_client.replace_order = MagicMock()
        
        # Call modify_order_price
        mock_client.modify_order_price(
            account_number="encrypted123",
            order_id=12345,
            new_price=155.00
        )
        
        # Verify that get_order was called
        mock_client.get_order.assert_called_once_with(
            account_number="encrypted123",
            order_id=12345
        )
        
        # Verify that replace_order was called with updated order
        mock_client.replace_order.assert_called_once()
        args, kwargs = mock_client.replace_order.call_args
        assert args[0] == "encrypted123"
        assert args[1] == 12345
        assert args[2].price == Decimal("155.00")
    
    def test_modify_order_quantity(self, mock_client):
        """Test modifying order quantity."""
        # Mock get_order to return a sample order
        sample_order = Order(
            session="NORMAL",
            duration="DAY",
            order_type=OrderType.MARKET,
            complex_order_strategy_type="NONE",
            quantity=Decimal("100"),
            filled_quantity=Decimal("0"),
            remaining_quantity=Decimal("100"),
            order_strategy_type="SINGLE",
            order_id=12345,
            status="WORKING",
            order_leg_collection=[
                {
                    "order_leg_type": "EQUITY",
                    "leg_id": 1,
                    "instrument": {
                        "symbol": "AAPL",
                        "description": "APPLE INC",
                        "instrument_id": 123,
                        "net_change": 0,
                        "type": "EQUITY"
                    },
                    "instruction": "BUY",
                    "position_effect": "OPENING",
                    "quantity": 100,
                    "quantity_type": "ALL_SHARES",
                    "div_cap_gains": "REINVEST"
                }
            ]
        )
        mock_client.get_order = MagicMock(return_value=sample_order)
        
        # Mock replace_order
        mock_client.replace_order = MagicMock()
        
        # Call modify_order_quantity
        mock_client.modify_order_quantity(
            account_number="encrypted123",
            order_id=12345,
            new_quantity=150
        )
        
        # Verify that get_order was called
        mock_client.get_order.assert_called_once_with(
            account_number="encrypted123",
            order_id=12345
        )
        
        # Verify that replace_order was called with updated order
        mock_client.replace_order.assert_called_once()
        args, kwargs = mock_client.replace_order.call_args
        assert args[0] == "encrypted123"
        assert args[1] == 12345
        assert args[2].quantity == Decimal("150")
    
    def test_batch_cancel_orders(self, mock_client):
        """Test batch cancelling orders."""
        # Mock cancel_order to succeed
        mock_client.cancel_order = MagicMock()
        
        # Call batch_cancel_orders
        result = mock_client.batch_cancel_orders(
            account_number="encrypted123",
            order_ids=[12345, 12346, 12347]
        )
        
        # Verify that cancel_order was called for each order ID
        assert mock_client.cancel_order.call_count == 3
        expected_calls = [
            ((("encrypted123", 12345), {})),
            ((("encrypted123", 12346), {})),
            ((("encrypted123", 12347), {}))
        ]
        assert mock_client.cancel_order.call_args_list == expected_calls
        
        # Verify result
        assert result == {12345: True, 12346: True, 12347: True}
    
    def test_batch_modify_orders(self, mock_client):
        """Test batch modifying orders."""
        # Mock sample orders
        sample_order = Order(
            session="NORMAL",
            duration="DAY",
            order_type=OrderType.LIMIT,
            complex_order_strategy_type="NONE",
            quantity=Decimal("100"),
            filled_quantity=Decimal("0"),
            remaining_quantity=Decimal("100"),
            price=Decimal("150.00"),
            order_strategy_type="SINGLE",
            order_id=12345,
            status="WORKING",
            order_leg_collection=[
                {
                    "order_leg_type": "EQUITY",
                    "leg_id": 1,
                    "instrument": {
                        "symbol": "AAPL",
                        "description": "APPLE INC",
                        "instrument_id": 123,
                        "net_change": 0,
                        "type": "EQUITY"
                    },
                    "instruction": "BUY",
                    "position_effect": "OPENING",
                    "quantity": 100,
                    "quantity_type": "ALL_SHARES",
                    "div_cap_gains": "REINVEST"
                }
            ]
        )
        
        # Mock get_order and replace_order
        mock_client.get_order = MagicMock(return_value=sample_order)
        mock_client.replace_order = MagicMock()
        
        # Call batch_modify_orders
        modifications = [
            {"order_id": 12345, "price": 155.00},
            {"order_id": 12346, "quantity": 200},
            {"order_id": 12347, "price": 160.00, "quantity": 150}
        ]
        
        result = mock_client.batch_modify_orders(
            account_number="encrypted123",
            modifications=modifications
        )
        
        # Verify that get_order and replace_order were called for each modification
        assert mock_client.get_order.call_count == 3
        assert mock_client.replace_order.call_count == 3