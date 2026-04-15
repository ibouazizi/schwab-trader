"""
Legacy quote models for backward compatibility.

This file is deprecated. Please use models from schwab.models.generated.market_data_models instead.
"""

# Re-export from generated models for backward compatibility
from .generated.market_data_models import (
    QuoteResponse,
    EquityResponse as QuoteData,
    QuoteEquity as Quote,
    AssetMainType,
)

# Create compatibility aliases for old model structure
class Reference:
    """Deprecated - use Quote fields directly"""
    pass

class Regular:
    """Deprecated - use Quote fields directly"""
    pass

class Fundamental:
    """Deprecated - use Quote fields directly"""
    pass

class QuoteType:
    """Deprecated - use AssetMainType instead"""
    pass

# Create SecurityStatus for compatibility
class SecurityStatus:
    """Deprecated - security status is included in Quote fields"""
    pass

# Deprecated - will be removed in future versions
__all__ = [
    "QuoteResponse", "QuoteData", "Quote", "Reference", "Regular", 
    "Fundamental", "AssetMainType", "QuoteType", "SecurityStatus"
]