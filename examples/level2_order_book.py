#!/usr/bin/env python3
"""
Level 2 Order Book Demo - Real-time order book visualization.

This example shows how to:
- Subscribe to Level 2 order book data
- Display bid/ask depth
- Track market maker activity
- Calculate spread and book imbalance
"""

import asyncio
import os
import sys
import webbrowser
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict
from urllib.parse import urlparse, parse_qs

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schwab.auth import SchwabAuth
from schwab.client import SchwabClient
from schwab.streaming import (
    StreamerClient, StreamerService, QOSLevel,
    StreamingOrderBook, OrderBookEntry
)
from credential_manager import CredentialManager


class OrderBookMonitor:
    """Monitor and display Level 2 order book data."""
    
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.order_books: Dict[str, StreamingOrderBook] = {}
        self.auth = None
        self.client = None
        self.streamer = None
        self.running = True
        self.cred_manager = CredentialManager()
        
    def get_authorization_code(self, auth: SchwabAuth) -> str:
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
        
    async def setup(self):
        """Initialize authentication and clients."""
        print("Initializing Schwab API...")
        
        # Check for stored credentials or prompt for new ones
        auth_params = self.cred_manager.get_auth_params()
        
        if not auth_params:
            print("\nNo stored credentials found. Please enter your Schwab API credentials.")
            print("You can obtain these from: https://developer.schwab.com\n")
            
            client_id = input("Client ID: ").strip()
            client_secret = input("Client Secret: ").strip()
            redirect_uri = input("Redirect URI (default: https://localhost:8443/callback): ").strip()
            
            if not redirect_uri:
                redirect_uri = "https://localhost:8443/callback"
            
            # Save credentials
            self.cred_manager.save_credentials(client_id, client_secret, redirect_uri)
            auth_params = {
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri
            }
        else:
            print("\nUsing stored credentials...")
            
        # Initialize the client with OAuth credentials
        self.client = SchwabClient(            
            client_id=auth_params['client_id'],
            client_secret=auth_params['client_secret'],
            redirect_uri=auth_params.get('redirect_uri', 'https://localhost:8443/callback')
        )
        
        # Check for valid tokens
        tokens = self.cred_manager.get_tokens()
        if tokens and tokens['is_valid']:
            print("Using stored access token...")
            self.client.auth.access_token = tokens['access_token']
            self.client.auth.refresh_token = tokens['refresh_token']
            self.client.auth.token_expiry = tokens['expiry']
            print("Successfully authenticated using stored tokens!")
        else:
            # Get new authorization
            auth_code = self.get_authorization_code(self.client.auth)
            
            # Exchange authorization code for tokens
            print("\nExchanging authorization code for tokens...")
            token_data = self.client.auth.exchange_code_for_tokens(auth_code)
            print("Successfully authenticated!")
            
            # Save tokens
            if hasattr(self.client.auth, 'access_token') and self.client.auth.access_token:
                self.cred_manager.save_tokens(
                    self.client.auth.access_token,
                    self.client.auth.refresh_token if hasattr(self.client.auth, 'refresh_token') else None,
                    expires_in=1800  # 30 minutes
                )
        
        # Get user preferences for streaming
        user_prefs = self.client.get_user_preferences()
        
        if not user_prefs.streamer_info:
            raise ValueError("No streamer info available in user preferences")
            
        # Initialize streaming client
        self.streamer = StreamerClient(self.client.auth, user_prefs.streamer_info[0])
        
        print("Setup complete!")
        
    def display_order_book(self, symbol: str, book: StreamingOrderBook):
        """Display order book in a formatted way."""
        print(f"\n{'='*60}")
        print(f"Order Book for {symbol} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        # Calculate metrics
        if book.bids and book.asks:
            spread = book.asks[0].price - book.bids[0].price
            mid_price = (book.asks[0].price + book.bids[0].price) / 2
            
            # Calculate book imbalance
            total_bid_size = sum(bid.size for bid in book.bids[:10])
            total_ask_size = sum(ask.size for ask in book.asks[:10])
            imbalance = (total_bid_size - total_ask_size) / (total_bid_size + total_ask_size) * 100
            
            print(f"Spread: ${spread:.2f} | Mid: ${mid_price:.2f} | Imbalance: {imbalance:+.1f}%")
            print("-" * 60)
        
        # Display header
        print(f"{'Level':<6} {'Bid Size':>10} {'Bid Price':>10} | {'Ask Price':>10} {'Ask Size':>10} {'MM':<10}")
        print("-" * 60)
        
        # Display top 10 levels
        max_levels = 10
        for i in range(max_levels):
            bid_info = ""
            ask_info = ""
            
            if i < len(book.bids):
                bid = book.bids[i]
                bid_info = f"{bid.size:>10,} {bid.price:>10.2f}"
                
            if i < len(book.asks):
                ask = book.asks[i]
                mm = ask.market_maker or ""
                ask_info = f"{ask.price:>10.2f} {ask.size:>10,} {mm:<10}"
                
            print(f"{i+1:<6} {bid_info:>21} | {ask_info}")
            
        # Summary statistics
        if book.bids and book.asks:
            print("-" * 60)
            print(f"Total Bid Depth (10 levels): {sum(b.size for b in book.bids[:10]):,}")
            print(f"Total Ask Depth (10 levels): {sum(a.size for a in book.asks[:10]):,}")
            
            # Market maker distribution
            mm_counts = defaultdict(int)
            for ask in book.asks[:20]:
                if ask.market_maker:
                    mm_counts[ask.market_maker] += 1
            for bid in book.bids[:20]:
                if bid.market_maker:
                    mm_counts[bid.market_maker] += 1
                    
            if mm_counts:
                print(f"\nTop Market Makers:")
                for mm, count in sorted(mm_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"  {mm}: {count} orders")
        
    async def on_level2_update(self, service: str, data: List[Dict[str, Any]]):
        """Handle Level 2 order book updates."""
        order_books = StreamingOrderBook.from_data(data)
        
        # Update our stored order books
        self.order_books.update(order_books)
        
        # Display each updated book
        for symbol, book in order_books.items():
            self.display_order_book(symbol, book)
            
    async def start_streaming(self):
        """Start streaming Level 2 data."""
        print("\nStarting streaming client...")
        await self.streamer.start()
        
        # Set quality of service to express (fastest)
        await self.streamer.set_qos(QOSLevel.EXPRESS)
        
        print(f"\nSubscribing to Level 2 data for: {', '.join(self.symbols)}")
        
        try:
            await self.streamer.subscribe_level_two_equity(
                symbols=self.symbols,
                callback=self.on_level2_update
            )
            print("✓ Successfully subscribed to Level 2 data")
        except Exception as e:
            print(f"✗ Failed to subscribe to Level 2 data: {e}")
            print("\nNote: Level 2 data often requires:")
            print("- Special permissions from your broker")
            print("- Additional market data subscriptions")
            print("- Professional trader status")
            raise
            
        print("\n" + "="*60)
        print("Level 2 Order Book Monitor Active!")
        print("Press Ctrl+C to stop")
        print("="*60)
        
    async def refresh_token_if_needed(self):
        """Check and refresh token if it's about to expire."""
        tokens = self.cred_manager.get_tokens()
        if tokens and tokens['expires_in'] < 300:  # Less than 5 minutes left
            print("\nToken expiring soon, refreshing...")
            try:
                # Refresh the token
                self.client.auth.refresh_access_token()
                
                # Save the new tokens
                if hasattr(self.client.auth, 'access_token') and self.client.auth.access_token:
                    self.cred_manager.save_tokens(
                        self.client.auth.access_token,
                        self.client.auth.refresh_token if hasattr(self.client.auth, 'refresh_token') else None,
                        expires_in=1800  # 30 minutes
                    )
                    print("Token refreshed successfully!")
            except Exception as e:
                print(f"Error refreshing token: {e}")
                
    async def run(self):
        """Main run loop with token refresh."""
        try:
            await self.setup()
            await self.start_streaming()
            
            # Keep running until interrupted
            token_check_counter = 0
            while self.running:
                await asyncio.sleep(1)
                
                # Check token every 60 seconds
                token_check_counter += 1
                if token_check_counter >= 60:
                    await self.refresh_token_if_needed()
                    token_check_counter = 0
                
        except KeyboardInterrupt:
            print("\nShutting down...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if self.streamer:
                await self.streamer.stop()
            print("Streaming stopped.")


async def main():
    """Main entry point."""
    # Configure symbols to monitor
    symbols = ["AAPL", "MSFT", "SPY"]  # Level 2 is data intensive, so limit symbols
    
    # You can override with command line arguments
    if len(sys.argv) > 1:
        symbols = sys.argv[1].split(",")
    
    monitor = OrderBookMonitor(symbols)
    await monitor.run()


if __name__ == "__main__":
    # Enable logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Schwab Level 2 Order Book Monitor")
    print("=================================")
    print()
    print("Usage: python level2_order_book.py [SYMBOL1,SYMBOL2,...]")
    print("Example: python level2_order_book.py AAPL,MSFT,SPY")
    print()
    print("Features:")
    print("- Real-time bid/ask depth")
    print("- Spread and mid-price calculation")
    print("- Book imbalance indicator")
    print("- Market maker tracking")
    print()
    
    asyncio.run(main())