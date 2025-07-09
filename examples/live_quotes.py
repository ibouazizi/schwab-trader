#!/usr/bin/env python3
"""Real-time stock quote display using the Schwab API with unified credential management."""

import os
import sys
import asyncio
import aiohttp
from datetime import datetime, timedelta
import time
from typing import Dict, Optional
import signal
import json
import base64
from pathlib import Path
from schwab import AsyncSchwabClient
from schwab.models.quotes import QuoteData

# Add parent directory to path if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from credential_manager import CredentialManager

# Initialize credential manager
cred_manager = CredentialManager()

# API endpoints
TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"

# ANSI color codes
GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"
BOLD = "\033[1m"
CLEAR_SCREEN = "\033[2J\033[H"


class QuoteMonitor:
    def __init__(self, symbols: list[str]):
        self.symbols = symbols
        self.previous_quotes: Dict[str, QuoteData] = {}
        self.running = True
        self.access_token = None
        self.token_expires_at = 0
        self.api_key = None
        self.api_secret = None
        
        # Initialize client
        self.client = None  # Will be initialized in setup
        
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
        
    def format_price(self, price: Optional[float]) -> str:
        """Format price with 2 decimal places."""
        return f"{price:.2f}" if price is not None else "N/A"
        
    def format_change(self, current: Optional[float], previous: Optional[float]) -> str:
        """Format price change with color coding."""
        if current is None or previous is None:
            return "N/A"
            
        change = current - previous
        pct_change = (change / previous) * 100
        
        if change > 0:
            return f"{GREEN}+{change:.2f} (+{pct_change:.2f}%){RESET}"
        elif change < 0:
            return f"{RED}{change:.2f} ({pct_change:.2f}%){RESET}"
        else:
            return f"0.00 (0.00%)"
            
    def print_header(self):
        """Print the table header."""
        print(CLEAR_SCREEN)  # Clear screen
        print(f"{BOLD}Real-time Stock Quotes - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
        print("\nSymbol    Last Price    Bid x Size    Ask x Size    Volume      Change")
        print("-" * 75)
        
    def print_quote(self, symbol: str, quote: QuoteData):
        """Print a single quote with formatting."""
        if not quote.quote:
            return
            
        previous = self.previous_quotes.get(symbol)
        
        # Format the quote data
        last_price = self.format_price(quote.quote.last_price) if quote.quote.last_price else "N/A"
        bid = f"{self.format_price(quote.quote.bid_price)} x {quote.quote.bid_size or 0}" if quote.quote.bid_price is not None else "N/A"
        ask = f"{self.format_price(quote.quote.ask_price)} x {quote.quote.ask_size or 0}" if quote.quote.ask_price is not None else "N/A"
        volume = f"{quote.quote.total_volume:,}" if quote.quote.total_volume else "N/A"
        
        # Calculate change from previous quote
        prev_quote = None
        if previous:
            if hasattr(previous, 'root'):
                prev_quote = previous.root
            else:
                prev_quote = previous
                
        if prev_quote and prev_quote.quote and prev_quote.quote.last_price and quote.quote.last_price:
            change = self.format_change(quote.quote.last_price, prev_quote.quote.last_price)
        elif quote.quote.last_price and quote.quote.close_price:
            change = self.format_change(quote.quote.last_price, quote.quote.close_price)
        else:
            change = "N/A"
            
        # Print the formatted line
        print(f"{symbol:<9} {last_price:>10}  {bid:>12}  {ask:>12}  {volume:>10}  {change}")
        
    async def update_quotes(self):
        """Update and display quotes."""
        await self.setup()  # Initial setup
        
        while self.running:
            try:
                # Ensure token is valid
                token = await self.ensure_valid_token()
                if token != self.client.api_key:
                    self.client = AsyncSchwabClient(api_key=token)
                
                # Get quotes for all symbols
                async with self.client:  # Use context manager
                    try:
                        quotes = await self.client.async_get_quotes(self.symbols)
                        quotes = quotes.root  # Access the root dictionary
                    except Exception as e:
                        print(f"Error getting quotes: {e}")
                        continue
                
                self.print_header()
                
                # Print quotes in symbol order
                for symbol in self.symbols:
                    if symbol in quotes:
                        # Access the actual response object through the root attribute
                        quote_obj = quotes[symbol]
                        if hasattr(quote_obj, 'root'):
                            self.print_quote(symbol, quote_obj.root)
                        else:
                            self.print_quote(symbol, quote_obj)
                        
                # Update previous quotes
                self.previous_quotes = quotes
                
                # Wait for next update
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error fetching quotes: {e}")
                await asyncio.sleep(1)
                
    def stop(self):
        """Stop the quote monitor."""
        self.running = False


async def main():
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
    
    # Tech stock symbols to monitor
    symbols = [
        "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA",
        "TSLA", "ADBE", "NFLX", "QCOM", "AVGO", "AMD"
    ]
    
    # Create and start quote monitor
    monitor = QuoteMonitor(symbols)
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\nStopping quote monitor...")
        monitor.stop()
        
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run the monitor
    await monitor.update_quotes()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")