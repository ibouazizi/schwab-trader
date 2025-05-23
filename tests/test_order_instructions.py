"""Tests for all order instruction types."""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

from schwab.models.generated.trading_models import Instruction as OrderInstruction, OrderType
from tests.helpers.model_factories import create_test_order


class TestOrderInstructions:
    """Test suite for all order instruction types."""
    
    def test_buy_instruction(self, mock_client):
        """Test creating an order with BUY instruction."""
        order = mock_client.create_market_order(
            symbol="AAPL",
            quantity=100,
            instruction=OrderInstruction.BUY,
            description="APPLE INC"
        )
        
        assert order.order_leg_collection[0].instruction == OrderInstruction.BUY
    
    def test_sell_instruction(self, mock_client):
        """Test creating an order with SELL instruction."""
        order = mock_client.create_market_order(
            symbol="AAPL",
            quantity=100,
            instruction=OrderInstruction.SELL,
            description="APPLE INC"
        )
        
        assert order.order_leg_collection[0].instruction == OrderInstruction.SELL
    
    def test_buy_to_cover_instruction(self, mock_client):
        """Test creating an order with BUY_TO_COVER instruction."""
        order = mock_client.create_market_order(
            symbol="AAPL",
            quantity=100,
            instruction=OrderInstruction.BUY_TO_COVER,
            description="APPLE INC"
        )
        
        assert order.order_leg_collection[0].instruction == OrderInstruction.BUY_TO_COVER
    
    def test_sell_short_instruction(self, mock_client):
        """Test creating an order with SELL_SHORT instruction."""
        order = mock_client.create_market_order(
            symbol="AAPL",
            quantity=100,
            instruction=OrderInstruction.SELL_SHORT,
            description="APPLE INC"
        )
        
        assert order.order_leg_collection[0].instruction == OrderInstruction.SELL_SHORT
    
    def test_buy_to_open_instruction(self, mock_client):
        """Test creating an order with BUY_TO_OPEN instruction."""
        order = mock_client.create_limit_order(
            symbol="AAPL_092423C150",
            quantity=1,
            limit_price=3.50,
            instruction=OrderInstruction.BUY_TO_OPEN,
            description="AAPL CALL"
        )
        
        assert order.order_leg_collection[0].instruction == OrderInstruction.BUY_TO_OPEN
    
    def test_buy_to_close_instruction(self, mock_client):
        """Test creating an order with BUY_TO_CLOSE instruction."""
        order = mock_client.create_limit_order(
            symbol="AAPL_092423C150",
            quantity=1,
            limit_price=3.50,
            instruction=OrderInstruction.BUY_TO_CLOSE,
            description="AAPL CALL"
        )
        
        assert order.order_leg_collection[0].instruction == OrderInstruction.BUY_TO_CLOSE
    
    def test_sell_to_open_instruction(self, mock_client):
        """Test creating an order with SELL_TO_OPEN instruction."""
        order = mock_client.create_limit_order(
            symbol="AAPL_092423C150",
            quantity=1,
            limit_price=3.50,
            instruction=OrderInstruction.SELL_TO_OPEN,
            description="AAPL CALL"
        )
        
        assert order.order_leg_collection[0].instruction == OrderInstruction.SELL_TO_OPEN
    
    def test_sell_to_close_instruction(self, mock_client):
        """Test creating an order with SELL_TO_CLOSE instruction."""
        order = mock_client.create_limit_order(
            symbol="AAPL_092423C150",
            quantity=1,
            limit_price=3.50,
            instruction=OrderInstruction.SELL_TO_CLOSE,
            description="AAPL CALL"
        )
        
        assert order.order_leg_collection[0].instruction == OrderInstruction.SELL_TO_CLOSE
    
    def test_exchange_instruction(self, mock_client):
        """Test creating an order with EXCHANGE instruction."""
        order = mock_client.create_market_order(
            symbol="AAPL",
            quantity=100,
            instruction=OrderInstruction.EXCHANGE,
            description="APPLE INC"
        )
        
        assert order.order_leg_collection[0].instruction == OrderInstruction.EXCHANGE
    
    def test_sell_short_exempt_instruction(self, mock_client):
        """Test creating an order with SELL_SHORT_EXEMPT instruction."""
        order = mock_client.create_market_order(
            symbol="AAPL",
            quantity=100,
            instruction=OrderInstruction.SELL_SHORT_EXEMPT,
            description="APPLE INC"
        )
        
        assert order.order_leg_collection[0].instruction == OrderInstruction.SELL_SHORT_EXEMPT
    
    def test_instructions_with_different_order_types(self, mock_client):
        """Test using different instructions with different order types."""
        # Test BUY with limit order
        order = mock_client.create_limit_order(
            symbol="AAPL",
            quantity=100,
            limit_price=150.00,
            instruction=OrderInstruction.BUY,
            description="APPLE INC"
        )
        assert order.order_type == OrderType.LIMIT
        assert order.order_leg_collection[0].instruction == OrderInstruction.BUY
        
        # Test SELL with stop order
        order = mock_client.create_stop_order(
            symbol="AAPL",
            quantity=100,
            stop_price=140.00,
            instruction=OrderInstruction.SELL,
            description="APPLE INC"
        )
        assert order.order_type == OrderType.STOP
        assert order.order_leg_collection[0].instruction == OrderInstruction.SELL
        
        # Test SELL_SHORT with trailing stop order
        order = mock_client.create_trailing_stop_order(
            symbol="AAPL",
            quantity=100,
            stop_price_offset=5.00,
            instruction=OrderInstruction.SELL_SHORT,
            description="APPLE INC"
        )
        assert order.order_type == OrderType.TRAILING_STOP
        assert order.order_leg_collection[0].instruction == OrderInstruction.SELL_SHORT