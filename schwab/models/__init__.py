"""Models for the Schwab API."""

# Import custom models that don't have generated equivalents
from .base import BaseModel, AccountNumbers
from .execution import ExecutionReport
from .order_validation import OrderValidator, OrderValidationError

# Import and re-export generated models
from .generated.trading_models import (
    # Account models
    AccountNumberHash as AccountNumber,
    Account,
    
    # Order models
    Order,
    OrderType,
    Session as OrderSession,
    Duration as OrderDuration,
    RequestedDestination,
    TaxLotMethod,
    SpecialInstruction,
    ComplexOrderStrategyType,
    OrderStrategyType,
    OrderLeg,
    OrderLegType,
    PositionEffect,
    QuantityType,
    DivCapGains as DividendCapitalGains,
    StopPriceLinkBasis,
    StopPriceLinkType,
    StopType,
    Instruction as OrderInstruction,
    Status as OrderStatus,
    
    # Transaction models
    Transaction,
    TransactionType,
    
    # User preference models
    UserPreference,
    StreamerInfo
)

from .generated.market_data_models import (
    # Error models
    ErrorResponse,
    
    # Quote models
    QuoteResponse,
    EquityResponse as QuoteData,
    QuoteEquity as Quote,
    AssetMainType
)

__all__ = [
    # Base models
    "BaseModel", "AccountNumber", "AccountNumbers", "ErrorResponse",
    
    # Account models
    "Account",
    
    # Order models
    "Order", "OrderType", "OrderInstruction", "OrderSession", "OrderStatus",
    "OrderDuration", "RequestedDestination", "TaxLotMethod", "SpecialInstruction",
    "ComplexOrderStrategyType", "OrderStrategyType", "OrderLeg", "OrderLegType",
    "PositionEffect", "QuantityType", "DividendCapitalGains", "StopPriceLinkBasis",
    "StopPriceLinkType", "StopType",
    
    # Execution models
    "ExecutionReport",
    
    # Quote models
    "QuoteResponse", "QuoteData", "Quote", "AssetMainType",
    
    # Transaction models
    "Transaction", "TransactionType",
    
    # User preference models
    "UserPreference", "StreamerInfo",
    
    # Validation models
    "OrderValidator", "OrderValidationError"
]
