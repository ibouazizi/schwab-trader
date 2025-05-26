#!/usr/bin/env python3
"""
OAuth Setup Helper for Schwab API

This script helps you complete the OAuth flow and save tokens to the database.
Run this after setup_credentials.py to get your access tokens.
"""

import os
import sys
import webbrowser
from urllib.parse import urlparse, parse_qs

# Add parent directory to path if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schwab import SchwabAuth
from credential_manager import CredentialManager

def main():
    print("=== Schwab OAuth Setup ===\n")
    
    # Initialize credential manager
    cred_manager = CredentialManager()
    
    # Check if we have credentials
    creds = cred_manager.get_credentials("trading")
    if not creds:
        print("ERROR: No credentials found in database.")
        print("Please run setup_credentials.py first to configure your API credentials.")
        sys.exit(1)
    
    print("✓ Found stored credentials")
    print(f"  Client ID: {creds['client_id'][:20]}...")
    print(f"  Redirect URI: {creds['redirect_uri']}")
    
    # Check if we already have valid tokens
    tokens = cred_manager.get_tokens("trading")
    if tokens and tokens['is_valid']:
        print("\n✓ You already have valid access tokens!")
        print(f"  Token expires in: {tokens['expires_in']} seconds")
        print("\nNo need to re-authenticate. Your scripts should work now.")
        return
    
    # Initialize SchwabAuth
    print("\nInitializing OAuth flow...")
    auth = SchwabAuth(
        client_id=creds['client_id'],
        client_secret=creds['client_secret'],
        redirect_uri=creds['redirect_uri']
    )
    
    # Get authorization URL
    auth_url = auth.get_authorization_url()
    
    print("\n" + "="*60)
    print("OAUTH AUTHORIZATION REQUIRED")
    print("="*60)
    print("\n1. Opening your browser to Schwab login page...")
    print("2. Log in with your Schwab credentials")
    print("3. Authorize the application")
    print("4. You'll be redirected to a URL (might show an error page)")
    print("5. Copy the ENTIRE URL from your browser's address bar")
    print("\n" + "="*60)
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Wait for user to complete authorization
    print("\nAfter authorizing, paste the full callback URL here:")
    print("(It should start with your redirect URI and contain a 'code' parameter)")
    print("\nURL: ", end="")
    callback_url = input().strip()
    
    # Parse the authorization code
    try:
        parsed = urlparse(callback_url)
        params = parse_qs(parsed.query)
        
        if 'code' not in params:
            print("\nERROR: No authorization code found in the URL.")
            print("Make sure you copied the entire URL including all parameters.")
            return
        
        auth_code = params['code'][0]
        print(f"\n✓ Authorization code received: {auth_code[:20]}...")
        
    except Exception as e:
        print(f"\nERROR parsing URL: {e}")
        return
    
    # Exchange code for tokens
    print("\nExchanging authorization code for access tokens...")
    try:
        token_data = auth.exchange_code_for_tokens(auth_code)
        
        print("\n✓ Successfully obtained tokens!")
        print(f"  Access Token: {auth.access_token[:30]}...")
        if auth.refresh_token:
            print(f"  Refresh Token: {auth.refresh_token[:30]}...")
        print(f"  Token expires at: {auth.token_expiry}")
        
        # Save tokens to database
        print("\nSaving tokens to database...")
        expires_in = int((auth.token_expiry - datetime.now()).total_seconds())
        
        success = cred_manager.save_tokens(
            access_token=auth.access_token,
            refresh_token=auth.refresh_token,
            expires_in=expires_in
        )
        
        if success:
            print("✓ Tokens saved successfully!")
            print("\nYou can now run any of the example scripts:")
            print("  - python account_overview_direct_fixed.py")
            print("  - python live_quotes.py")
            print("  - python portfolio_manager_demo.py")
            print("  - etc.")
        else:
            print("✗ Failed to save tokens to database")
            
    except Exception as e:
        print(f"\nERROR exchanging code for tokens: {e}")
        print("\nThis might happen if:")
        print("1. The authorization code has expired (they're only valid for a short time)")
        print("2. The code has already been used")
        print("3. There's a mismatch in your redirect URI")
        print("\nPlease try running this script again.")

if __name__ == "__main__":
    from datetime import datetime
    main()