"""
Paper Trading Indicators for Schwab Trader.

This module provides visual indicators and safeguards to clearly
distinguish between paper trading and live trading environments.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
import functools
import time

logger = logging.getLogger(__name__)

class PaperTradingIndicator:
    """
    Visual indicators and safeguards for paper trading mode.
    
    This class provides utilities to clearly mark when paper trading
    is active and provide safeguards against mixing paper and live trading.
    
    Attributes:
        enabled: Whether paper trading mode is enabled
    """
    
    # ANSI color codes for terminal output
    PAPER_COLOR = "\033[36m"  # Cyan
    LIVE_COLOR = "\033[91m"   # Light red
    RESET_COLOR = "\033[0m"   # Reset to default
    
    def __init__(self, enabled: bool = False):
        """
        Initialize the paper trading indicator.
        
        Args:
            enabled: Whether paper trading mode is enabled
        """
        self.enabled = enabled
        self.start_time = time.time()
        self.warning_interval = 600  # 10 minutes
        self.last_warning = 0
    
    def enable(self):
        """Enable paper trading mode."""
        self.enabled = True
        logger.info(f"{self.PAPER_COLOR}PAPER TRADING MODE ENABLED{self.RESET_COLOR}")
        self._print_warning()
    
    def disable(self):
        """Disable paper trading mode."""
        self.enabled = False
        logger.info(f"{self.LIVE_COLOR}PAPER TRADING MODE DISABLED - LIVE TRADING{self.RESET_COLOR}")
    
    def status(self) -> str:
        """
        Get the current paper trading status.
        
        Returns:
            A string indicating the current mode
        """
        if self.enabled:
            return f"{self.PAPER_COLOR}PAPER TRADING MODE{self.RESET_COLOR}"
        else:
            return f"{self.LIVE_COLOR}LIVE TRADING MODE{self.RESET_COLOR}"
    
    def _print_warning(self):
        """Print a warning about paper trading mode."""
        current_time = time.time()
        
        # Only print warning if enough time has passed since last warning
        if current_time - self.last_warning >= self.warning_interval:
            self.last_warning = current_time
            
            warning = f"""
{self.PAPER_COLOR}
============================================================
                    PAPER TRADING MODE
          All trades will be simulated, not real
============================================================
{self.RESET_COLOR}
"""
            logger.warning(warning)
    
    def validate_account_type(self, account_number: str, is_paper_account: bool):
        """
        Validate account type against current mode.
        
        Args:
            account_number: The account number
            is_paper_account: Whether the account is a paper account
            
        Raises:
            ValueError: If there's a mismatch between account type and trading mode
        """
        if self.enabled and not is_paper_account:
            raise ValueError(
                f"{self.PAPER_COLOR}PAPER TRADING MODE is enabled but attempting "
                f"to use live account {account_number}.{self.RESET_COLOR}"
            )
            
        if not self.enabled and is_paper_account:
            logger.warning(
                f"{self.LIVE_COLOR}LIVE TRADING MODE is enabled but using "
                f"paper account {account_number}.{self.RESET_COLOR}"
            )
    
    def decorate_message(self, message: str) -> str:
        """
        Add paper trading indicator to a message.
        
        Args:
            message: The original message
            
        Returns:
            Decorated message
        """
        if self.enabled:
            prefix = f"{self.PAPER_COLOR}[PAPER]{self.RESET_COLOR} "
            return prefix + message
        return message


def paper_trading_check(func: Callable) -> Callable:
    """
    Decorator to add paper trading warnings to methods.
    
    This decorator adds warnings and validations to methods
    that interact with trading functionality.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Check if this is a client instance with paper trading indicator
        if hasattr(self, '_paper_trading_indicator'):
            indicator = self._paper_trading_indicator
            
            # Print periodic warning if in paper trading mode
            if indicator.enabled:
                indicator._print_warning()
            
            # Check account type from kwargs or positional args
            account_number = None
            if 'account_number' in kwargs:
                account_number = kwargs['account_number']
            elif len(args) >= 1:
                account_number = args[0]
            if account_number is not None and hasattr(self, 'is_paper_account'):
                is_paper = self.is_paper_account(account_number)
                indicator.validate_account_type(account_number, is_paper)
                
        return func(self, *args, **kwargs)
    
    return wrapper