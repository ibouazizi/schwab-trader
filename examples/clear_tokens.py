#!/usr/bin/env python3
"""
Clear stored OAuth tokens to force re-authentication.
Useful when tokens expire or become invalid.
"""

import sqlite3
import os
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / 'schwab_trader.db'

def clear_tokens():
    """Clear all saved tokens from database."""
    if not DB_PATH.exists():
        print("Database not found. Nothing to clear.")
        return
        
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get count of tokens before clearing
        c.execute("SELECT COUNT(*) FROM tokens")
        count = c.fetchone()[0]
        
        if count == 0:
            print("No tokens found in database.")
        else:
            # Clear tokens
            c.execute("DELETE FROM tokens")
            conn.commit()
            print(f"✓ Cleared {count} token(s) from database.")
            print("\nYou will need to re-authenticate the next time you run the portfolio GUI.")
            
        conn.close()
        
    except Exception as e:
        print(f"Error clearing tokens: {e}")

def show_token_info():
    """Show information about stored tokens."""
    if not DB_PATH.exists():
        print("Database not found.")
        return
        
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get token info
        c.execute("SELECT api_type, expiry, created_at FROM tokens")
        tokens = c.fetchall()
        
        if not tokens:
            print("No tokens found in database.")
        else:
            print("\nStored tokens:")
            print("-" * 50)
            for token in tokens:
                api_type, expiry, created_at = token
                print(f"API Type: {api_type}")
                print(f"Created: {created_at}")
                print(f"Expires: {expiry}")
                print("-" * 50)
                
        conn.close()
        
    except Exception as e:
        print(f"Error reading tokens: {e}")

if __name__ == "__main__":
    print("Schwab Token Manager")
    print("=" * 50)
    
    show_token_info()
    
    response = input("\nDo you want to clear all tokens? (y/n): ").lower()
    if response == 'y':
        clear_tokens()
    else:
        print("Tokens not cleared.")