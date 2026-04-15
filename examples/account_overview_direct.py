#!/usr/bin/env python3
"""
Schwab Account Overview Script - Fixed Version
This script provides a comprehensive overview of your Schwab account using
stored OAuth tokens from the unified credential system.
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from tabulate import tabulate

# Add parent directory to path for schwab imports
# Add examples directory to path for credential_manager imports
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_script_dir))
sys.path.insert(0, _script_dir)

from schwab import AsyncSchwabClient, SchwabAuth
from schwab.models.generated.trading_models import Account, Position, Status as OrderStatus
from credential_manager import CredentialManager

# Initialize credential manager
cred_manager = CredentialManager()

class AccountOverview:
    def __init__(self):
        """Initialize the overview class."""
        self.client = None
        self.auth = None
        
    async def setup(self):
        """Initialize the client with stored credentials and tokens."""
        # Get auth parameters from credential manager
        auth_params = cred_manager.get_auth_params("trading")
        if not auth_params:
            print("ERROR: No credentials found in database.")
            print("Please run setup_credentials.py first to configure your API credentials.")
            print("Then run account_overview.py to complete the OAuth flow.")
            sys.exit(1)
        
        # Check if we have valid tokens
        tokens = cred_manager.get_tokens("trading")
        if not tokens or not tokens['is_valid']:
            print("ERROR: No valid access token found.")
            print("Please run account_overview.py first to complete the OAuth flow.")
            print("This will save tokens that can be reused by this script.")
            sys.exit(1)
        
        # Initialize auth with stored credentials
        self.auth = SchwabAuth(
            client_id=auth_params['client_id'],
            client_secret=auth_params['client_secret'],
            redirect_uri=auth_params.get('redirect_uri', 'https://localhost:8443/callback')
        )
        
        # Set the stored tokens
        self.auth.access_token = tokens['access_token']
        self.auth.refresh_token = tokens['refresh_token']
        self.auth.token_expiry = tokens['expiry']
        
        # Ensure token is valid
        self.auth.ensure_valid_token()
        
        # Initialize the async client with the access token
        self.client = AsyncSchwabClient(api_key=self.auth.access_token)
        
        print("✓ Successfully initialized client with stored credentials")
        
    def format_currency(self, amount: Decimal) -> str:
        """Format decimal amounts as currency strings."""
        if amount is None:
            return "$0.00"
        return f"${amount:,.2f}"
    
    def format_percentage(self, value: Decimal) -> str:
        """Format decimal values as percentage strings."""
        if value is None:
            return "0.00%"
        return f"{value:.2f}%"

    async def get_account_summary(self, account_number: str) -> Dict:
        """Get a summary of account balances and positions."""
        account = await self.client.get_account(account_number, include_positions=True)
        
        # Extract basic info
        summary = {
            "account_number": account_number,
            "positions": []
        }
        
        # Handle the account data structure
        if hasattr(account, 'securities_account') and account.securities_account:
            sec_account = account.securities_account
            
            # Get account type
            summary["account_type"] = getattr(sec_account, 'type', 'Unknown')
            
            # Get balances based on account type
            if hasattr(sec_account, 'current_balances') and sec_account.current_balances:
                balances = sec_account.current_balances
                
                if summary["account_type"] == "MARGIN":
                    available_funds = getattr(balances, 'available_funds', None)
                    summary["cash_balance"] = Decimal(str(available_funds)) if available_funds is not None else Decimal('0')
                    buying_power = getattr(balances, 'buying_power', None)
                    summary["buying_power"] = Decimal(str(buying_power)) if buying_power is not None else Decimal('0')
                else:  # CASH account
                    cash_available = getattr(balances, 'cash_available_for_trading', None)
                    summary["cash_balance"] = Decimal(str(cash_available)) if cash_available is not None else Decimal('0')
                    summary["buying_power"] = summary["cash_balance"]
            
            # Get initial balances for total value
            if hasattr(sec_account, 'initial_balances') and sec_account.initial_balances:
                account_value = getattr(sec_account.initial_balances, 'account_value', None)
                summary["total_value"] = Decimal(str(account_value)) if account_value is not None else Decimal('0')
            
            # Get positions
            if hasattr(sec_account, 'positions') and sec_account.positions:
                summary["positions"] = sec_account.positions
                
                # Calculate total equity value
                total_equity = Decimal('0')
                for position in sec_account.positions:
                    if hasattr(position, 'market_value') and position.market_value is not None:
                        market_value = Decimal(str(position.market_value))
                        total_equity += market_value
                summary["total_equity"] = total_equity
        
        return summary

    async def get_open_orders(self, account_number: str) -> List:
        """Get all open orders for the account."""
        orders = await self.client.get_orders(
            account_number=account_number,
            from_entered_time=datetime.now() - timedelta(days=7),
            to_entered_time=datetime.now(),
            status="WORKING"
        )
        return orders

    async def print_account_overview(self, account_number: str):
        """Print a comprehensive account overview."""
        try:
            summary = await self.get_account_summary(account_number)
            open_orders = await self.get_open_orders(account_number)

            # Print Account Information
            print("\n=== Account Information ===")
            print(f"Account: {account_number}")
            print(f"Type: {summary.get('account_type', 'Unknown')}")
            print(f"Total Value: {self.format_currency(summary.get('total_value', 0))}")
            print(f"Cash Balance: {self.format_currency(summary.get('cash_balance', 0))}")
            print(f"Total Equity: {self.format_currency(summary.get('total_equity', 0))}")
            print(f"Buying Power: {self.format_currency(summary.get('buying_power', 0))}")

            # Print Positions
            if summary.get('positions'):
                print("\n=== Current Positions ===")
                position_data = []
                
                for position in summary['positions']:
                    symbol = "Unknown"
                    if hasattr(position, 'instrument') and hasattr(position.instrument, 'symbol'):
                        symbol = position.instrument.symbol
                    
                    # Get position values
                    quantity = Decimal(str(getattr(position, 'long_quantity', 0)))
                    avg_price = Decimal(str(getattr(position, 'average_price', 0)))
                    market_value = Decimal(str(getattr(position, 'market_value', 0)))
                    
                    # Calculate gain/loss
                    cost_basis = quantity * avg_price
                    gain_loss = market_value - cost_basis
                    gain_loss_pct = (gain_loss / cost_basis * 100) if cost_basis > 0 else Decimal('0')
                    
                    position_data.append([
                        symbol,
                        quantity,
                        self.format_currency(avg_price),
                        self.format_currency(market_value),
                        self.format_currency(gain_loss),
                        self.format_percentage(gain_loss_pct)
                    ])
                
                print(tabulate(
                    position_data,
                    headers=['Symbol', 'Quantity', 'Avg Price', 'Market Value', 'Gain/Loss', 'Gain/Loss %'],
                    tablefmt='grid'
                ))
            else:
                print("\n=== Current Positions ===")
                print("No positions found.")

            # Print Open Orders
            print("\n=== Open Orders ===")
            if open_orders:
                order_data = []
                for order in open_orders:
                    symbol = "Unknown"
                    if hasattr(order, 'order_leg_collection') and order.order_leg_collection:
                        first_leg = order.order_leg_collection[0]
                        if hasattr(first_leg, 'instrument') and hasattr(first_leg.instrument, 'symbol'):
                            symbol = first_leg.instrument.symbol
                    
                    order_data.append([
                        getattr(order, 'order_id', 'N/A'),
                        symbol,
                        getattr(order, 'order_type', 'Unknown'),
                        getattr(order, 'quantity', 0),
                        self.format_currency(getattr(order, 'price', 0)),
                        getattr(order, 'status', 'Unknown')
                    ])
                
                print(tabulate(
                    order_data,
                    headers=['Order ID', 'Symbol', 'Type', 'Quantity', 'Price', 'Status'],
                    tablefmt='grid'
                ))
            else:
                print("No open orders.")
                
        except Exception as e:
            print(f"\nError getting account details: {str(e)}")
            if "401" in str(e):
                print("\nAuthentication failed. This could mean:")
                print("1. Your access token has expired")
                print("2. Your credentials are incorrect")
                print("\nPlease run account_overview.py to refresh your authentication.")

async def main():
    try:
        # Initialize the overview class
        overview = AccountOverview()
        
        # Setup client with stored credentials
        await overview.setup()
        
        # Get all account numbers
        print("\nFetching account numbers...")
        async with overview.client:
            accounts = await overview.client.get_account_numbers()
            
            if not accounts.accounts:
                print("No accounts found.")
                return
                
            print(f"\nFound {len(accounts.accounts)} account(s)")
            
            # Print overview for each account
            for account in accounts.accounts:
                account_number = account.hash_value
                print(f"\n{'='*60}")
                print(f"Account: {account.account_number}")
                print(f"{'='*60}")
                await overview.print_account_overview(account_number)

    except Exception as e:
        print(f"\nError: {str(e)}")
        if "401" in str(e):
            print("\nAuthentication failed. Please ensure you have:")
            print("1. Run setup_credentials.py to save your API credentials")
            print("2. Run account_overview.py to complete OAuth authentication")
            print("3. Valid, non-expired access tokens")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")