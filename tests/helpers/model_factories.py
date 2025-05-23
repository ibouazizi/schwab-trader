"""
Model factories for testing.

This module provides factory functions for creating model instances
that can be used in tests.
"""

from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from schwab.models.generated.trading_models import (
    Order,
    OrderType,
    Status as OrderStatus,
    Instruction as OrderInstruction,
    Session as OrderSession,
    Duration as OrderDuration,
    ComplexOrderStrategyType,
    OrderStrategyType,
    OrderLegCollection as OrderLeg,
    OrderLegType,
    PositionEffect,
    QuantityType,
    DivCapGains,
    Account,
    Position,
    OrderActivity,
    ExecutionLeg
)

def create_test_order(
    order_id: int = 12345,
    symbol: str = "AAPL",
    quantity: Decimal = Decimal("100"),
    order_type: OrderType = OrderType.market,
    instruction: OrderInstruction = OrderInstruction.buy,
    status: OrderStatus = OrderStatus.working,
    **kwargs
) -> Order:
    """
    Create an Order model instance for testing.
    
    Args:
        order_id: The order ID
        symbol: The ticker symbol
        quantity: Order quantity
        order_type: Type of order (market, limit, etc.)
        instruction: Order instruction (buy, sell, etc.)
        status: Order status
        **kwargs: Additional fields to override defaults
        
    Returns:
        An Order model instance
    """
    # Default values for an order
    defaults = {
        "order_id": order_id,
        "session": OrderSession.normal,
        "duration": OrderDuration.day,
        "order_type": order_type,
        "complex_order_strategy_type": ComplexOrderStrategyType.none,
        "quantity": quantity,
        "filled_quantity": Decimal("0"),
        "remaining_quantity": quantity,
        "order_strategy_type": OrderStrategyType.single,
        "status": status,
        "entered_time": datetime.now(timezone.utc),
        "order_leg_collection": [
            {
                "order_leg_type": OrderLegType.equity,
                "leg_id": 1,
                "instrument": {
                    "symbol": symbol,
                    "description": f"{symbol} Stock",
                    "instrument_id": 12345,
                    "net_change": Decimal("0"),
                    "type": "EQUITY"
                },
                "instruction": instruction,
                "position_effect": PositionEffect.opening,
                "quantity": quantity,
                "quantity_type": QuantityType.all_shares,
                "div_cap_gains": DivCapGains.reinvest
            }
        ]
    }
    
    # Override with any provided kwargs
    defaults.update(kwargs)
    
    # Create the Order model
    return Order.model_validate(defaults)

def create_test_account(
    account_number: str = "123456789",
    hash_value: str = "abcdef1234567890",
    **kwargs
) -> Account:
    """
    Create an Account model instance for testing.
    
    Args:
        account_number: The account number
        hash_value: The hashed account number
        **kwargs: Additional fields to override defaults
        
    Returns:
        An Account model instance
    """
    # Default values for an account
    defaults = {
        "account_number": account_number,
        "hash_value": hash_value,
        "securities_account": {
            "account_id": "123456789",
            "current_balances": {
                "cash_balance": Decimal("10000.00"),
                "money_market_fund": Decimal("5000.00"),
                "long_market_value": Decimal("50000.00"),
                "short_market_value": Decimal("0.00"),
                "buying_power": Decimal("20000.00"),
                "available_funds": Decimal("15000.00"),
                "cash_available_for_trading": Decimal("15000.00"),
                "day_trading_buying_power": Decimal("60000.00"),
                "equity": Decimal("65000.00"),
                "liquidation_value": Decimal("65000.00")
            },
            "positions": []
        },
        "type": "MARGIN"
    }
    
    # Override with any provided kwargs
    defaults.update(kwargs)
    
    # Create the Account model
    return Account.model_validate(defaults)

def create_test_position(
    symbol: str = "AAPL",
    quantity: Decimal = Decimal("100"),
    average_price: Decimal = Decimal("150.00"),
    market_value: Decimal = Decimal("15000.00"),
    **kwargs
) -> Position:
    """
    Create a Position model instance for testing.
    
    Args:
        symbol: The ticker symbol
        quantity: Position quantity
        average_price: Average price per share
        market_value: Current market value
        **kwargs: Additional fields to override defaults
        
    Returns:
        A Position model instance
    """
    # Default values for a position
    defaults = {
        "long_quantity": quantity,
        "short_quantity": Decimal("0"),
        "average_price": average_price,
        "market_value": market_value,
        "cost_basis": average_price * quantity,
        "instrument": {
            "symbol": symbol,
            "description": f"{symbol} Stock",
            "instrument_id": 12345,
            "net_change": Decimal("0"),
            "type": "EQUITY"
        }
    }
    
    # Override with any provided kwargs
    defaults.update(kwargs)
    
    # Create the Position model
    return Position.model_validate(defaults)

def create_test_execution_leg(
    leg_id: int = 1,
    price: float = 150.50,
    quantity: float = 100.0,
    time: Optional[datetime] = None,
    instrument_id: int = 12345,
    **kwargs
) -> ExecutionLeg:
    """
    Create an ExecutionLeg model instance for testing.
    
    Args:
        leg_id: Execution leg ID
        price: Execution price
        quantity: Execution quantity
        time: Execution timestamp
        instrument_id: Instrument ID
        **kwargs: Additional fields to override defaults
        
    Returns:
        An ExecutionLeg model instance
    """
    # Default execution time if not provided
    if time is None:
        time = datetime.now(timezone.utc)
        
    # Default values for an execution leg
    defaults = {
        "leg_id": leg_id,
        "price": price,
        "quantity": quantity,
        "time": time,
        "instrument_id": instrument_id
    }
    
    # Override with any provided kwargs
    defaults.update(kwargs)
    
    # Create the ExecutionLeg model
    return ExecutionLeg.model_validate(defaults)

def create_test_order_activity(
    activity_type: str = "EXECUTION",
    execution_type: str = "FILL",
    quantity: float = 100.0,
    order_remaining_quantity: float = 0.0,
    execution_legs: Optional[List[Dict[str, Any]]] = None,
    **kwargs
) -> OrderActivity:
    """
    Create an OrderActivity model instance for testing.
    
    Args:
        activity_type: Type of order activity
        execution_type: Type of execution
        quantity: Execution quantity
        order_remaining_quantity: Remaining quantity
        execution_legs: List of execution legs
        **kwargs: Additional fields to override defaults
        
    Returns:
        An OrderActivity model instance
    """
    # Default execution legs if not provided
    if execution_legs is None:
        execution_legs = [
            create_test_execution_leg().model_dump()
        ]
        
    # Default values for an order activity
    defaults = {
        "activity_type": activity_type,
        "execution_type": execution_type,
        "quantity": quantity,
        "order_remaining_quantity": order_remaining_quantity,
        "execution_legs": execution_legs
    }
    
    # Override with any provided kwargs
    defaults.update(kwargs)
    
    # Create the OrderActivity model
    return OrderActivity.model_validate(defaults)