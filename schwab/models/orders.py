"""
Legacy order models for backward compatibility.

This file is deprecated. Please use models from schwab.models.generated.trading_models instead.
"""

# Re-export from generated models for backward compatibility
from .generated.trading_models import (
    Order,
    OrderType,
    Session as OrderSession,
    Duration as OrderDuration,
    Status as OrderStatus,
    Instruction as OrderInstruction,
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
)

# Deprecated - will be removed in future versions
__all__ = [
    "Order", "OrderType", "OrderSession", "OrderDuration", "OrderStatus",
    "OrderInstruction", "RequestedDestination", "TaxLotMethod", "SpecialInstruction",
    "ComplexOrderStrategyType", "OrderStrategyType", "OrderLeg", "OrderLegType",
    "PositionEffect", "QuantityType", "DividendCapitalGains", "StopPriceLinkBasis",
    "StopPriceLinkType", "StopType"
]