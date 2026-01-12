"""
Paper Trading Account Management for Schwab Trader.

This module provides utilities for identifying and managing Schwab paper trading accounts.
"""

import logging
from typing import List, Optional, Dict, Any

from ..models.generated.trading_models import AccountNumberHash as AccountNumber
from pydantic import BaseModel
from typing import List

# For backward compatibility
class AccountNumbers(BaseModel):
    """List of account numbers."""
    accounts: List[AccountNumber]

logger = logging.getLogger(__name__)

class PaperAccountManager:
    """
    Utilities for managing Schwab paper trading accounts.
    
    This class provides methods to identify paper trading accounts, switch between
    paper and live trading modes, and manage paper account operations.
    
    Attributes:
        client: An authenticated SchwabClient or AsyncSchwabClient instance
    """
    
    # Paper account patterns may vary by broker - these are examples
    # that would need to be verified with Schwab's actual implementation
    PAPER_ACCOUNT_PREFIXES = ['PT', 'PAPER', 'SIM']
    PAPER_ACCOUNT_SUFFIXES = ['-PAPER', '-SIM', '-PT']
    
    def __init__(self, client):
        """
        Initialize the paper account manager.
        
        Args:
            client: An authenticated SchwabClient or AsyncSchwabClient instance
        """
        self.client = client
        
    def get_paper_accounts(self) -> List[AccountNumber]:
        """
        Identify and return paper trading accounts.
        
        Returns:
            List of paper trading account objects
        """
        all_accounts = self.client.get_account_numbers()
        paper_accounts = []

        if all_accounts and all_accounts.accounts:
            for account in all_accounts.accounts:
                if self.is_paper_account(account):
                    paper_accounts.append(account)

        return paper_accounts

    def is_paper_account(self, account: AccountNumber) -> bool:
        """
        Check if an account is a paper trading account.
        
        Paper accounts are identified based on account number patterns
        or specific flags in the account data provided by Schwab.
        
        Args:
            account: The account to check
            
        Returns:
            True if this is a paper trading account, False otherwise
        """
        # Check for paper account prefixes
        for prefix in self.PAPER_ACCOUNT_PREFIXES:
            if account.account_number.startswith(prefix):
                return True
                
        # Check for paper account suffixes
        for suffix in self.PAPER_ACCOUNT_SUFFIXES:
            if account.account_number.endswith(suffix):
                return True
        
        # Additional checks that might be specific to Schwab's implementation
        # would go here. For example, checking account metadata or flags
        # that indicate paper trading status.
        
        return False
    
    async def get_paper_accounts_async(self) -> List[AccountNumber]:
        """
        Identify and return paper trading accounts asynchronously.
        
        Returns:
            List of paper trading account objects
        """
        all_accounts = await self.client.get_account_numbers()
        paper_accounts = []

        if all_accounts and all_accounts.accounts:
            for account in all_accounts.accounts:
                if self.is_paper_account(account):
                    paper_accounts.append(account)

        return paper_accounts

    def get_paper_account_balances(self, include_positions: bool = False) -> Dict[str, Any]:
        """
        Get balances for all paper trading accounts.
        
        Args:
            include_positions: Whether to include position information
            
        Returns:
            Dictionary mapping account numbers to account data
        """
        paper_accounts = self.get_paper_accounts()
        account_data = {}
        
        for account in paper_accounts:
            try:
                account_info = self.client.get_account(
                    account_number=account.hash_value, 
                    include_positions=include_positions
                )
                account_data[account.account_number] = account_info
            except Exception as e:
                logger.error(f"Error getting paper account {account.account_number}: {str(e)}")
        
        return account_data
    
    async def get_paper_account_balances_async(self, include_positions: bool = False) -> Dict[str, Any]:
        """
        Get balances for all paper trading accounts asynchronously.
        
        Args:
            include_positions: Whether to include position information
            
        Returns:
            Dictionary mapping account numbers to account data
        """
        paper_accounts = await self.get_paper_accounts_async()
        account_data = {}
        
        for account in paper_accounts:
            try:
                account_info = await self.client.get_account(
                    account_number=account.hash_value, 
                    include_positions=include_positions
                )
                account_data[account.account_number] = account_info
            except Exception as e:
                logger.error(f"Error getting paper account {account.account_number}: {str(e)}")
        
        return account_data
    
    def reset_paper_account(self, account_number: str) -> bool:
        """
        Reset a paper trading account to its initial state.
        
        Note: This feature depends on whether Schwab's API supports
        resetting paper trading accounts. If not, this will raise
        an exception.
        
        Args:
            account_number: The encrypted account number
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            NotImplementedError: If Schwab's API doesn't support this operation
        """
        # This would need to be implemented based on Schwab's actual API capabilities
        # for paper trading accounts. If they don't offer this functionality,
        # we would need to throw an appropriate exception.
        
        raise NotImplementedError("Resetting paper accounts is not yet supported")
    
    async def reset_paper_account_async(self, account_number: str) -> bool:
        """
        Reset a paper trading account to its initial state asynchronously.
        
        Note: This feature depends on whether Schwab's API supports
        resetting paper trading accounts. If not, this will raise
        an exception.
        
        Args:
            account_number: The encrypted account number
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            NotImplementedError: If Schwab's API doesn't support this operation
        """
        # This would need to be implemented based on Schwab's actual API capabilities
        # for paper trading accounts. If they don't offer this functionality,
        # we would need to throw an appropriate exception.
        
        raise NotImplementedError("Resetting paper accounts is not yet supported")