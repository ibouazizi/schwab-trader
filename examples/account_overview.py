#!/usr/bin/env python3
"""
Schwab Account Overview Script
This script provides a comprehensive overview of your Schwab account including:
- Account balances and cash positions
- Current equity positions
- Open orders
- Recent order history
- Account performance metrics
"""

import os
import webbrowser
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List
from tabulate import tabulate
from schwab import SchwabClient, SchwabAuth
from schwab.models.orders import Order, OrderStatus, OrderType, OrderInstruction


# API information - Replace with your API keys
SCHWAB_CLIENT_ID = 'YOUR_CLIENT_ID'
SCHWAB_CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
SCHWAB_REDIRECT_URI = 'YOUR_REDIRECT_URI'

def get_authorization_code(auth: 'SchwabAuth') -> str:
    """
    Get authorization code through OAuth flow.
    Opens browser for user authorization and waits for callback URL to be pasted.
    """
    # Get authorization URL
    auth_url = auth.get_authorization_url()
    
    # Open browser for user to authorize
    print("\nOpening browser for authorization...")
    webbrowser.open(auth_url)
    
    # Wait for user to complete authorization
    print("\nAfter authorizing, please paste the full callback URL here:")
    callback_url = input().strip()
    
    # Parse the authorization code from callback URL
    parsed = urlparse(callback_url)
    params = parse_qs(parsed.query)
    
    if 'code' not in params:
        raise ValueError("No authorization code found in callback URL")
    
    return params['code'][0]

class AccountOverview:
    def __init__(self, client: SchwabClient):
        """Initialize with authenticated client."""
        self.client = client
        
    def format_currency(self, amount: Decimal) -> str:
        """Format decimal amounts as currency strings."""
        return f"${amount:,.2f}"
    
    def format_percentage(self, value: Decimal) -> str:
        """Format decimal values as percentage strings."""
        return f"{value:.2f}%"

    def get_account_summary(self, account_number: str) -> Dict:
        """Get a summary of account balances and positions."""
        account = self.client.get_account(account_number, include_positions=True)
        
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

    def get_open_orders(self, account_number: str) -> List[Order]:
        """Get all open orders for the account."""
        return self.client.get_orders(
            account_number=account_number,
            from_entered_time=datetime.now() - timedelta(days=30),
            to_entered_time=datetime.now(),
            status="WORKING"
        )

    def print_account_overview(self, account_number: str):
        """Print a comprehensive account overview."""
        summary = self.get_account_summary(account_number)
        open_orders = self.get_open_orders(account_number)

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

def main():
    # Get OAuth credentials from environment
    client_id = SCHWAB_CLIENT_ID
    client_secret = SCHWAB_CLIENT_SECRET
    redirect_uri = SCHWAB_REDIRECT_URI    

    try:
        # Initialize the client with OAuth credentials
        client = SchwabClient(            
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri
        )
        
        # Get authorization code through OAuth flow
        auth_code = get_authorization_code(client.auth)
        
        # Exchange authorization code for tokens
        print("\nExchanging authorization code for tokens...")
        token_data = client.auth.exchange_code_for_tokens(auth_code)
        print("Successfully authenticated!")
        
        # Initialize the overview class
        overview = AccountOverview(client)
        
        # Get all account numbers
        print("\nFetching account numbers...")
        accounts = client.get_account_numbers()
        
        # Print overview for each account
        for account in accounts:
            print(f"\nAccount Overview for: {account.account_id}")
            print("=" * 50)
            overview.print_account_overview(account.encrypted_account_number)

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()