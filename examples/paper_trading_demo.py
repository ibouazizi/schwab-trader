#!/usr/bin/env python3
"""
Schwab Paper Trading Demo

This script demonstrates how to use the paper trading features
of the Schwab Trader library to practice trading strategies
without using real money.
"""

import os
import sys
import webbrowser
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import logging
from tabulate import tabulate
from time import sleep

# Add parent directory to path for schwab imports
# Add examples directory to path for credential_manager imports
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_script_dir))
sys.path.insert(0, _script_dir)

from schwab.paper_trading.client import PaperTradingClient
from schwab.paper_trading.account import PaperAccountManager
from schwab.models.generated.trading_models import Instruction as OrderInstruction
from schwab.portfolio import PortfolioManager
from credential_manager import CredentialManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize credential manager
cred_manager = CredentialManager()

def get_authorization_code(auth):
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

def format_currency(amount):
    """Format a number as currency."""
    return f"${amount:,.2f}"

def print_account_list(accounts):
    """Print a list of accounts with type indicators."""
    account_data = []
    for account in accounts:
        account_type = "PAPER" if "PAPER" in account_data else "LIVE"
        account_data.append([
            account.account_number,
            account.hash_value,
            account_type
        ])
    
    if account_data:
        print(tabulate(
            account_data,
            headers=['Account Number', 'Hash Value', 'Type'],
            tablefmt='grid'
        ))
    else:
        print("No accounts found.")

def print_paper_account_details(paper_accounts_data):
    """Print details of paper trading accounts."""
    for account_number, account_info in paper_accounts_data.items():
        print(f"\n=== Paper Account: {account_number} ===")
        
        # Print account balances
        print("\nAccount Balances:")
        balances = account_info.securities_account.current_balances
        print(f"Cash Balance: {format_currency(balances.cash_balance)}")
        print(f"Buying Power: {format_currency(balances.buying_power)}")
        print(f"Equity Value: {format_currency(balances.equity)}")
        
        # Print positions if available
        if account_info.securities_account.positions:
            print("\nPositions:")
            positions_data = []
            for position in account_info.securities_account.positions:
                positions_data.append([
                    position.instrument.symbol,
                    position.long_quantity - position.short_quantity,
                    format_currency(position.market_value)
                ])
            
            print(tabulate(
                positions_data,
                headers=['Symbol', 'Quantity', 'Market Value'],
                tablefmt='grid'
            ))
        else:
            print("\nNo positions found.")

def order_status_callback(order, status):
    """Callback for order status changes."""
    print(f"\nOrder Status Change: #{order.order_id} - {status}")
    print(f"  Symbol: {order.order_leg_collection[0].instrument['symbol']}")
    print(f"  Type: {order.order_type}")
    print(f"  Filled: {order.filled_quantity}/{order.quantity}")

