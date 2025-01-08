"""Schwab API Python Library.

This library provides a clean and Pythonic interface to Charles Schwab's Trading API.
"""

from .client import SchwabClient
from .auth import SchwabAuth
from .async_client import AsyncSchwabClient

__version__ = "0.1.0"
__all__ = ["SchwabClient", "AsyncSchwabClient", "SchwabAuth"]
