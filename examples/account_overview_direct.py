#!/usr/bin/env python3
"""
Schwab Account Overview Script
This script provides a comprehensive overview of your Schwab account including:
- Account balances and cash positions
- Current equity positions
- Open orders
- Recent order history
- Account performance metrics

Uses direct API key authentication with credentials from unified database.
"""

import os
import sys
import asyncio
import aiohttp
import base64
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from tabulate import tabulate
from schwab import AsyncSchwabClient
from schwab.models.orders import Order, OrderStatus, OrderType, OrderInstruction

# Add parent directory to path if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from credential_manager import CredentialManager

# Initialize credential manager
cred_manager = CredentialManager()

# API endpoints
TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"

class AccountOverview:
    def __init__(self):
        """Initialize the overview class."""
        self.client = None
        self.access_token = None
        self.token_expires_at = 0
        self.api_key = None
        self.api_secret = None
        
        # Load credentials from database
        self._load_credentials()
        
    def _load_credentials(self):
        """Load API credentials from the unified database."""
        creds = cred_manager.get_credentials("trading")
        if not creds:
            print("ERROR: No credentials found in database.")
            print("Please run setup_credentials.py first to configure your API credentials.")
            sys.exit(1)
        
        self.api_key = creds.get('client_id')
        self.api_secret = creds.get('client_secret')
        
        if not self.api_key or not self.api_secret:
            print("ERROR: Invalid credentials in database.")
            print("Please run setup_credentials.py to reconfigure.")
            sys.exit(1)
        
    def get_basic_auth_header(self) -> str:
        """Create Basic Auth header from API credentials."""
        credentials = f"{self.api_key}:{self.api_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def get_access_token(self) -> dict:
        """Get access token from stored credentials or refresh if needed."""
        # First check if we have valid stored tokens
        tokens = cred_manager.get_tokens("trading")
        if tokens and tokens['is_valid']:
            return {
                'access_token': tokens['access_token'],
                'expires_in': tokens['expires_in']
            }
        
        # If we have a refresh token, try to refresh
        if tokens and tokens['refresh_token']:
            print("Access token expired, attempting to refresh...")
            return await self.refresh_access_token(tokens['refresh_token'])
        
        # No valid tokens available
        raise Exception("No valid access token available. Please run setup_oauth.py first.")
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh the access token using refresh token."""
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': self.get_basic_auth_header(),
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }
            
            async with session.post(TOKEN_URL, headers=headers, data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to refresh access token: {error_text}")
                
                token_data = await response.json()
                
                # Save the new tokens
                cred_manager.save_tokens(
                    access_token=token_data['access_token'],
                    refresh_token=token_data.get('refresh_token', refresh_token),
                    expires_in=token_data.get('expires_in', 1800)
                )
                
                return token_data

    async def ensure_valid_token(self) -> str:
        """Ensure we have a valid access token."""
        token_data = await self.get_access_token()
        self.access_token = token_data['access_token']
        self.token_expires_at = time.time() + token_data.get('expires_in', 1800) - 60
        return self.access_token

    async def setup(self):
        """Initialize the client with valid token."""
        # Check if we have any stored credentials first
        creds = cred_manager.get_credentials("trading")
        if not creds:
            print("\nERROR: No credentials found in database.")
            print("Please run the following commands in order:")
            print("1. python examples/setup_credentials.py  (to save your API credentials)")
            print("2. python examples/setup_oauth.py  (to complete OAuth and get tokens)")
            raise Exception("Missing credentials")
        
        # Get valid token
        try:
            token = await self.ensure_valid_token()
        except Exception as e:
            print(f"\nERROR: {str(e)}")
            print("\nTo fix this, run:")
            print("  python examples/setup_oauth.py")
            print("\nThis will guide you through the OAuth process to get valid tokens.")
            raise
        
        # Create client with access token
        self.client = AsyncSchwabClient(api_key=token)
        
    def format_currency(self, amount: Decimal) -> str:
        """Format decimal amounts as currency strings."""
        return f"${amount:,.2f}"
    
    def format_percentage(self, value: Decimal) -> str:
        """Format decimal values as percentage strings."""
        return f"{value:.2f}%"

    async def get_account_summary(self, account_number: str) -> Dict:
        """Get a summary of account balances and positions."""
        async with self.client:
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
                        summary["cash_balance"] = getattr(balances, 'available_funds', Decimal('0'))
                        summary["buying_power"] = getattr(balances, 'buying_power', Decimal('0'))
                    else:  # CASH account
                        summary["cash_balance"] = getattr(balances, 'cash_available_for_trading', Decimal('0'))
                        summary["buying_power"] = summary["cash_balance"]
                
                # Get initial balances for total value
                if hasattr(sec_account, 'initial_balances') and sec_account.initial_balances:
                    summary["total_value"] = getattr(sec_account.initial_balances, 'account_value', Decimal('0'))
                
                # Get positions
                if hasattr(sec_account, 'positions') and sec_account.positions:
                    summary["positions"] = sec_account.positions
                    
                    # Calculate total equity value
                    total_equity = Decimal('0')
                    for position in sec_account.positions:
                        if hasattr(position, 'market_value'):
                            total_equity += getattr(position, 'market_value', Decimal('0'))
                    summary["total_equity"] = total_equity
            
            return summary

    async def get_open_orders(self, account_number: str) -> List[Order]:
        """Get all open orders for the account."""
        async with self.client:
            return await self.client.get_orders(
                account_number=account_number,
                from_entered_time=datetime.now() - timedelta(days=30),
                to_entered_time=datetime.now(),
                status="WORKING"
            )

    async def print_account_overview(self, account_number: str):
        """Print a comprehensive account overview."""
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
                
                position_data.append([
                    symbol,
                    getattr(position, 'long_quantity', 0),
                    self.format_currency(getattr(position, 'average_price', 0)),
                    self.format_currency(getattr(position, 'market_value', 0)),
                    self.format_currency(getattr(position, 'unrealized_gain_loss', 0)),
                    self.format_percentage(getattr(position, 'unrealized_gain_loss_percentage', 0))
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
                instruction = "Unknown"
                if hasattr(order, 'order_leg_collection') and order.order_leg_collection:
                    first_leg = order.order_leg_collection[0]
                    if hasattr(first_leg, 'instrument') and hasattr(first_leg.instrument, 'symbol'):
                        symbol = first_leg.instrument.symbol
                    if hasattr(first_leg, 'instruction'):
                        instruction = first_leg.instruction
                
                order_data.append([
                    getattr(order, 'order_id', 'N/A'),
                    symbol,
                    getattr(order, 'order_type', 'Unknown'),
                    instruction,
                    getattr(order, 'quantity', 0),
                    self.format_currency(getattr(order, 'price', 0)) if getattr(order, 'price', None) else 'MARKET',
                    getattr(order, 'status', 'Unknown')
                ])
            
            print(tabulate(
                order_data,
                headers=['Order ID', 'Symbol', 'Type', 'Side', 'Quantity', 'Price', 'Status'],
                tablefmt='grid'
            ))
        else:
            print("No open orders found.")

        # Print Account Allocation
        print("\n=== Account Allocation ===")
        total_value = summary['total_value']
        if total_value > 0:
            cash_allocation = (summary['cash_balance'] / total_value) * 100
            equity_allocation = (summary['total_equity'] / total_value) * 100
            
            allocation_data = [
                ['Cash', self.format_currency(summary['cash_balance']), self.format_percentage(cash_allocation)],
                ['Equity', self.format_currency(summary['total_equity']), self.format_percentage(equity_allocation)]
            ]
            
            print(tabulate(
                allocation_data,
                headers=['Asset Class', 'Value', 'Allocation'],
                tablefmt='grid'
            ))

async def main():
    try:
        # Initialize the overview class
        overview = AccountOverview()
        
        # Setup client with valid token
        await overview.setup()
        
        # Get all account numbers
        print("\nFetching account numbers...")
        async with overview.client:
            account_numbers = await overview.client.get_account_numbers()
            
            if not account_numbers.accounts:
                print("No accounts found.")
                return
                
            print(f"\nFound {len(account_numbers.accounts)} account(s)")
            
            # Print overview for each account
            for account in account_numbers.accounts:
                print(f"\n{'='*60}")
                print(f"Account: {account.account_number}")
                print(f"{'='*60}")
                await overview.print_account_overview(account.hash_value)

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")