#!/usr/bin/env python3
"""
Advanced Streaming Demo - Demonstrates all streaming features.

This example shows how to use:
- Level 1 equity quotes
- Level 2 order book data
- Options quotes with Greeks
- Real-time news
- Account activity monitoring
- Chart data streaming
"""

import asyncio
import json
import os
import signal
import sys
import webbrowser
from datetime import datetime
from typing import Dict, Any, List
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
    StreamingQuote, StreamingOptionQuote, StreamingOrderBook,
    StreamingNews, StreamingChartBar, StreamingAccountActivity,
    LevelOneEquityFields, LevelOneOptionFields
)
from credential_manager import CredentialManager


class StreamingDemo:
    """Demonstrates advanced streaming features."""
    
    def __init__(self):
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
        print("Getting user preferences...")
        user_prefs = self.client.get_user_preferences()
        
        if not user_prefs.streamer_info:
            raise ValueError("No streamer info available in user preferences")
            
        # Initialize streaming client
        self.streamer = StreamerClient(self.client.auth, user_prefs.streamer_info[0])
        
        print("Setup complete!")
        
    async def on_level1_quote(self, service: str, data: List[Dict[str, Any]]):
        """Handle Level 1 equity quotes."""
        print(f"\n=== Level 1 Equity Quote Update ===")
        for item in data:
            quote = StreamingQuote.from_data(item)
            print(f"Symbol: {quote.symbol}")
            print(f"  Bid: ${quote.bid_price:.2f} x {quote.bid_size}")
            print(f"  Ask: ${quote.ask_price:.2f} x {quote.ask_size}")
            print(f"  Last: ${quote.last_price:.2f} ({quote.net_change:+.2f})")
            print(f"  Volume: {quote.total_volume:,}")
            
    async def on_level2_data(self, service: str, data: List[Dict[str, Any]]):
        """Handle Level 2 order book data."""
        print(f"\n=== Level 2 Order Book Update ===")
        order_books = StreamingOrderBook.from_data(data)
        
        for symbol, book in order_books.items():
            print(f"Symbol: {symbol}")
            print("  Bids:")
            for i, bid in enumerate(book.bids[:5]):  # Top 5 bids
                print(f"    {i+1}. ${bid.price:.2f} x {bid.size} [{bid.market_maker}]")
            print("  Asks:")
            for i, ask in enumerate(book.asks[:5]):  # Top 5 asks
                print(f"    {i+1}. ${ask.price:.2f} x {ask.size} [{ask.market_maker}]")
                
    async def on_option_quote(self, service: str, data: List[Dict[str, Any]]):
        """Handle option quotes with Greeks."""
        print(f"\n=== Option Quote Update ===")
        for item in data:
            quote = StreamingOptionQuote.from_data(item)
            print(f"Option: {quote.symbol}")
            print(f"  Description: {quote.description}")
            print(f"  Bid/Ask: ${quote.bid_price:.2f} / ${quote.ask_price:.2f}")
            print(f"  Last: ${quote.last_price:.2f}")
            print(f"  Strike: ${quote.strike_price:.2f}")
            print(f"  Greeks:")
            print(f"    Delta: {quote.delta:.4f}")
            print(f"    Gamma: {quote.gamma:.4f}")
            print(f"    Theta: {quote.theta:.4f}")
            print(f"    Vega: {quote.vega:.4f}")
            print(f"    IV: {quote.implied_volatility:.2%}")
            
    async def on_news(self, service: str, data: List[Dict[str, Any]]):
        """Handle news updates."""
        print(f"\n=== News Update ===")
        for item in data:
            news = StreamingNews.from_data(item)
            print(f"Symbol: {news.symbol}")
            print(f"  Headline: {news.headline}")
            print(f"  Time: {datetime.fromtimestamp(news.story_datetime/1000)}")
            print(f"  Hot: {'YES' if news.is_hot else 'NO'}")
            print(f"  Source: {news.story_source}")
            
    async def on_account_activity(self, service: str, data: List[Dict[str, Any]]):
        """Handle account activity updates."""
        print(f"\n=== Account Activity ===")
        for item in data:
            activity = StreamingAccountActivity.from_data(item)
            print(f"Account: {activity.account}")
            print(f"  Type: {activity.message_type}")
            print(f"  Data: {json.dumps(activity.message_data, indent=2)}")
            
    async def on_chart_data(self, service: str, data: List[Dict[str, Any]]):
        """Handle chart data updates."""
        print(f"\n=== Chart Data Update ===")
        for item in data:
            bar = StreamingChartBar.from_data(item)
            print(f"Symbol: {bar.symbol}")
            print(f"  Time: {datetime.fromtimestamp(bar.chart_time/1000)}")
            print(f"  OHLC: {bar.open_price:.2f} / {bar.high_price:.2f} / {bar.low_price:.2f} / {bar.close_price:.2f}")
            print(f"  Volume: {bar.volume:,}")
            
    async def start_streaming(self):
        """Start streaming with various subscriptions."""
        print("\nStarting streaming client...")
        await self.streamer.start()
        
        # Set quality of service to real-time
        await self.streamer.set_qos(QOSLevel.REAL_TIME)
        
        # Example symbols
        equity_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        option_symbols = ["AAPL_112924C200", "MSFT_112924P400"]  # Example option symbols
        
        print("\nSubscribing to streams...")
        
        # Subscribe to Level 1 equity quotes
        await self.streamer.subscribe_level_one_equity(
            symbols=equity_symbols,
            fields=[f.value for f in LevelOneEquityFields],
            callback=self.on_level1_quote
        )
        print(f"✓ Subscribed to Level 1 quotes for: {', '.join(equity_symbols)}")
        
        # Subscribe to Level 2 order book (usually requires special permissions)
        try:
            await self.streamer.subscribe_level_two_equity(
                symbols=["AAPL"],  # Level 2 is data intensive, so fewer symbols
                callback=self.on_level2_data
            )
            print("✓ Subscribed to Level 2 order book for AAPL")
        except Exception as e:
            print(f"✗ Level 2 subscription failed (may require special permissions): {e}")
        
        # Subscribe to option quotes with Greeks
        try:
            await self.streamer.subscribe_level_one_option(
                symbols=option_symbols,
                fields=[f.value for f in LevelOneOptionFields],
                callback=self.on_option_quote
            )
            print(f"✓ Subscribed to option quotes for: {', '.join(option_symbols)}")
        except Exception as e:
            print(f"✗ Option subscription failed: {e}")
        
        # Subscribe to news
        await self.streamer.subscribe_news(
            symbols=equity_symbols,
            callback=self.on_news
        )
        print(f"✓ Subscribed to news for: {', '.join(equity_symbols)}")
        
        # Subscribe to account activity
        await self.streamer.subscribe_account_activity(
            callback=self.on_account_activity
        )
        print("✓ Subscribed to account activity")
        
        # Subscribe to chart data
        await self.streamer.subscribe_chart_equity(
            symbols=["AAPL", "MSFT"],
            callback=self.on_chart_data
        )
        print("✓ Subscribed to chart data for AAPL and MSFT")
        
        print("\n" + "="*50)
        print("Streaming is active! Press Ctrl+C to stop.")
        print("="*50)
        
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
            
    def handle_signal(self, signum, frame):
        """Handle shutdown signals."""
        self.running = False


async def main():
    """Main entry point."""
    demo = StreamingDemo()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, demo.handle_signal)
    signal.signal(signal.SIGTERM, demo.handle_signal)
    
    await demo.run()


if __name__ == "__main__":
    # Enable debug logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Schwab Advanced Streaming Demo")
    print("==============================")
    print()
    print("This demo shows all streaming capabilities:")
    print("- Level 1 equity quotes")
    print("- Level 2 order book depth")
    print("- Options quotes with Greeks")
    print("- Real-time news")
    print("- Account activity monitoring")
    print("- Chart data streaming")
    print()
    
    asyncio.run(main())