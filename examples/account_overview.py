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
import sys
import webbrowser
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List
from tabulate import tabulate

# Add parent directory to path for schwab imports
# Add examples directory to path for credential_manager imports
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_script_dir))
sys.path.insert(0, _script_dir)

from schwab import SchwabClient, SchwabAuth
from schwab.models.orders import Order, OrderStatus, OrderType, OrderInstruction
from credential_manager import CredentialManager

# Initialize credential manager
cred_manager = CredentialManager()

def get_authorization_code(auth: 'SchwabAuth') -> str:
    """
    Get authorization code through OAuth flow.
    Opens browser for user authorization and waits for callback URL to be pasted.
    """
    # Get authorization URL
    auth_url = auth.get_authorization_url()
    
    # Try to copy to clipboard
    try:
        import pyperclip
        pyperclip.copy(auth_url)
        print(f"\n✓ Authorization URL copied to clipboard!")
        print("You can paste it in your browser if the automatic opening doesn't work.\n")
    except:
        # pyperclip not installed or clipboard not available
        print(f"\nAuthorization URL: {auth_url}\n")
    
    # Open browser for user to authorize
    print("Opening browser for authorization...")
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
        
        # Access the securities account
        sec_acct = account.securities_account
        
        # Get positions list
        positions_list = []
        if hasattr(sec_acct, 'positions') and sec_acct.positions:
            positions_list = sec_acct.positions
        
        # Calculate total equity value
        total_equity = Decimal("0")
        for position in positions_list:
            if hasattr(position, 'instrument') and hasattr(position.instrument, 'asset_type'):
                if position.instrument.asset_type == "EQUITY":
                    if hasattr(position, 'market_value') and position.market_value:
                        total_equity += Decimal(str(position.market_value))
        
        # Get account info from securities account
        account_id = sec_acct.account_number if hasattr(sec_acct, 'account_number') else "Unknown"
        account_type = sec_acct.type if hasattr(sec_acct, 'type') else "Unknown"
        
        # Get balance info
        cash_balance = Decimal("0")
        total_value = Decimal("0")
        buying_power_value = Decimal("0")
        
        if hasattr(sec_acct, 'current_balances') and sec_acct.current_balances:
            balances = sec_acct.current_balances
            if hasattr(balances, 'available_funds'):
                cash_balance = Decimal(str(balances.available_funds))
            if hasattr(balances, 'liquidation_value'):
                total_value = Decimal(str(balances.liquidation_value))
            
            # For margin accounts
            if hasattr(balances, 'buying_power') and balances.buying_power:
                buying_power_value = Decimal(str(balances.buying_power))
            # For cash accounts, use cash_available_for_trading
            elif hasattr(balances, 'cash_available_for_trading') and balances.cash_available_for_trading:
                buying_power_value = Decimal(str(balances.cash_available_for_trading))
        
        return {
            "account_id": account_id,
            "account_type": account_type,
            "cash_balance": cash_balance,
            "total_equity": total_equity,
            "total_value": total_value,
            "buying_power": buying_power_value,
            "positions": positions_list
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
            if hasattr(pos, 'instrument') and hasattr(pos.instrument, 'asset_type'):
                if pos.instrument.asset_type == "EQUITY":
                    # Get symbol
                    symbol = pos.instrument.symbol if hasattr(pos.instrument, 'symbol') else "Unknown"
                    
                    # Get position values
                    quantity = Decimal(str(pos.long_quantity)) if hasattr(pos, 'long_quantity') and pos.long_quantity else Decimal('0')
                    market_value = Decimal(str(pos.market_value)) if hasattr(pos, 'market_value') and pos.market_value else Decimal('0')
                    
                    # Get average cost
                    average_price = Decimal('0')
                    if hasattr(pos, 'average_price') and pos.average_price:
                        average_price = Decimal(str(pos.average_price))
                    
                    # Calculate current price from market value
                    current_price = market_value / quantity if quantity > 0 else Decimal('0')
                    
                    # Calculate gain/loss
                    cost_basis = average_price * quantity
                    gain_loss = market_value - cost_basis
                    gain_loss_pct = (gain_loss / cost_basis * 100) if cost_basis != 0 else Decimal('0')
                    
                    positions_data.append([
                        symbol,
                        quantity,
                        self.format_currency(average_price),
                        self.format_currency(current_price),
                        self.format_currency(market_value),
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
            # Get order details
            order_id = order.order_id if hasattr(order, 'order_id') else "Unknown"
            order_type = order.order_type if hasattr(order, 'order_type') else "Unknown"
            status = order.status if hasattr(order, 'status') else "Unknown"
            quantity = order.quantity if hasattr(order, 'quantity') else 0
            price = order.price if hasattr(order, 'price') and order.price else None
            entered_time = order.entered_time if hasattr(order, 'entered_time') else None
            
            # Get symbol and instruction from order legs
            symbol = "Unknown"
            instruction = "Unknown"
            if hasattr(order, 'order_leg_collection') and order.order_leg_collection:
                first_leg = order.order_leg_collection[0]
                if hasattr(first_leg, 'instrument') and hasattr(first_leg.instrument, 'symbol'):
                    symbol = first_leg.instrument.symbol
                if hasattr(first_leg, 'instruction'):
                    instruction = first_leg.instruction
            
            orders_data.append([
                order_id,
                order_type,
                symbol,
                instruction,
                quantity,
                self.format_currency(Decimal(str(price))) if price else "MARKET",
                status,
                entered_time.strftime("%Y-%m-%d %H:%M:%S") if entered_time else "Unknown"
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
    # Check for stored credentials or prompt for new ones
    auth_params = cred_manager.get_auth_params()
    
    if not auth_params:
        print("\nNo stored credentials found. Please enter your Schwab API credentials.")
        print("You can obtain these from: https://developer.schwab.com\n")
        
        client_id = input("Client ID: ").strip()
        client_secret = input("Client Secret: ").strip()
        redirect_uri = input("Redirect URI (default: https://localhost:8443/callback): ").strip()
        
        if not redirect_uri:
            redirect_uri = "https://localhost:8443/callback"
        
        # Save credentials
        cred_manager.save_credentials(client_id, client_secret, redirect_uri)
        auth_params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri
        }
    else:
        print("\nUsing stored credentials...")

    try:
        # Initialize the client with OAuth credentials
        client = SchwabClient(            
            client_id=auth_params['client_id'],
            client_secret=auth_params['client_secret'],
            redirect_uri=auth_params.get('redirect_uri', 'https://localhost:8443/callback')
        )
        
        # Check for valid tokens
        tokens = cred_manager.get_tokens()
        if tokens and tokens.get('refresh_token'):
            # We have tokens, set them even if expired
            client.auth.access_token = tokens['access_token']
            client.auth.refresh_token = tokens['refresh_token']
            if tokens.get('expiry'):
                client.auth.token_expiry = tokens['expiry']
                
            # Try to refresh if expired
            if not tokens['is_valid'] and tokens.get('refresh_token'):
                print("Access token expired, refreshing...")
                try:
                    # Refresh the token
                    token_data = client.auth.refresh_access_token()
                    print("Successfully refreshed access token!")
                    
                    # Save new tokens
                    cred_manager.save_tokens(
                        client.auth.access_token,
                        client.auth.refresh_token,
                        expires_in=1800  # 30 minutes
                    )
                except Exception as e:
                    print(f"Failed to refresh token: {e}")
                    # Fall through to get new authorization
                    tokens = None
            else:
                print("Using stored access token...")
                
            # Update session headers with the authorization token
            if tokens:
                client.session.headers.update(client.auth.authorization_header)
                print("Successfully authenticated using stored tokens!")
        
        # If no valid tokens, get new authorization
        if not tokens or not client.auth.access_token:
            # Get new authorization
            auth_code = get_authorization_code(client.auth)
            
            # Exchange authorization code for tokens
            print("\nExchanging authorization code for tokens...")
            token_data = client.auth.exchange_code_for_tokens(auth_code)
            print("Successfully authenticated!")
            
            # Save tokens
            if hasattr(client.auth, 'access_token') and client.auth.access_token:
                cred_manager.save_tokens(
                    client.auth.access_token,
                    client.auth.refresh_token if hasattr(client.auth, 'refresh_token') else None,
                    expires_in=1800  # 30 minutes
                )
        
        # Initialize the overview class
        overview = AccountOverview(client)
        
        # Get all account numbers
        print("\nFetching account numbers...")
        account_numbers = client.get_account_numbers()
        
        # Print overview for each account
        for account in account_numbers.accounts:
            print(f"\nAccount Overview for: {account.account_number}")
            print("=" * 50)
            overview.print_account_overview(account.hash_value)

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()