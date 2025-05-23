"""
Paper Trading Client Extensions for Schwab Trader.

This module extends the SchwabClient and AsyncSchwabClient classes
with paper trading capabilities.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
import functools

from ..client import SchwabClient
from ..async_client import AsyncSchwabClient
from .account import PaperAccountManager
from .indicators import PaperTradingIndicator, paper_trading_check
from ..models.generated.trading_models import AccountNumberHash as AccountNumber

logger = logging.getLogger(__name__)

class PaperTradingClientMixin:
    """
    Mixin class to add paper trading capabilities to SchwabClient.
    
    This mixin adds methods and properties for working with paper trading
    accounts, including account identification, safety checks, and visual
    indicators.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the paper trading mixin."""
        # Initialize parent class
        super().__init__(*args, **kwargs)
        
        # Create paper trading components
        self._paper_trading_indicator = PaperTradingIndicator()
        self._paper_account_manager = PaperAccountManager(self)
        
    def enable_paper_trading(self):
        """Enable paper trading mode."""
        self._paper_trading_indicator.enable()
        
    def disable_paper_trading(self):
        """Disable paper trading mode."""
        self._paper_trading_indicator.disable()
        
    @property
    def is_paper_trading_enabled(self) -> bool:
        """Check if paper trading mode is enabled."""
        return self._paper_trading_indicator.enabled
    
    def paper_trading_status(self) -> str:
        """Get the current paper trading status."""
        return self._paper_trading_indicator.status()
    
    def get_paper_accounts(self):
        """Get all paper trading accounts."""
        return self._paper_account_manager.get_paper_accounts()
    
    def is_paper_account(self, account_number: str) -> bool:
        """
        Check if an account is a paper trading account.
        
        Args:
            account_number: The account number or hash value
            
        Returns:
            True if this is a paper trading account, False otherwise
        """
        # First, handle the case where we have a hash value instead of an account number
        # by finding the corresponding account number
        accounts = self.get_account_numbers()
        for account in accounts.accounts:
            if account.hash_value == account_number:
                return self._paper_account_manager.is_paper_account(account)
                
        # If we have the actual account number, create a temporary AccountNumber object
        
        temp_account = AccountNumber(account_number=account_number, hash_value="")
        return self._paper_account_manager.is_paper_account(temp_account)
    
    @paper_trading_check
    def place_order(self, account_number: str, order):
        """
        Place an order with paper trading safeguards.
        
        Args:
            account_number: The encrypted account number
            order: The order to place
            
        Returns:
            Result from the parent method
        """
        # The paper_trading_check decorator handles validation
        # Now proceed with the normal order placement
        return super().place_order(account_number, order)
    
    @paper_trading_check
    def replace_order(self, account_number: str, order_id: int, new_order):
        """
        Replace an order with paper trading safeguards.
        
        Args:
            account_number: The encrypted account number
            order_id: The ID of the order to replace
            new_order: The new order
            
        Returns:
            Result from the parent method
        """
        return super().replace_order(account_number, order_id, new_order)
    
    @paper_trading_check
    def cancel_order(self, account_number: str, order_id: int):
        """
        Cancel an order with paper trading safeguards.
        
        Args:
            account_number: The encrypted account number
            order_id: The ID of the order to cancel
            
        Returns:
            Result from the parent method
        """
        return super().cancel_order(account_number, order_id)
    

class PaperTradingClient(PaperTradingClientMixin, SchwabClient):
    """
    SchwabClient extended with paper trading capabilities.
    
    This class adds paper trading account identification, safety checks,
    and visual indicators to the standard SchwabClient.
    """
    
    def __init__(self, *args, paper_trading_enabled=False, **kwargs):
        """
        Initialize the paper trading client.
        
        Args:
            paper_trading_enabled: Whether to start in paper trading mode
            *args, **kwargs: Arguments to pass to SchwabClient
        """
        # Initialize SchwabClient and the PaperTradingClientMixin
        super().__init__(*args, **kwargs)
        
        # Set initial paper trading mode
        if paper_trading_enabled:
            self.enable_paper_trading()


class AsyncPaperTradingClientMixin:
    """
    Mixin class to add paper trading capabilities to AsyncSchwabClient.
    
    This mixin adds methods and properties for working with paper trading
    accounts, including account identification, safety checks, and visual
    indicators.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the paper trading mixin."""
        # Initialize parent class
        super().__init__(*args, **kwargs)
        
        # Create paper trading components
        self._paper_trading_indicator = PaperTradingIndicator()
        self._paper_account_manager = PaperAccountManager(self)
        
    def enable_paper_trading(self):
        """Enable paper trading mode."""
        self._paper_trading_indicator.enable()
        
    def disable_paper_trading(self):
        """Disable paper trading mode."""
        self._paper_trading_indicator.disable()
        
    @property
    def is_paper_trading_enabled(self) -> bool:
        """Check if paper trading mode is enabled."""
        return self._paper_trading_indicator.enabled
    
    def paper_trading_status(self) -> str:
        """Get the current paper trading status."""
        return self._paper_trading_indicator.status()
    
    async def get_paper_accounts(self):
        """Get all paper trading accounts asynchronously."""
        return await self._paper_account_manager.get_paper_accounts_async()
    
    async def is_paper_account(self, account_number: str) -> bool:
        """
        Check if an account is a paper trading account asynchronously.
        
        Args:
            account_number: The account number or hash value
            
        Returns:
            True if this is a paper trading account, False otherwise
        """
        # First, handle the case where we have a hash value instead of an account number
        # by finding the corresponding account number
        accounts = await self.get_account_numbers()
        for account in accounts.accounts:
            if account.hash_value == account_number:
                return self._paper_account_manager.is_paper_account(account)
                
        # If we have the actual account number, create a temporary AccountNumber object
        
        temp_account = AccountNumber(account_number=account_number, hash_value="")
        return self._paper_account_manager.is_paper_account(temp_account)
    
    @paper_trading_check
    async def place_order(self, account_number: str, order):
        """
        Place an order with paper trading safeguards.
        
        Args:
            account_number: The encrypted account number
            order: The order to place
            
        Returns:
            Result from the parent method
        """
        # The paper_trading_check decorator handles validation
        # Now proceed with the normal order placement
        return await super().place_order(account_number, order)
    
    @paper_trading_check
    async def replace_order(self, account_number: str, order_id: int, new_order):
        """
        Replace an order with paper trading safeguards.
        
        Args:
            account_number: The encrypted account number
            order_id: The ID of the order to replace
            new_order: The new order
            
        Returns:
            Result from the parent method
        """
        return await super().replace_order(account_number, order_id, new_order)
    
    @paper_trading_check
    async def cancel_order(self, account_number: str, order_id: int):
        """
        Cancel an order with paper trading safeguards.
        
        Args:
            account_number: The encrypted account number
            order_id: The ID of the order to cancel
            
        Returns:
            Result from the parent method
        """
        return await super().cancel_order(account_number, order_id)


class AsyncPaperTradingClient(AsyncPaperTradingClientMixin, AsyncSchwabClient):
    """
    AsyncSchwabClient extended with paper trading capabilities.
    
    This class adds paper trading account identification, safety checks,
    and visual indicators to the standard AsyncSchwabClient.
    """
    
    def __init__(self, api_key: str, paper_trading_enabled: bool = False):
        """
        Initialize the async paper trading client.

        Args:
            api_key: The API key to use for both trading and market data
            paper_trading_enabled: Whether to start in paper trading mode
        """
        # Initialize AsyncSchwabClient with the API key for both trading and market data
        # trading_client_id and client_secret use api_key, redirect_uri set to None
        # Initialize AsyncSchwabClient and AsyncPaperTradingClientMixin via MRO
        super().__init__(
            api_key,
            api_key,
            None,
            api_key,
            api_key
        )
        # Set initial paper trading mode
        if paper_trading_enabled:
            self.enable_paper_trading()