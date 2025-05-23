"""Tests for order creation functionality."""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

from schwab.models.generated.trading_models import (
    Order,
    OrderType,
    Instruction as OrderInstruction,
    Session as OrderSession,
    Duration as OrderDuration,
    RequestedDestination,
    TaxLotMethod,
    SpecialInstruction,
    OrderStrategyType,
    OrderLeg,
    OrderLegType,
    PositionEffect,
    QuantityType,
    DivCapGains,
    StopPriceLinkBasis,
    StopPriceLinkType,
    StopType,
)


class TestOrderCreation:
    """Test suite for order creation functionality."""
    
    def test_create_market_order(self, mock_client):
        """Test creating a market order."""
        # Call the method
        order = mock_client.create_market_order(
            symbol="AAPL",
            quantity=100,
            instruction=OrderInstruction.BUY,
            description="APPLE INC"
        )
        
        # Verify result
        assert isinstance(order, Order)
        assert order.order_type == OrderType.MARKET
        assert order.session == OrderSession.normal
        assert order.duration == OrderDuration.day
        assert order.quantity == Decimal("100")
        assert order.order_strategy_type == OrderStrategyType.SINGLE
        assert len(order.order_leg_collection) == 1
        
        # Verify order leg
        leg = order.order_leg_collection[0]
        assert leg.order_leg_type == OrderLegType.EQUITY
        assert leg.instruction == OrderInstruction.BUY
        assert leg.position_effect == PositionEffect.opening
        assert leg.quantity == Decimal("100")
        assert leg.instrument["symbol"] == "AAPL"
        assert leg.instrument["description"] == "APPLE INC"
    
    def test_create_limit_order(self, mock_client):
        """Test creating a limit order."""
        # Call the method
        order = mock_client.create_limit_order(
            symbol="AAPL",
            quantity=100,
            limit_price=150.00,
            instruction=OrderInstruction.BUY,
            description="APPLE INC"
        )
        
        # Verify result
        assert isinstance(order, Order)
        assert order.order_type == OrderType.LIMIT
        assert order.price == Decimal("150.00")
        assert order.quantity == Decimal("100")
        assert len(order.order_leg_collection) == 1
        
        # Verify order leg
        leg = order.order_leg_collection[0]
        assert leg.instruction == OrderInstruction.BUY
        assert leg.instrument["symbol"] == "AAPL"
    
    def test_create_stop_order(self, mock_client):
        """Test creating a stop order."""
        # Call the method
        order = mock_client.create_stop_order(
            symbol="AAPL",
            quantity=100,
            stop_price=140.00,
            instruction=OrderInstruction.SELL,
            description="APPLE INC"
        )
        
        # Verify result
        assert isinstance(order, Order)
        assert order.order_type == OrderType.STOP
        assert order.stop_price == Decimal("140.00")
        assert order.quantity == Decimal("100")
        assert order.stop_price_link_basis == StopPriceLinkBasis.MANUAL
        assert order.stop_price_link_type == StopPriceLinkType.VALUE
        assert order.stop_type == StopType.STANDARD
        
        # Verify order leg
        leg = order.order_leg_collection[0]
        assert leg.instruction == OrderInstruction.SELL
        assert leg.instrument["symbol"] == "AAPL"
    
    def test_create_stop_limit_order(self, mock_client):
        """Test creating a stop-limit order."""
        # Call the method
        order = mock_client.create_stop_limit_order(
            symbol="AAPL",
            quantity=100,
            stop_price=140.00,
            limit_price=138.00,
            instruction=OrderInstruction.SELL,
            description="APPLE INC"
        )
        
        # Verify result
        assert isinstance(order, Order)
        assert order.order_type == OrderType.STOP_LIMIT
        assert order.stop_price == Decimal("140.00")
        assert order.price == Decimal("138.00")
        assert order.quantity == Decimal("100")
        
        # Verify order leg
        leg = order.order_leg_collection[0]
        assert leg.instruction == OrderInstruction.SELL
        assert leg.instrument["symbol"] == "AAPL"
    
    def test_create_trailing_stop_order(self, mock_client):
        """Test creating a trailing stop order."""
        # Call the method
        order = mock_client.create_trailing_stop_order(
            symbol="AAPL",
            quantity=100,
            stop_price_offset=5.00,
            instruction=OrderInstruction.SELL,
            description="APPLE INC"
        )
        
        # Verify result
        assert isinstance(order, Order)
        assert order.order_type == OrderType.TRAILING_STOP
        assert order.stop_price_offset == Decimal("5.00")
        assert order.quantity == Decimal("100")
        
        # Verify order leg
        leg = order.order_leg_collection[0]
        assert leg.instruction == OrderInstruction.SELL
        assert leg.instrument["symbol"] == "AAPL"
    
    def test_create_market_on_close_order(self, mock_client):
        """Test creating a market-on-close order."""
        # Call the method
        order = mock_client.create_market_on_close_order(
            symbol="AAPL",
            quantity=100,
            instruction=OrderInstruction.BUY,
            description="APPLE INC"
        )
        
        # Verify result
        assert isinstance(order, Order)
        assert order.order_type == OrderType.MARKET_ON_CLOSE
        assert order.duration == OrderDuration.DAY  # MOC must be DAY
        assert order.quantity == Decimal("100")
        
        # Verify order leg
        leg = order.order_leg_collection[0]
        assert leg.instruction == OrderInstruction.BUY
        assert leg.instrument["symbol"] == "AAPL"
    
    def test_create_limit_on_close_order(self, mock_client):
        """Test creating a limit-on-close order."""
        # Call the method
        order = mock_client.create_limit_on_close_order(
            symbol="AAPL",
            quantity=100,
            limit_price=150.00,
            instruction=OrderInstruction.BUY,
            description="APPLE INC"
        )
        
        # Verify result
        assert isinstance(order, Order)
        assert order.order_type == OrderType.LIMIT_ON_CLOSE
        assert order.price == Decimal("150.00")
        assert order.duration == OrderDuration.DAY  # LOC must be DAY
        assert order.quantity == Decimal("100")
        
        # Verify order leg
        leg = order.order_leg_collection[0]
        assert leg.instruction == OrderInstruction.BUY
        assert leg.instrument["symbol"] == "AAPL"
    
    def test_order_with_custom_parameters(self, mock_client):
        """Test creating an order with custom parameters."""
        # Call the method with custom parameters
        order = mock_client.create_limit_order(
            symbol="AAPL",
            quantity=100,
            limit_price=150.00,
            instruction=OrderInstruction.BUY,
            description="APPLE INC",
            session=OrderSession.PM,  # After hours
            duration=OrderDuration.GOOD_TILL_CANCEL,
            requested_destination=RequestedDestination.NASDAQ,
            tax_lot_method=TaxLotMethod.FIFO,
            special_instruction=SpecialInstruction.ALL_OR_NONE
        )
        
        # Verify custom parameters
        assert order.session == OrderSession.PM
        assert order.duration == OrderDuration.GOOD_TILL_CANCEL
        assert order.requested_destination == RequestedDestination.NASDAQ
        assert order.tax_lot_method == TaxLotMethod.FIFO
        assert order.special_instruction == SpecialInstruction.ALL_OR_NONE