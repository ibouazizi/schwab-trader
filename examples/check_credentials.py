#!/usr/bin/env python3
"""
Quick script to check if credentials are properly stored in the database
"""

import os
import sys

# Add parent directory to path for schwab imports
# Add examples directory to path for credential_manager imports
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_script_dir))
sys.path.insert(0, _script_dir)

from credential_manager import CredentialManager

def main():
    cred_manager = CredentialManager()
    
    print("=== Checking Stored Credentials ===\n")
    
    # Check trading credentials
    creds = cred_manager.get_credentials("trading")
    if creds:
        print("✓ Trading credentials found:")
        print(f"  Client ID: {creds['client_id'][:10]}..." if len(creds['client_id']) > 10 else f"  Client ID: {creds['client_id']}")
        print(f"  Client Secret: {'*' * 10}...")
        print(f"  Redirect URI: {creds['redirect_uri']}")
    else:
        print("✗ No trading credentials found")
        print("  Run setup_credentials.py to configure")
    
    # Check tokens
    print("\n=== Checking Stored Tokens ===\n")
    tokens = cred_manager.get_tokens("trading")
    if tokens:
        print("✓ Tokens found:")
        print(f"  Access Token: {tokens['access_token'][:20]}..." if len(tokens['access_token']) > 20 else f"  Access Token: {tokens['access_token']}")
        print(f"  Token Valid: {tokens['is_valid']}")
        if tokens['is_valid']:
            print(f"  Expires in: {tokens['expires_in']} seconds")
        else:
            print("  Token is expired - needs refresh or re-authentication")
    else:
        print("✗ No tokens found")
        print("  Need to complete OAuth flow")
    
    # Check overall auth status
    print("\n=== Authentication Status ===\n")
    if cred_manager.has_valid_auth():
        print("✓ Ready to authenticate - valid credentials and tokens available")
    else:
        print("✗ Not ready to authenticate - missing credentials or tokens")

if __name__ == "__main__":
    main()