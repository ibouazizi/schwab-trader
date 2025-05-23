#!/usr/bin/env python3
"""
Demo script showing credential and token persistence with Schwab API
This demonstrates how to save and reuse authentication without re-entering credentials
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

# Use a separate test database to not interfere with portfolio_gui.db
TEST_DB = Path("test_auth_persistence.db")

def setup_database():
    """Create the database schema"""
    conn = sqlite3.connect(TEST_DB)
    c = conn.cursor()
    
    # Create credentials table
    c.execute('''
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY,
            trading_client_id TEXT NOT NULL,
            trading_client_secret TEXT NOT NULL,
            redirect_uri TEXT NOT NULL,
            market_data_client_id TEXT,
            market_data_client_secret TEXT
        )
    ''')
    
    # Create tokens table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY,
            api_type TEXT NOT NULL DEFAULT 'trading',
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            expiry TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def save_credentials(client_id, client_secret, redirect_uri):
    """Save API credentials to database"""
    conn = sqlite3.connect(TEST_DB)
    c = conn.cursor()
    
    # Clear existing
    c.execute("DELETE FROM credentials")
    
    # Insert new
    c.execute("""
        INSERT INTO credentials 
        (trading_client_id, trading_client_secret, redirect_uri)
        VALUES (?, ?, ?)
    """, (client_id, client_secret, redirect_uri))
    
    conn.commit()
    conn.close()
    print("✓ Credentials saved to database")

def save_tokens(access_token, refresh_token, expiry_datetime):
    """Save OAuth tokens to database"""
    conn = sqlite3.connect(TEST_DB)
    c = conn.cursor()
    
    # Clear existing
    c.execute("DELETE FROM tokens WHERE api_type='trading'")
    
    # Insert new
    c.execute("""
        INSERT INTO tokens (api_type, access_token, refresh_token, expiry)
        VALUES (?, ?, ?, ?)
    """, ('trading', access_token, refresh_token, expiry_datetime.isoformat()))
    
    conn.commit()
    conn.close()
    print("✓ Tokens saved to database")

def load_saved_auth():
    """Load saved credentials and tokens from database"""
    if not TEST_DB.exists():
        print("✗ No saved authentication found")
        return None
    
    conn = sqlite3.connect(TEST_DB)
    c = conn.cursor()
    
    # Load credentials
    c.execute("SELECT * FROM credentials LIMIT 1")
    creds = c.fetchone()
    
    # Load tokens
    c.execute("SELECT * FROM tokens WHERE api_type='trading' LIMIT 1")
    tokens = c.fetchone()
    
    conn.close()
    
    if not creds:
        print("✗ No saved credentials found")
        return None
    
    auth_data = {
        'client_id': creds[1],
        'client_secret': creds[2],
        'redirect_uri': creds[3],
        'has_tokens': False
    }
    
    if tokens:
        auth_data['has_tokens'] = True
        auth_data['access_token'] = tokens[2]
        auth_data['refresh_token'] = tokens[3]
        
        # Check token validity
        try:
            expiry = datetime.fromisoformat(tokens[4])
            auth_data['token_expiry'] = expiry
            auth_data['token_valid'] = expiry > datetime.now()
            auth_data['expires_in'] = expiry - datetime.now() if auth_data['token_valid'] else None
        except:
            auth_data['token_valid'] = False
    
    return auth_data

def demonstrate_persistence():
    """Demonstrate the credential persistence flow"""
    print("=== Schwab API Credential Persistence Demo ===\n")
    
    # Setup database
    setup_database()
    
    # Simulate first-time setup
    print("1. FIRST TIME SETUP:")
    print("   User enters API credentials...")
    save_credentials(
        client_id="YOUR_CLIENT_ID_HERE",
        client_secret="YOUR_SECRET_HERE",
        redirect_uri="https://localhost:8443/callback"
    )
    
    # Simulate OAuth completion
    print("\n2. OAUTH FLOW COMPLETED:")
    print("   Tokens received from Schwab...")
    # Create a token that expires in 30 minutes (Schwab tokens typically last 30 mins)
    expiry = datetime.now() + timedelta(minutes=30)
    save_tokens(
        access_token="SAMPLE_ACCESS_TOKEN_xyz123",
        refresh_token="SAMPLE_REFRESH_TOKEN_abc456",
        expiry_datetime=expiry
    )
    
    # Demonstrate loading on next run
    print("\n3. NEXT APPLICATION RUN:")
    print("   Loading saved authentication...")
    
    auth_data = load_saved_auth()
    if auth_data:
        print(f"\n   ✓ Found saved credentials:")
        print(f"     Client ID: {auth_data['client_id'][:10]}...")
        print(f"     Redirect URI: {auth_data['redirect_uri']}")
        
        if auth_data['has_tokens']:
            print(f"\n   ✓ Found saved tokens:")
            print(f"     Access Token: {auth_data['access_token'][:20]}...")
            print(f"     Refresh Token: {auth_data['refresh_token'][:20]}...")
            
            if auth_data['token_valid']:
                print(f"\n   ✓ Token is VALID")
                print(f"     Expires in: {auth_data['expires_in']}")
                print("\n   → No re-authentication needed! Can use API immediately.")
            else:
                print(f"\n   ✗ Token is EXPIRED")
                print("     Would attempt refresh using refresh_token...")
                print("     If refresh fails, user must re-authenticate")
    
    print("\n" + "="*50)
    print("This is how the portfolio GUI persists authentication:")
    print("1. Credentials saved once when entered")
    print("2. Tokens saved after OAuth and after each refresh")
    print("3. On startup, loads and validates saved tokens")
    print("4. Only prompts for re-auth when necessary")
    
    # Cleanup
    if TEST_DB.exists():
        os.remove(TEST_DB)
        print(f"\n✓ Cleaned up test database")

if __name__ == "__main__":
    demonstrate_persistence()