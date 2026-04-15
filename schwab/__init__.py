"""Schwab API Python Library.

This library provides a clean and Pythonic interface to Charles Schwab's Trading API.
"""

from .client import SchwabClient
from .auth import SchwabAuth
from .dual_auth import DualSchwabAuth
from .async_client import AsyncSchwabClient
from .streaming import (
    StreamerClient, StreamerService, QOSLevel,
    StreamingQuote, StreamingOptionQuote, StreamingOrderBook,
    StreamingNews, StreamingChartBar, StreamingAccountActivity,
    LevelOneEquityFields, LevelOneOptionFields, LevelTwoFields,
    NewsFields, ChartEquityFields, AcctActivityFields
)

__version__ = "0.1.0"
__all__ = [
    "SchwabClient", 
    "AsyncSchwabClient", 
    "SchwabAuth",
    "DualSchwabAuth",
    "StreamerClient",
    "StreamerService",
    "QOSLevel",
    "StreamingQuote",
    "StreamingOptionQuote",
    "StreamingOrderBook",
    "StreamingNews",
    "StreamingChartBar",
    "StreamingAccountActivity",
    "LevelOneEquityFields",
    "LevelOneOptionFields",
    "LevelTwoFields",
    "NewsFields",
    "ChartEquityFields",
    "AcctActivityFields",
]
