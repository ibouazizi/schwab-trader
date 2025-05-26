#!/usr/bin/env python3
"""
Setup script for Schwab Portfolio GUI credentials
This script helps users properly configure their Schwab API credentials
"""

import os
import sqlite3
import sys
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / 'schwab_trader.db'

def clear_database():
    """Clear all existing credentials and tokens from database"""
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Clear credentials
        c.execute("DELETE FROM credentials")
        print("✓ Cleared existing credentials")
        
        # Clear tokens
        c.execute("DELETE FROM tokens")
        print("✓ Cleared existing tokens")
        
        conn.commit()
        print("\nDatabase cleared successfully!")
        
    except Exception as e:
        print(f"Error clearing database: {e}")
    finally:
        conn.close()

def show_setup_instructions():
    """Show instructions for setting up Schwab API access"""
    print("\n" + "="*60)
    print("SCHWAB API SETUP INSTRUCTIONS")
    print("="*60)
    
    print("\n1. REGISTER YOUR APPLICATION:")
    print("   - Go to https://developer.schwab.com")
    print("   - Sign in with your Schwab account")
    print("   - Create a new application")
    print("   - Note your Client ID and Client Secret")
    
    print("\n2. SET REDIRECT URI:")
    print("   - In your app settings, add this redirect URI:")
    print("   - https://localhost:8443/callback")
    print("   - This must match exactly!")
    
    print("\n3. REQUIRED CREDENTIALS:")
    print("   - Client ID: Your app's client ID")
    print("   - Client Secret: Your app's client secret")
    print("   - Redirect URI: https://localhost:8443/callback")
    
    print("\n4. RUN THE PORTFOLIO GUI:")
    print("   - python examples/portfolio_gui.py")
    print("   - Click 'Connect' and enter your credentials")
    print("   - Follow the OAuth flow to authenticate")
    
    print("\n" + "="*60)
    print("IMPORTANT NOTES:")
    print("="*60)
    print("- The credentials in the database were demo/test values")
    print("- You need real Schwab API credentials to use this app")
    print("- Keep your Client Secret secure and never share it")
    print("- The OAuth token will expire and need refreshing")
    print("\n")

def main():
    """Main setup function"""
    print("Schwab Portfolio GUI - Credential Setup")
    print("-" * 40)
    
    if DB_PATH.exists():
        print(f"\nFound existing database at: {DB_PATH}")
        response = input("\nDo you want to clear existing credentials? (y/n): ").lower()
        
        if response == 'y':
            clear_database()
    else:
        print(f"\nNo existing database found at: {DB_PATH}")
        print("The database will be created when you run the portfolio GUI")
    
    show_setup_instructions()
    
    print("\nSetup complete! You can now run the portfolio GUI with:")
    print("python examples/portfolio_gui.py")

if __name__ == "__main__":
    main()