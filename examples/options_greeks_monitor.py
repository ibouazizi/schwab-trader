#!/usr/bin/env python3
"""
Options Greeks Monitor - Real-time options quotes with Greeks.

This example shows how to:
- Subscribe to options quotes with full Greeks
- Monitor implied volatility changes
- Track option price movements
- Calculate profit/loss scenarios
"""

import asyncio
import os
import sys
import webbrowser
from datetime import datetime
from typing import Dict, Any, List, Optional
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
    StreamingOptionQuote, LevelOneOptionFields
)
from credential_manager import CredentialManager


class OptionsGreeksMonitor:
    """Monitor options with real-time Greeks updates."""
    
    def __init__(self):
        self.auth = None
        self.client = None
        self.streamer = None
        self.running = True
        self.option_chains: Dict[str, List[str]] = {}
        self.latest_quotes: Dict[str, StreamingOptionQuote] = {}
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
        
    async def get_option_symbols(self, underlying: str, expiry_days: int = 30) -> List[str]:
        """Get option symbols for streaming."""
        print(f"\nFetching option chain for {underlying}...")
        
        try:
            # Get option chain
            from datetime import timedelta
            to_date = datetime.now() + timedelta(days=expiry_days)
            
            chain = self.client.get_option_chain(
                symbol=underlying,
                contract_type="ALL",
                strike_count=10,  # 10 strikes above and below
                include_underlying_quote=True,
                to_date=to_date
            )
            
            option_symbols = []
            
            # Extract call symbols
            for expiry_date, strikes in chain.call_exp_date_map.items():
                for strike, options in strikes.items():
                    if options:
                        option_symbols.append(options[0].symbol)
                        
            # Extract put symbols
            for expiry_date, strikes in chain.put_exp_date_map.items():
                for strike, options in strikes.items():
                    if options:
                        option_symbols.append(options[0].symbol)
                        
            print(f"Found {len(option_symbols)} option contracts")
            return option_symbols[:20]  # Limit to 20 for demo
            
        except Exception as e:
            print(f"Error fetching option chain: {e}")
            # Return some example option symbols as fallback
            return [
                f"{underlying}_112924C{int(100 + i*5)}" for i in range(5)
            ] + [
                f"{underlying}_112924P{int(100 + i*5)}" for i in range(5)
            ]
            
    def display_option_quote(self, quote: StreamingOptionQuote):
        """Display formatted option quote with Greeks."""
        print(f"\n{'='*80}")
        print(f"Option: {quote.symbol}")
        if quote.description:
            print(f"Description: {quote.description}")
        print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 80)
        
        # Price information
        print(f"{'Pricing:':<20}")
        print(f"  Bid/Ask:         ${quote.bid_price:.2f} / ${quote.ask_price:.2f}")
        if quote.bid_size and quote.ask_size:
            print(f"  Bid/Ask Size:    {quote.bid_size} x {quote.ask_size}")
        print(f"  Last Price:      ${quote.last_price:.2f}")
        print(f"  Volume:          {quote.total_volume:,}")
        print(f"  Open Interest:   {quote.open_interest:,}")
        
        # Contract details
        print(f"\n{'Contract Details:':<20}")
        print(f"  Strike Price:    ${quote.strike_price:.2f}")
        print(f"  Underlying:      ${quote.underlying_price:.2f}")
        
        # Value breakdown
        if quote.intrinsic_value is not None and quote.time_value is not None:
            print(f"\n{'Value Breakdown:':<20}")
            print(f"  Intrinsic Value: ${quote.intrinsic_value:.2f}")
            print(f"  Time Value:      ${quote.time_value:.2f}")
            moneyness = "ITM" if quote.intrinsic_value > 0 else "OTM"
            print(f"  Moneyness:       {moneyness}")
        
        # Greeks
        print(f"\n{'Greeks:':<20}")
        if quote.delta is not None:
            print(f"  Delta:           {quote.delta:+.4f}")
        if quote.gamma is not None:
            print(f"  Gamma:           {quote.gamma:.4f}")
        if quote.theta is not None:
            print(f"  Theta:           {quote.theta:.4f} (${quote.theta:.2f}/day)")
        if quote.vega is not None:
            print(f"  Vega:            {quote.vega:.4f}")
        if quote.rho is not None:
            print(f"  Rho:             {quote.rho:.4f}")
        if quote.implied_volatility is not None:
            print(f"  IV:              {quote.implied_volatility:.1%}")
            
        # Risk scenarios
        if quote.delta is not None and quote.gamma is not None and quote.underlying_price:
            print(f"\n{'Risk Scenarios:':<20}")
            
            # Calculate P&L for different underlying moves
            moves = [-5, -2, -1, 1, 2, 5]  # Percentage moves
            print(f"  Underlying Move  →  Option P&L (per contract)")
            
            for move in moves:
                price_change = quote.underlying_price * (move / 100)
                # Simplified calculation using delta and gamma
                option_change = (quote.delta * price_change + 
                               0.5 * quote.gamma * price_change**2)
                print(f"    {move:+3d}% (${price_change:+6.2f})  →  ${option_change*100:+7.2f}")
                
    async def on_option_update(self, service: str, data: List[Dict[str, Any]]):
        """Handle option quote updates."""
        for item in data:
            quote = StreamingOptionQuote.from_data(item)
            self.latest_quotes[quote.symbol] = quote
            self.display_option_quote(quote)
            
    async def monitor_portfolio_greeks(self):
        """Calculate and display portfolio-level Greeks."""
        while self.running:
            await asyncio.sleep(30)  # Update every 30 seconds
            
            if not self.latest_quotes:
                continue
                
            print(f"\n{'='*80}")
            print(f"PORTFOLIO GREEKS SUMMARY - {datetime.now().strftime('%H:%M:%S')}")
            print("="*80)
            
            total_delta = 0
            total_gamma = 0
            total_theta = 0
            total_vega = 0
            
            for symbol, quote in self.latest_quotes.items():
                if quote.delta is not None:
                    total_delta += quote.delta
                if quote.gamma is not None:
                    total_gamma += quote.gamma
                if quote.theta is not None:
                    total_theta += quote.theta
                if quote.vega is not None:
                    total_vega += quote.vega
                    
            print(f"Total Delta: {total_delta:+.2f}")
            print(f"Total Gamma: {total_gamma:.2f}")
            print(f"Total Theta: {total_theta:.2f} (${total_theta:.2f}/day)")
            print(f"Total Vega:  {total_vega:.2f}")
            
    async def start_streaming(self):
        """Start streaming options data."""
        print("\nStarting streaming client...")
        await self.streamer.start()
        
        # Set quality of service
        await self.streamer.set_qos(QOSLevel.REAL_TIME)
        
        # Get option symbols for popular underlyings
        underlyings = ["AAPL", "SPY", "MSFT"]
        all_option_symbols = []
        
        for underlying in underlyings:
            symbols = await self.get_option_symbols(underlying, expiry_days=30)
            all_option_symbols.extend(symbols[:5])  # Limit symbols per underlying
            
        if not all_option_symbols:
            print("No option symbols found!")
            return
            
        print(f"\nSubscribing to {len(all_option_symbols)} option contracts...")
        
        # Subscribe to options with all fields including Greeks
        await self.streamer.subscribe_level_one_option(
            symbols=all_option_symbols,
            fields=[f.value for f in LevelOneOptionFields],
            callback=self.on_option_update
        )
        
        print("✓ Successfully subscribed to options data")
        
        # Start portfolio Greeks monitor
        asyncio.create_task(self.monitor_portfolio_greeks())
        
        print("\n" + "="*80)
        print("Options Greeks Monitor Active!")
        print("Monitoring real-time Greeks for option contracts")
        print("Press Ctrl+C to stop")
        print("="*80)
        
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
            import traceback
            traceback.print_exc()
        finally:
            self.running = False
            if self.streamer:
                await self.streamer.stop()
            print("Streaming stopped.")


async def main():
    """Main entry point."""
    monitor = OptionsGreeksMonitor()
    await monitor.run()


if __name__ == "__main__":
    # Enable logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Schwab Options Greeks Monitor")
    print("=============================")
    print()
    print("This monitor displays:")
    print("- Real-time option prices and sizes")
    print("- Full Greeks (Delta, Gamma, Theta, Vega, Rho)")
    print("- Implied volatility")
    print("- Intrinsic and time value")
    print("- P&L scenarios for underlying moves")
    print("- Portfolio-level Greeks aggregation")
    print()
    
    asyncio.run(main())