def main():
    """Main function demonstrating paper trading capabilities."""
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
        # Initialize the paper trading client
        client = PaperTradingClient(
            client_id=auth_params['client_id'],
            client_secret=auth_params['client_secret'],
            redirect_uri=auth_params.get('redirect_uri', 'https://localhost:8443/callback'),
            paper_trading_enabled=True  # Start in paper trading mode
        )
        
        # Check for valid tokens
        tokens = cred_manager.get_tokens()
        if tokens and tokens['is_valid']:
            print("Using stored access token...")
            client.auth.access_token = tokens['access_token']
            client.auth.refresh_token = tokens['refresh_token']
            print("Successfully authenticated using stored tokens!")
        else:
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
        
        # Display paper trading status
        status = client.paper_trading_status()
        print(f"\nCurrent trading mode: {status}")
        
        # Get all accounts and identify paper accounts
        all_accounts = client.get_account_numbers()
        print(f"\nFound {len(all_accounts.accounts)} total accounts:")
        print_account_list(all_accounts.accounts)
        
        # Specifically identify paper trading accounts
        paper_accounts = client.get_paper_accounts()
        print(f"\nFound {len(paper_accounts)} paper trading accounts:")
        print_account_list(paper_accounts)
        
        if not paper_accounts:
            print("\nNo paper trading accounts found. Paper trading may not be enabled for your account.")
            print("Contact Schwab customer service to enable paper trading.")
            return
            
        # Get details for paper accounts
        paper_account_manager = PaperAccountManager(client)
        paper_accounts_data = paper_account_manager.get_paper_account_balances(include_positions=True)
        print_paper_account_details(paper_accounts_data)
        
        # Initialize portfolio manager with paper trading account
        if paper_accounts:
            portfolio = PortfolioManager(client)
            print("\nAdding paper trading account to portfolio manager...")
            portfolio.add_account(paper_accounts[0].hash_value)
            
            # Register for order status updates
            portfolio.monitor_orders(order_status_callback)
            
            # Interactive demo loop
            print("\n=== Paper Trading Demo ===")
            print("Choose an option:")
            print("1. Place a paper trade")
            print("2. View portfolio summary")
            print("3. Switch trading mode")
            print("4. Exit")
            
            while True:
                choice = input("\nEnter choice (1-4): ").strip()
                
                if choice == '1':
                    # Place a paper trade
                    print("\nPlacing a paper trade...")
                    
                    symbol = input("Enter symbol: ").strip().upper()
                    quantity = int(input("Enter quantity: ").strip())
                    side = input("Buy or sell (b/s): ").strip().lower()
                    
                    instruction = OrderInstruction.BUY if side.startswith('b') else OrderInstruction.SELL
                    
                    # Create a market order
                    order = client.create_market_order(
                        symbol=symbol,
                        quantity=quantity,
                        instruction=instruction,
                        description=symbol
                    )
                    
                    # Place the order via portfolio manager
                    try:
                        paper_account = paper_accounts[0].hash_value
                        order_id = portfolio.place_order(paper_account, order)
                        print(f"Order placed successfully with ID: {order_id}")
                    except Exception as e:
                        print(f"Error placing order: {str(e)}")
                    
                elif choice == '2':
                    # View portfolio summary
                    print("\nGetting portfolio summary...")
                    summary = portfolio.get_portfolio_summary()
                    
                    print(f"Total Value: {format_currency(summary['total_value'])}")
                    print(f"Cash: {format_currency(summary['total_cash'])} ({summary['cash_allocation']:.2f}%)")
                    print(f"Equity: {format_currency(summary['total_equity'])} ({summary['equity_allocation']:.2f}%)")
                    
                    # Show positions
                    if summary['positions_by_symbol']:
                        positions_data = []
                        for symbol, data in summary['positions_by_symbol'].items():
                            positions_data.append([
                                symbol,
                                data['quantity'],
                                format_currency(data['market_value'])
                            ])
                        
                        print("\nPositions:")
                        print(tabulate(
                            positions_data,
                            headers=['Symbol', 'Quantity', 'Market Value'],
                            tablefmt='grid'
                        ))
                    else:
                        print("\nNo positions found.")
                    
                    # Show order history
                    orders = portfolio.get_order_history()
                    if orders:
                        order_data = []
                        for order in orders:
                            leg = order.order_leg_collection[0]
                            order_data.append([
                                order.order_id,
                                leg.instrument['symbol'],
                                order.order_type,
                                leg.instruction,
                                f"{order.filled_quantity}/{order.quantity}",
                                order.status
                            ])
                        
                        print("\nRecent Orders:")
                        print(tabulate(
                            order_data,
                            headers=['ID', 'Symbol', 'Type', 'Side', 'Filled/Qty', 'Status'],
                            tablefmt='grid'
                        ))
                    else:
                        print("\nNo order history found.")
                    
                elif choice == '3':
                    # Toggle paper trading mode
                    if client.is_paper_trading_enabled:
                        print("\nSwitching to LIVE trading mode...")
                        client.disable_paper_trading()
                    else:
                        print("\nSwitching to PAPER trading mode...")
                        client.enable_paper_trading()
                    
                    # Display current status
                    status = client.paper_trading_status()
                    print(f"Trading mode changed to: {status}")
                    
                elif choice == '4':
                    # Exit the demo
                    print("\nExiting Paper Trading Demo...")
                    break
                    
                else:
                    print("Invalid choice. Please try again.")
            
        else:
            print("\nNo paper trading accounts available. Demo cannot continue.")
            
    except Exception as e:
        logger.error(f"Error in Paper Trading Demo: {str(e)}")
        
if __name__ == "__main__":
    main()