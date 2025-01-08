#!/usr/bin/env python3
"""
Schwab Account Overview Script
This script provides a comprehensive overview of your Schwab account including:
- Account balances and cash positions
- Current equity positions
- Open orders
- Recent order history
- Account performance metrics

Uses direct API key authentication.
"""

import os
import asyncio
import aiohttp
import base64
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List
from tabulate import tabulate
from schwab import AsyncSchwabClient
from schwab.models.orders import Order, OrderStatus, OrderType, OrderInstruction

# API information - Direct API keys
API_KEY = 'YOUR_API_KEY'
API_SECRET = 'YOUR_API_SECRET'

# API endpoints
TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"

class AccountOverview:
    def __init__(self):
        """Initialize the overview class."""
        self.client = None
        self.access_token = None
        self.token_expires_at = 0
        
    def get_basic_auth_header(self) -> str:
        """Create Basic Auth header from API credentials."""
        credentials = f"{API_KEY}:{API_SECRET}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def get_access_token(self) -> dict:
        """Get access token using client credentials grant."""
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': self.get_basic_auth_header(),
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'client_credentials'
            }
            
            async with session.post(TOKEN_URL, headers=headers, data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to get access token: {error_text}")
                
                return await response.json()

    async def ensure_valid_token(self) -> str:
        """Ensure we have a valid access token."""
        current_time = time.time()
        
        if not self.access_token or current_time >= self.token_expires_at:
            # Get new token
            token_data = await self.get_access_token()
            
            # Update token and expiration
            self.access_token = token_data['access_token']
            expires_in = int(token_data.get('expires_in', 3600))  # Default 1 hour
            self.token_expires_at = time.time() + expires_in - 60  # 1-minute buffer
            
        return self.access_token

    async def setup(self):
        """Initialize the client with valid token."""
        token = await self.ensure_valid_token()
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
            
            # Calculate total equity value
            total_equity = sum(
                position.market_value
                for position in account.positions
                if position.asset_type == "EQUITY"
            )
            
            return {
                "account_id": account.account_id,
                "account_type": account.account_type,
                "cash_balance": account.cash_balance,
                "total_equity": total_equity,
                "total_value": account.total_value,
                "buying_power": account.buying_power,
                "positions": account.positions
            }

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
        print(f"Account ID: {summary['account_id']}")
        print(f"Account Type: {summary['account_type']}")
        print(f"Cash Balance: {self.format_currency(summary['cash_balance'])}")
        print(f"Total Equity Value: {self.format_currency(summary['total_equity'])}")
        print(f"Total Account Value: {self.format_currency(summary['total_value'])}")
        print(f"Buying Power: {self.format_currency(summary['buying_power'])}")

        # Print Equity Positions
        print("\n=== Equity Positions ===")
        positions_data = []
        for pos in summary['positions']:
            if pos.asset_type == "EQUITY":
                gain_loss = pos.market_value - pos.cost_basis
                gain_loss_pct = (gain_loss / pos.cost_basis * 100) if pos.cost_basis != 0 else Decimal('0')
                
                positions_data.append([
                    pos.symbol,
                    pos.quantity,
                    self.format_currency(pos.average_price),
                    self.format_currency(pos.current_price),
                    self.format_currency(pos.market_value),
                    self.format_currency(gain_loss),
                    self.format_percentage(gain_loss_pct)
                ])

        if positions_data:
            print(tabulate(
                positions_data,
                headers=['Symbol', 'Quantity', 'Avg Price', 'Current Price', 'Market Value', 'Gain/Loss', 'G/L %'],
                tablefmt='grid'
            ))
        else:
            print("No equity positions found.")

        # Print Open Orders
        print("\n=== Open Orders ===")
        orders_data = []
        for order in open_orders:
            orders_data.append([
                order.order_id,
                order.order_type,
                order.symbol,
                order.instruction,
                order.quantity,
                self.format_currency(order.price) if order.price else "MARKET",
                order.status,
                order.entered_time.strftime("%Y-%m-%d %H:%M:%S")
            ])

        if orders_data:
            print(tabulate(
                orders_data,
                headers=['Order ID', 'Type', 'Symbol', 'Side', 'Quantity', 'Price', 'Status', 'Entered Time'],
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
            accounts = await overview.client.get_account_numbers()
        
        # Print overview for each account
        for account in accounts:
            print(f"\nAccount Overview for: {account.account_id}")
            print("=" * 50)
            await overview.print_account_overview(account.encrypted_account_number)

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")