#!/usr/bin/env python3
"""
Initialize and reset the Schwab Trader credentials database.
This ensures all examples use the same database schema.
"""

import sqlite3
from pathlib import Path

# Database path - unified for all scripts
DB_PATH = Path(__file__).parent / 'schwab_trader.db'

def init_database():
    """Initialize the database with the correct schema."""
    print(f"Initializing database at: {DB_PATH}")
    
    # Remove existing database if it exists
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("Removed existing database")
    
    # Create new database with correct schema
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create credentials table with all required fields
    c.execute('''
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            client_id TEXT,
            client_secret TEXT,
            redirect_uri TEXT,
            trading_client_id TEXT,
            trading_client_secret TEXT,
            market_data_client_id TEXT,
            market_data_client_secret TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create tokens table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY,
            api_type TEXT NOT NULL DEFAULT 'trading',
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            expiry TEXT NOT NULL,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("Database initialized successfully!")
    print("\nTable schema:")
    
    # Show the schema
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("\nCredentials table:")
    c.execute("PRAGMA table_info(credentials)")
    for row in c.fetchall():
        print(f"  {row[1]} {row[2]}")
    
    print("\nTokens table:")
    c.execute("PRAGMA table_info(tokens)")
    for row in c.fetchall():
        print(f"  {row[1]} {row[2]}")
    
    conn.close()

if __name__ == "__main__":
    init_database()