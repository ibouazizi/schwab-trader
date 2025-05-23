#!/usr/bin/env python3
"""
Schwab Portfolio Manager Demo

This script demonstrates how to use the PortfolioManager class to track
positions, orders, and executions across multiple accounts. It supports
both regular and paper trading accounts, as well as a demo mode that works
without API access.
"""

import os
import webbrowser
import logging
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import time
from decimal import Decimal
from tabulate import tabulate

from schwab import SchwabClient, SchwabAuth, PortfolioManager
from schwab.paper_trading.client import PaperTradingClient
# Import directly from generated models
from schwab.models.generated.trading_models import (
    Status as OrderStatus,
    Instruction as OrderInstruction,
    Session,
    OrderType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API information - Replace with your API keys
SCHWAB_CLIENT_ID = os.getenv('SCHWAB_CLIENT_ID', 'YOUR_CLIENT_ID')
SCHWAB_CLIENT_SECRET = os.getenv('SCHWAB_CLIENT_SECRET', 'YOUR_CLIENT_SECRET')
SCHWAB_REDIRECT_URI = os.getenv('SCHWAB_REDIRECT_URI', 'YOUR_REDIRECT_URI')

# Where to store portfolio state
PERSISTENCE_PATH = 'portfolio_state.json'

# Set to True to run in demo mode (no API access required)
DEMO_MODE = False

# Set to True to use paper trading (safer for testing)
USE_PAPER_TRADING = True

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

def order_status_callback(order, status):
    """Callback for order status changes."""
    print(f"\nOrder Status Change: #{order.order_id} - {status}")
    print(f"  Symbol: {order.order_leg_collection[0].instrument['symbol']}")
    print(f"  Type: {order.order_type}")
    print(f"  Filled: {order.filled_quantity}/{order.quantity}")

def format_currency(amount):
    """Format a Decimal as currency."""
    return f"${amount:,.2f}"

def format_percentage(value):
    """Format a Decimal as a percentage."""
    return f"{value:.2f}%"

def print_portfolio_summary(portfolio):
    """Print a summary of the portfolio."""
    summary = portfolio.get_portfolio_summary()
    
    print("\n=== Portfolio Summary ===")
    print(f"Total Value: {format_currency(summary['total_value'])}")
    print(f"Cash: {format_currency(summary['total_cash'])} ({format_percentage(summary['cash_allocation'])})")
    print(f"Equity: {format_currency(summary['total_equity'])} ({format_percentage(summary['equity_allocation'])})")
    print(f"Accounts: {len(summary['accounts'])}")
    print(f"Open Orders: {summary['open_orders']}")
    print(f"Total Orders: {summary['total_orders']}")
    print(f"Total Executions: {summary['total_executions']}")
    
    print("\n=== Asset Allocation ===")
    allocation_data = []
    for asset_class, percentage in summary['asset_allocation'].items():
        if percentage > 0:
            allocation_data.append([asset_class, format_percentage(percentage)])
    
    if allocation_data:
        print(tabulate(allocation_data, headers=['Asset Class', 'Allocation'], tablefmt='grid'))
    else:
        print("No assets found.")
    
    print("\n=== Positions by Symbol ===")
    positions_data = []
    for symbol, data in summary['positions_by_symbol'].items():
        if data['market_value'] > 0:
            gain_loss = data['market_value'] - data['cost_basis']
            gain_loss_pct = (gain_loss / data['cost_basis'] * 100) if data['cost_basis'] > 0 else Decimal('0')
            
            positions_data.append([
                symbol,
                data['quantity'],
                format_currency(data['market_value']),
                format_currency(gain_loss),
                format_percentage(gain_loss_pct)
            ])
    
    if positions_data:
        print(tabulate(
            positions_data,
            headers=['Symbol', 'Quantity', 'Market Value', 'Gain/Loss', 'G/L %'],
            tablefmt='grid'
        ))
    else:
        print("No positions found.")

def print_order_history(portfolio):
    """Print recent order history."""
    # Get orders from the last 30 days
    from_date = datetime.now() - timedelta(days=30)
    orders = portfolio.get_order_history(from_date=from_date)
    
    print("\n=== Recent Order History ===")
    order_data = []
    for order in orders:
        if order.entered_time:  # Check if entered_time exists
            leg = order.order_leg_collection[0]
            order_data.append([
                order.order_id,
                leg.instrument['symbol'],
                order.order_type,
                leg.instruction,
                f"{order.filled_quantity}/{order.quantity}",
                order.status,
                order.entered_time.strftime("%Y-%m-%d %H:%M")
            ])
    
    if order_data:
        print(tabulate(
            order_data,
            headers=['Order ID', 'Symbol', 'Type', 'Side', 'Filled/Qty', 'Status', 'Entered'],
            tablefmt='grid'
        ))
    else:
        print("No recent orders found.")

def main():
    """Main function to demonstrate portfolio manager."""
    try:
        # Initialize the client with OAuth credentials
        client = SchwabClient(            
            client_id=SCHWAB_CLIENT_ID,
            client_secret=SCHWAB_CLIENT_SECRET,
            redirect_uri=SCHWAB_REDIRECT_URI
        )
        
        # Get authorization code through OAuth flow
        auth_code = get_authorization_code(client.auth)
        
        # Exchange authorization code for tokens
        print("\nExchanging authorization code for tokens...")
        token_data = client.auth.exchange_code_for_tokens(auth_code)
        print("Successfully authenticated!")
        
        # Initialize the portfolio manager
        portfolio = PortfolioManager(client, persistence_path=PERSISTENCE_PATH)
        
        # Get all account numbers
        print("\nFetching account numbers...")
        accounts = client.get_account_numbers()
        
        # Add accounts to portfolio manager
        for account in accounts.accounts:
            print(f"Adding account {account.account_number} to portfolio...")
            portfolio.add_account(account.hash_value)
        
        # Register for order status notifications
        portfolio.monitor_orders(order_status_callback)
        
        # Display portfolio summary
        print_portfolio_summary(portfolio)
        print_order_history(portfolio)
        
        # Interactive loop
        print("\n=== Portfolio Manager Demo ===")
        print("Choose an option:")
        print("1. Refresh portfolio")
        print("2. Place a market order")
        print("3. View order history")
        print("4. View specific position")
        print("5. Exit")
        
        while True:
            choice = input("\nEnter choice (1-5): ").strip()
            
            if choice == '1':
                print("Refreshing portfolio...")
                portfolio.refresh_positions()
                print_portfolio_summary(portfolio)
                
            elif choice == '2':
                account_hash = accounts.accounts[0].hash_value  # Use first account
                symbol = input("Enter symbol: ").strip().upper()
                quantity = int(input("Enter quantity: ").strip())
                side = input("Enter side (buy/sell): ").strip().lower()
                
                instruction = OrderInstruction.BUY if side == 'buy' else OrderInstruction.SELL
                
                print(f"Creating market order for {quantity} shares of {symbol}...")
                order = client.create_market_order(
                    symbol=symbol,
                    quantity=quantity,
                    instruction=instruction,
                    description=symbol
                )
                
                order_id = portfolio.place_order(account_hash, order)
                print(f"Order placed with ID: {order_id}")
                
            elif choice == '3':
                print_order_history(portfolio)
                
            elif choice == '4':
                symbol = input("Enter symbol: ").strip().upper()
                position = portfolio.get_position(symbol)
                
                print(f"\n=== Position: {symbol} ===")
                print(f"Quantity: {position['quantity']}")
                print(f"Market Value: {format_currency(position['market_value'])}")
                print(f"Cost Basis: {format_currency(position['cost_basis'])}")
                print(f"Average Price: {format_currency(position['average_price'])}")
                print(f"Gain/Loss: {format_currency(position['gain_loss'])} ({format_percentage(position['gain_loss_pct'])})")
                
            elif choice == '5':
                break
                
            else:
                print("Invalid choice. Please try again.")
        
        # Stop monitoring before exit
        portfolio.stop_monitoring()
        print("Exiting...")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()