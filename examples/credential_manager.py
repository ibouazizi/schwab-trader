#!/usr/bin/env python3
"""
Unified Credential Manager for Schwab Trader Examples

This module provides a centralized way to manage Schwab API credentials
across all example scripts. It handles:
- Storing credentials in a SQLite database
- Retrieving stored credentials
- Managing OAuth tokens and their expiration
- Providing a consistent interface for all scripts
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Database path - unified for all scripts
DB_PATH = Path(__file__).parent / 'schwab_trader.db'

class CredentialManager:
    """Manages Schwab API credentials and tokens in a unified database."""
    
    def __init__(self, db_path: Path = DB_PATH):
        """Initialize the credential manager with optional custom database path."""
        self.db_path = db_path
        self._ensure_database()
    
    def _ensure_database(self):
        """Create database and tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Create credentials table
        c.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY,
                trading_client_id TEXT NOT NULL,
                trading_client_secret TEXT NOT NULL,
                redirect_uri TEXT NOT NULL,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_credentials(self, client_id: str, client_secret: str, 
                        redirect_uri: str = "https://localhost:8443/callback",
                        api_type: str = "trading") -> bool:
        """
        Save API credentials to the database.
        
        Args:
            client_id: Schwab API client ID
            client_secret: Schwab API client secret
            redirect_uri: OAuth redirect URI
            api_type: Type of API ('trading' or 'market_data')
            
        Returns:
            bool: True if saved successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Clear existing credentials
            c.execute("DELETE FROM credentials")
            
            # Insert new credentials
            if api_type == "trading":
                c.execute("""
                    INSERT INTO credentials 
                    (trading_client_id, trading_client_secret, redirect_uri)
                    VALUES (?, ?, ?)
                """, (client_id, client_secret, redirect_uri))
            else:
                # Update to support market data credentials
                c.execute("""
                    UPDATE credentials 
                    SET market_data_client_id = ?, market_data_client_secret = ?
                    WHERE id = (SELECT MAX(id) FROM credentials)
                """, (client_id, client_secret))
            
            conn.commit()
            conn.close()
            logger.info(f"Saved {api_type} credentials successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            return False
    
    def get_credentials(self, api_type: str = "trading") -> Optional[Dict[str, str]]:
        """
        Retrieve stored credentials from the database.
        
        Args:
            api_type: Type of API ('trading' or 'market_data')
            
        Returns:
            Dict with credentials or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute("SELECT * FROM credentials ORDER BY id DESC LIMIT 1")
            row = c.fetchone()
            conn.close()
            
            if not row:
                return None
            
            if api_type == "trading":
                return {
                    'client_id': row[1],
                    'client_secret': row[2],
                    'redirect_uri': row[3]
                }
            else:
                return {
                    'client_id': row[4],
                    'client_secret': row[5]
                } if row[4] and row[5] else None
                
        except Exception as e:
            logger.error(f"Error retrieving credentials: {e}")
            return None
    
    def save_tokens(self, access_token: str, refresh_token: Optional[str],
                   expires_in: int = 1800, api_type: str = "trading") -> bool:
        """
        Save OAuth tokens to the database.
        
        Args:
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_in: Token validity in seconds (default 30 minutes)
            api_type: Type of API ('trading' or 'market_data')
            
        Returns:
            bool: True if saved successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Calculate expiry time
            expiry = datetime.now() + timedelta(seconds=expires_in)
            
            # Clear existing tokens for this API type
            c.execute("DELETE FROM tokens WHERE api_type = ?", (api_type,))
            
            # Insert new tokens
            c.execute("""
                INSERT INTO tokens (api_type, access_token, refresh_token, expiry)
                VALUES (?, ?, ?, ?)
            """, (api_type, access_token, refresh_token, expiry.isoformat()))
            
            conn.commit()
            conn.close()
            logger.info(f"Saved {api_type} tokens successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving tokens: {e}")
            return False
    
    def get_tokens(self, api_type: str = "trading") -> Optional[Dict[str, any]]:
        """
        Retrieve stored tokens and check their validity.
        
        Args:
            api_type: Type of API ('trading' or 'market_data')
            
        Returns:
            Dict with token info including validity status, or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute("""
                SELECT access_token, refresh_token, expiry 
                FROM tokens 
                WHERE api_type = ? 
                ORDER BY id DESC 
                LIMIT 1
            """, (api_type,))
            
            row = c.fetchone()
            conn.close()
            
            if not row:
                return None
            
            # Parse expiry and check validity
            expiry = datetime.fromisoformat(row[2])
            is_valid = expiry > datetime.now()
            time_remaining = expiry - datetime.now() if is_valid else timedelta(0)
            
            return {
                'access_token': row[0],
                'refresh_token': row[1],
                'expiry': expiry,
                'is_valid': is_valid,
                'expires_in': int(time_remaining.total_seconds())
            }
            
        except Exception as e:
            logger.error(f"Error retrieving tokens: {e}")
            return None
    
    def clear_all(self) -> bool:
        """Clear all credentials and tokens from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute("DELETE FROM credentials")
            c.execute("DELETE FROM tokens")
            
            conn.commit()
            conn.close()
            logger.info("Cleared all credentials and tokens")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            return False
    
    def has_valid_auth(self, api_type: str = "trading") -> bool:
        """
        Check if we have valid credentials and non-expired tokens.
        
        Args:
            api_type: Type of API to check
            
        Returns:
            bool: True if we have valid auth ready to use
        """
        creds = self.get_credentials(api_type)
        if not creds:
            return False
        
        tokens = self.get_tokens(api_type)
        if not tokens:
            return False
        
        return tokens['is_valid']
    
    def get_auth_params(self, api_type: str = "trading") -> Optional[Dict[str, str]]:
        """
        Get all authentication parameters needed to initialize a Schwab client.
        
        Args:
            api_type: Type of API
            
        Returns:
            Dict with all auth parameters or None if not available
        """
        creds = self.get_credentials(api_type)
        if not creds:
            return None
        
        tokens = self.get_tokens(api_type)
        
        result = {
            'client_id': creds['client_id'],
            'client_secret': creds['client_secret']
        }
        
        if 'redirect_uri' in creds:
            result['redirect_uri'] = creds['redirect_uri']
        
        if tokens and tokens['is_valid']:
            result['access_token'] = tokens['access_token']
            result['refresh_token'] = tokens['refresh_token']
            result['token_expiry'] = tokens['expiry']
        
        return result


# Convenience functions for backward compatibility
def get_stored_credentials() -> Optional[Dict[str, str]]:
    """Get stored credentials (backward compatibility wrapper)."""
    manager = CredentialManager()
    return manager.get_credentials()

def save_credentials(client_id: str, client_secret: str, redirect_uri: str) -> bool:
    """Save credentials (backward compatibility wrapper)."""
    manager = CredentialManager()
    return manager.save_credentials(client_id, client_secret, redirect_uri)

def get_valid_tokens() -> Optional[Dict[str, any]]:
    """Get valid tokens if available (backward compatibility wrapper)."""
    manager = CredentialManager()
    tokens = manager.get_tokens()
    return tokens if tokens and tokens['is_valid'] else None