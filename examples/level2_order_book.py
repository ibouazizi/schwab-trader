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

# Add parent directory to path for schwab imports
# Add examples directory to path for credential_manager imports
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_script_dir))
sys.path.insert(0, _script_dir)

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
        
        # Check for market data credentials first
        auth_params = self.cred_manager.get_auth_params(api_type="market_data")
        
        if not auth_params:
            print("\nNo stored market data credentials found.")
            print("Level 2 streaming requires Market Data API credentials.")
            print("You can obtain these from: https://developer.schwab.com\n")
            
            client_id = input("Market Data API Client ID: ").strip()
            client_secret = input("Market Data API Client Secret: ").strip()
            
            # Save market data credentials
            self.cred_manager.save_credentials(client_id, client_secret, api_type="market_data")
            auth_params = {
                'client_id': client_id,
                'client_secret': client_secret
            }
        else:
            print("\nUsing stored market data credentials...")
            
        # For market data streaming, we need a trading client for user preferences
        # but will use market data credentials for streaming auth
        trading_params = self.cred_manager.get_auth_params(api_type="trading")
        if not trading_params:
            print("\nTrading API credentials also needed for user preferences...")
            trading_client_id = input("Trading API Client ID: ").strip()
            trading_client_secret = input("Trading API Client Secret: ").strip()
            redirect_uri = input("Redirect URI (default: https://localhost:8443/callback): ").strip()
            if not redirect_uri:
                redirect_uri = "https://localhost:8443/callback"
            self.cred_manager.save_credentials(trading_client_id, trading_client_secret, redirect_uri, api_type="trading")
            trading_params = {
                'client_id': trading_client_id,
                'client_secret': trading_client_secret,
                'redirect_uri': redirect_uri
            }
        
        # Initialize the trading client for user preferences
        self.client = SchwabClient(            
            client_id=trading_params['client_id'],
            client_secret=trading_params['client_secret'],
            redirect_uri=trading_params.get('redirect_uri', 'https://localhost:8443/callback')
        )
        
        # Check for valid trading tokens (for user preferences)
        tokens = self.cred_manager.get_tokens(api_type="trading")
        if tokens and tokens['is_valid']:
            print("Using stored trading access token...")
            self.client.auth.access_token = tokens['access_token']
            self.client.auth.refresh_token = tokens['refresh_token']
            self.client.auth.token_expiry = tokens['expiry']
            print("Successfully authenticated with trading API!")
        else:
            # Get new authorization
            auth_code = self.get_authorization_code(self.client.auth)
            
            # Exchange authorization code for tokens
            print("\nExchanging authorization code for trading tokens...")
            token_data = self.client.auth.exchange_code_for_tokens(auth_code)
            print("Successfully authenticated with trading API!")
            
            # Save trading tokens
            if hasattr(self.client.auth, 'access_token') and self.client.auth.access_token:
                self.cred_manager.save_tokens(
                    self.client.auth.access_token,
                    self.client.auth.refresh_token if hasattr(self.client.auth, 'refresh_token') else None,
                    expires_in=1800,  # 30 minutes
                    api_type="trading"
                )
        
        # Get user preferences for streaming
        user_prefs = self.client.get_user_preferences()
        
        if not user_prefs.streamer_info:
            raise ValueError("No streamer info available in user preferences")
            
        # Create market data auth for streaming
        from schwab.auth import SchwabAuth
        market_data_auth = SchwabAuth(
            client_id=auth_params['client_id'],
            client_secret=auth_params['client_secret'],
            redirect_uri="https://localhost:8443/callback"  # Market data doesn't need redirect
        )
        
        # Check for market data tokens
        md_tokens = self.cred_manager.get_tokens(api_type="market_data")
        if md_tokens and md_tokens['is_valid']:
            print("Using stored market data access token...")
            market_data_auth.access_token = md_tokens['access_token']
            market_data_auth.refresh_token = md_tokens['refresh_token']
            market_data_auth.token_expiry = md_tokens['expiry']
        else:
            # Get market data token using client credentials grant
            print("Getting market data access token...")
            try:
                # Market data API uses client credentials grant (no user authorization needed)
                token_data = market_data_auth.get_client_credentials_token()
                print("Successfully authenticated with market data API!")
                
                # Save market data tokens
                self.cred_manager.save_tokens(
                    market_data_auth.access_token,
                    None,  # No refresh token for client credentials
                    expires_in=1800,
                    api_type="market_data"
                )
            except Exception as e:
                print(f"Failed to get market data token: {e}")
                raise
        
        # Initialize streaming client with market data auth
        self.streamer = StreamerClient(market_data_auth, user_prefs.streamer_info[0])
        
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
        print(f"\n🔄 Level 2 callback triggered for service: {service}")
        print(f"📊 Received {len(data)} data items")
        
        # Debug: Print raw data structure
        if data:
            print(f"📋 Sample data structure: {data[0].keys() if data[0] else 'Empty'}")
            for i, item in enumerate(data[:3]):  # Show first 3 items
                print(f"  Item {i}: {item}")
        
        try:
            order_books = StreamingOrderBook.from_data(data)
            print(f"📖 Parsed {len(order_books)} order books")
            
            # Update our stored order books
            self.order_books.update(order_books)
            
            # Display each updated book
            for symbol, book in order_books.items():
                print(f"📈 Displaying order book for {symbol}")
                self.display_order_book(symbol, book)
                
        except Exception as e:
            print(f"❌ Error processing Level 2 data: {e}")
            print(f"📊 Raw data: {data}")
            
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
        print("\n⏳ Waiting for Level 2 data...")
        print("💡 Note: Level 2 data may take time to arrive or may not be available")
        print("   for your account type. Many retail accounts don't have access to")
        print("   real-time Level 2 market depth data.")
        
    async def refresh_token_if_needed(self):
        """Check and refresh tokens if they're about to expire."""
        # Check trading tokens
        trading_tokens = self.cred_manager.get_tokens(api_type="trading")
        if trading_tokens and trading_tokens['expires_in'] < 300:  # Less than 5 minutes left
            print("\nTrading token expiring soon, refreshing...")
            try:
                self.client.auth.refresh_access_token()
                self.cred_manager.save_tokens(
                    self.client.auth.access_token,
                    self.client.auth.refresh_token,
                    expires_in=1800,
                    api_type="trading"
                )
                print("Trading token refreshed successfully!")
            except Exception as e:
                print(f"Error refreshing trading token: {e}")
        
        # Check market data tokens
        md_tokens = self.cred_manager.get_tokens(api_type="market_data")
        if md_tokens and md_tokens['expires_in'] < 300:  # Less than 5 minutes left
            print("\nMarket data token expiring soon, refreshing...")
            try:
                # Market data uses client credentials, so get a new token
                if hasattr(self.streamer, 'streamer') and hasattr(self.streamer.streamer, 'auth'):
                    self.streamer.streamer.auth.get_client_credentials_token()
                    self.cred_manager.save_tokens(
                        self.streamer.streamer.auth.access_token,
                        None,  # No refresh token for client credentials
                        expires_in=1800,
                        api_type="market_data"
                    )
                    print("Market data token refreshed successfully!")
            except Exception as e:
                print(f"Error refreshing market data token: {e}")
                
    async def run(self):
        """Main run loop with token refresh."""
        try:
            await self.setup()
            await self.start_streaming()
            
            # Keep running until interrupted
            token_check_counter = 0
            status_check_counter = 0
            while self.running:
                await asyncio.sleep(1)
                
                # Check token every 60 seconds
                token_check_counter += 1
                if token_check_counter >= 60:
                    await self.refresh_token_if_needed()
                    token_check_counter = 0
                
                # Print status every 30 seconds
                status_check_counter += 1
                if status_check_counter >= 30:
                    is_connected = self.streamer and hasattr(self.streamer, 'streamer') and self.streamer.streamer and self.streamer.streamer.is_connected
                    data_received = len(self.order_books) > 0
                    
                    # Check token status
                    trading_tokens = self.cred_manager.get_tokens(api_type="trading")
                    md_tokens = self.cred_manager.get_tokens(api_type="market_data")
                    trading_valid = trading_tokens and trading_tokens['is_valid']
                    md_valid = md_tokens and md_tokens['is_valid']
                    
                    print(f"\n📡 Status: Connected={is_connected}, Data Received={data_received}, Books={len(self.order_books)}")
                    print(f"🔐 Auth: Trading Token={trading_valid}, Market Data Token={md_valid}")
                    if not data_received:
                        print("💭 Still waiting for Level 2 data. This is normal for retail accounts.")
                        print("🎯 Using Market Data API credentials for streaming authentication.")
                    status_check_counter = 0
                
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