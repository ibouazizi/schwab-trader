#!/usr/bin/env python3
"""
Schwab Portfolio GUI with Comprehensive Order Entry

A GUI application for managing and monitoring trading activity with Schwab.
Built using CustomTkinter and integrating with the PortfolioManager.
Now includes support for options and derivatives trading.
"""

import os
import webbrowser
import threading
import time
import logging
import queue
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
from decimal import Decimal
import tkinter as tk
import requests
from tkinter import messagebox, simpledialog, ttk
import customtkinter as ctk
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
import sqlite3
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import Schwab components
try:
    from schwab.auth import SchwabAuth
    from schwab.client import SchwabClient
    from schwab.portfolio import PortfolioManager
    from schwab.order_monitor import OrderMonitor
    from schwab.models.orders import OrderType, OrderSession, OrderDuration, ComplexOrderStrategyType
    from schwab.models.generated.trading_models import AssetType, Instruction, PutCall, ExecutionLeg
    from schwab.streaming import StreamerClient, StreamerService, QOSLevel
except ImportError as e:
    print(f"Error importing Schwab components: {e}")
    print("Please ensure the schwab package is installed and in your Python path")
    exit(1)

# Local SQLite database for storing credentials and tokens
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'portfolio_gui.db')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Debug: Log the DB path
logger.info(f"Database path: {DB_PATH}")
logger.info(f"Database exists: {os.path.exists(DB_PATH)}")

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # "light" or "dark"
ctk.set_default_color_theme("blue")  # "blue", "green", or "dark-blue"

# Default symbol list for autocomplete
DEFAULT_SYMBOL_LIST = ["AAPL", "AMD", "AMZN", "AVGO", "GOOGL", "META", "MSFT", "NFLX", "NVDA", "QCOM", "TSLA"]

# Option chain display columns
OPTION_CHAIN_COLUMNS = [
    "Symbol", "Strike", "Bid", "Ask", "Last", "Volume", "Open Interest", 
    "IV", "Delta", "Theta", "Gamma", "Vega"
]

def check_and_upgrade_db():
    """Check for and upgrade the database schema if needed."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if the credentials table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='credentials'")
        if not c.fetchone():
            c.execute('''
                CREATE TABLE credentials (
                    id INTEGER PRIMARY KEY,
                    trading_client_id TEXT NOT NULL,
                    trading_client_secret TEXT NOT NULL,
                    redirect_uri TEXT NOT NULL,
                    market_data_client_id TEXT,
                    market_data_client_secret TEXT
                )
            ''')
        
        # Check if the tokens table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tokens'")
        if not c.fetchone():
            c.execute('''
                CREATE TABLE tokens (
                    id INTEGER PRIMARY KEY,
                    api_type TEXT NOT NULL DEFAULT 'trading',
                    access_token TEXT NOT NULL,
                    refresh_token TEXT,
                    expiry TEXT NOT NULL
                )
            ''')
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Database upgrade error: {e}")
        raise

class ComprehensiveOrderEntryDialog(ctk.CTkToplevel):
    """Comprehensive order entry dialog with support for all order types including options."""
    
    def __init__(self, parent, client: SchwabClient, accounts: List[str], on_submit=None):
        super().__init__(parent)
        
        self.parent = parent  # Store parent reference
        self.client = client
        self.accounts = accounts
        self.on_submit = on_submit
        self.option_chain_data = None
        self.selected_option = None
        
        # Log client info for debugging
        logger.info(f"ComprehensiveOrderEntryDialog initialized")
        logger.info(f"Client type: {type(self.client)}")
        logger.info(f"Has get_option_chain: {hasattr(self.client, 'get_option_chain')}")
        logger.info(f"Has get_option_expiration_chain: {hasattr(self.client, 'get_option_expiration_chain')}")
        
        # Window configuration
        self.title("Advanced Order Entry")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        
        # Create main layout
        self.create_main_layout()
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Center the window
        self.center_window()
    
    def center_window(self):
        """Center the window on screen."""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def create_main_layout(self):
        """Create the main layout with tabs."""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Advanced Order Entry",
            font=("Roboto", 24, "bold")
        )
        title_label.pack(pady=(10, 20))
        
        # Create tabview
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True)
        
        # Add tabs
        self.tab_equity = self.tabview.add("Equity")
        self.tab_options = self.tabview.add("Options")
        self.tab_spreads = self.tabview.add("Spreads")
        self.tab_conditional = self.tabview.add("Conditional")
        
        # Create content for each tab
        self.create_equity_tab()
        self.create_options_tab()
        self.create_spreads_tab()
        self.create_conditional_tab()
        
        # Bottom buttons frame
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Preview and submit buttons
        self.preview_button = ctk.CTkButton(
            button_frame,
            text="Preview Order",
            command=self.preview_order,
            width=150
        )
        self.preview_button.pack(side="left", padx=5)
        
        self.submit_button = ctk.CTkButton(
            button_frame,
            text="Submit Order",
            command=self.submit_order,
            state="disabled",
            width=150
        )
        self.submit_button.pack(side="left", padx=5)
        
        # Cancel button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            width=150
        )
        cancel_button.pack(side="right", padx=5)
    
    def create_equity_tab(self):
        """Create equity order entry tab."""
        # Main container with scrollbar
        container = ctk.CTkScrollableFrame(self.tab_equity)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Account selection
        account_frame = ctk.CTkFrame(container)
        account_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(account_frame, text="Account:", font=("Roboto", 14)).pack(side="left", padx=(0, 10))
        self.account_var = ctk.StringVar(value=self.accounts[0] if self.accounts else "")
        self.account_menu = ctk.CTkOptionMenu(
            account_frame,
            values=self.accounts,
            variable=self.account_var,
            width=200
        )
        self.account_menu.pack(side="left")
        
        # Symbol entry with search
        symbol_frame = ctk.CTkFrame(container)
        symbol_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(symbol_frame, text="Symbol:", font=("Roboto", 14)).pack(side="left", padx=(0, 10))
        self.symbol_entry = ctk.CTkEntry(symbol_frame, width=150)
        self.symbol_entry.pack(side="left", padx=(0, 10))
        
        search_button = ctk.CTkButton(
            symbol_frame,
            text="Search",
            command=self.search_symbol,
            width=80
        )
        search_button.pack(side="left")
        
        # Quote display
        self.quote_frame = ctk.CTkFrame(container)
        self.quote_frame.pack(fill="x", pady=(0, 10))
        self.quote_label = ctk.CTkLabel(self.quote_frame, text="")
        self.quote_label.pack()
        
        # Order details frame
        details_frame = ctk.CTkFrame(container)
        details_frame.pack(fill="x", pady=(0, 10))
        
        # Left column
        left_col = ctk.CTkFrame(details_frame)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Quantity
        ctk.CTkLabel(left_col, text="Quantity:", font=("Roboto", 12)).pack(anchor="w", pady=(0, 5))
        self.quantity_entry = ctk.CTkEntry(left_col, width=150)
        self.quantity_entry.pack(anchor="w", pady=(0, 10))
        
        # Order Type
        ctk.CTkLabel(left_col, text="Order Type:", font=("Roboto", 12)).pack(anchor="w", pady=(0, 5))
        self.order_type_var = ctk.StringVar(value="MARKET")
        order_types = ["MARKET", "LIMIT", "STOP", "STOP_LIMIT", "TRAILING_STOP", "MARKET_ON_CLOSE", "LIMIT_ON_CLOSE"]
        self.order_type_menu = ctk.CTkOptionMenu(
            left_col,
            values=order_types,
            variable=self.order_type_var,
            command=self.on_order_type_change,
            width=150
        )
        self.order_type_menu.pack(anchor="w", pady=(0, 10))
        
        # Instruction
        ctk.CTkLabel(left_col, text="Instruction:", font=("Roboto", 12)).pack(anchor="w", pady=(0, 5))
        self.instruction_var = ctk.StringVar(value="BUY")
        instructions = ["BUY", "SELL", "BUY_TO_COVER", "SELL_SHORT"]
        self.instruction_menu = ctk.CTkOptionMenu(
            left_col,
            values=instructions,
            variable=self.instruction_var,
            width=150
        )
        self.instruction_menu.pack(anchor="w", pady=(0, 10))
        
        # Right column
        right_col = ctk.CTkFrame(details_frame)
        right_col.pack(side="right", fill="both", expand=True)
        
        # Price fields (shown/hidden based on order type)
        self.price_frame = ctk.CTkFrame(right_col)
        self.price_frame.pack(fill="x")
        
        # Limit price
        self.limit_price_label = ctk.CTkLabel(self.price_frame, text="Limit Price:", font=("Roboto", 12))
        self.limit_price_label.pack(anchor="w", pady=(0, 5))
        self.limit_price_entry = ctk.CTkEntry(self.price_frame, width=150)
        self.limit_price_entry.pack(anchor="w", pady=(0, 10))
        
        # Stop price
        self.stop_price_label = ctk.CTkLabel(self.price_frame, text="Stop Price:", font=("Roboto", 12))
        self.stop_price_label.pack(anchor="w", pady=(0, 5))
        self.stop_price_entry = ctk.CTkEntry(self.price_frame, width=150)
        self.stop_price_entry.pack(anchor="w", pady=(0, 10))
        
        # Trailing amount
        self.trail_amount_label = ctk.CTkLabel(self.price_frame, text="Trail Amount:", font=("Roboto", 12))
        self.trail_amount_label.pack(anchor="w", pady=(0, 5))
        self.trail_amount_entry = ctk.CTkEntry(self.price_frame, width=150)
        self.trail_amount_entry.pack(anchor="w", pady=(0, 10))
        
        # Duration
        ctk.CTkLabel(right_col, text="Duration:", font=("Roboto", 12)).pack(anchor="w", pady=(0, 5))
        self.duration_var = ctk.StringVar(value="DAY")
        durations = ["DAY", "GOOD_TILL_CANCEL", "FILL_OR_KILL", "IMMEDIATE_OR_CANCEL"]
        self.duration_menu = ctk.CTkOptionMenu(
            right_col,
            values=durations,
            variable=self.duration_var,
            width=150
        )
        self.duration_menu.pack(anchor="w", pady=(0, 10))
        
        # Session
        ctk.CTkLabel(right_col, text="Session:", font=("Roboto", 12)).pack(anchor="w", pady=(0, 5))
        self.session_var = ctk.StringVar(value="NORMAL")
        sessions = ["NORMAL", "SEAMLESS"]
        self.session_menu = ctk.CTkOptionMenu(
            right_col,
            values=sessions,
            variable=self.session_var,
            width=150
        )
        self.session_menu.pack(anchor="w", pady=(0, 10))
        
        # Advanced options
        advanced_frame = ctk.CTkFrame(container)
        advanced_frame.pack(fill="x", pady=(10, 0))
        
        self.all_or_none_var = ctk.BooleanVar(value=False)
        self.all_or_none_check = ctk.CTkCheckBox(
            advanced_frame,
            text="All or None",
            variable=self.all_or_none_var
        )
        self.all_or_none_check.pack(side="left", padx=(0, 20))
        
        # Update price fields based on order type
        self.on_order_type_change()
    
    def create_options_tab(self):
        """Create options order entry tab."""
        # Main container
        container = ctk.CTkFrame(self.tab_options)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top section - Symbol and chain lookup
        top_frame = ctk.CTkFrame(container)
        top_frame.pack(fill="x", pady=(0, 10))
        
        # Symbol entry
        symbol_frame = ctk.CTkFrame(top_frame)
        symbol_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(symbol_frame, text="Underlying Symbol:", font=("Roboto", 14)).pack(side="left", padx=(0, 10))
        self.option_symbol_entry = ctk.CTkEntry(symbol_frame, width=150)
        self.option_symbol_entry.pack(side="left", padx=(0, 10))
        self.option_symbol_entry.bind("<Return>", lambda e: self.load_option_chain())
        
        # Expiration date selection
        ctk.CTkLabel(symbol_frame, text="Expiration:", font=("Roboto", 14)).pack(side="left", padx=(10, 10))
        self.expiration_var = ctk.StringVar()
        self.expiration_menu = ctk.CTkOptionMenu(
            symbol_frame,
            values=[],
            variable=self.expiration_var,
            width=150,
            command=self.on_expiration_change
        )
        self.expiration_menu.pack(side="left", padx=(0, 10))
        
        # Option type
        ctk.CTkLabel(symbol_frame, text="Type:", font=("Roboto", 14)).pack(side="left", padx=(10, 10))
        self.option_type_var = ctk.StringVar(value="CALL")
        option_types = ["CALL", "PUT", "BOTH"]
        self.option_type_menu = ctk.CTkOptionMenu(
            symbol_frame,
            values=option_types,
            variable=self.option_type_var,
            width=100,
            command=self.on_option_type_change
        )
        self.option_type_menu.pack(side="left", padx=(0, 10))
        
        # Load chain button
        load_chain_button = ctk.CTkButton(
            symbol_frame,
            text="Load Option Chain",
            command=self.load_option_chain,
            width=150
        )
        load_chain_button.pack(side="left", padx=(10, 0))
        
        # Refresh button
        refresh_button = ctk.CTkButton(
            symbol_frame,
            text="↻",
            command=self.refresh_option_chain,
            width=40,
            font=("Roboto", 16)
        )
        refresh_button.pack(side="left", padx=(5, 0))
        
        # Option chain display
        chain_frame = ctk.CTkFrame(container)
        chain_frame.pack(fill="both", expand=True, pady=(10, 10))
        
        # Create treeview for option chain
        tree_frame = ctk.CTkFrame(chain_frame)
        tree_frame.pack(fill="both", expand=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        self.option_tree = ttk.Treeview(
            tree_frame,
            columns=OPTION_CHAIN_COLUMNS,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.option_tree.yview)
        hsb.config(command=self.option_tree.xview)
        
        # Configure columns
        for col in OPTION_CHAIN_COLUMNS:
            self.option_tree.heading(col, text=col)
            self.option_tree.column(col, width=100)
        
        # Pack treeview and scrollbars
        self.option_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind selection event
        self.option_tree.bind("<<TreeviewSelect>>", self.on_option_select)
        
        # Order details section
        order_frame = ctk.CTkFrame(container)
        order_frame.pack(fill="x", pady=(10, 0))
        
        # Selected option display
        self.selected_option_label = ctk.CTkLabel(
            order_frame,
            text="No option selected",
            font=("Roboto", 14, "bold")
        )
        self.selected_option_label.pack(pady=(0, 10))
        
        # Order details
        details_frame = ctk.CTkFrame(order_frame)
        details_frame.pack(fill="x")
        
        # Quantity
        ctk.CTkLabel(details_frame, text="Contracts:", font=("Roboto", 12)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.option_quantity_entry = ctk.CTkEntry(details_frame, width=100)
        self.option_quantity_entry.grid(row=0, column=1, padx=(0, 20))
        
        # Instruction
        ctk.CTkLabel(details_frame, text="Instruction:", font=("Roboto", 12)).grid(row=0, column=2, sticky="w", padx=(0, 10))
        self.option_instruction_var = ctk.StringVar(value="BUY_TO_OPEN")
        option_instructions = ["BUY_TO_OPEN", "BUY_TO_CLOSE", "SELL_TO_OPEN", "SELL_TO_CLOSE"]
        self.option_instruction_menu = ctk.CTkOptionMenu(
            details_frame,
            values=option_instructions,
            variable=self.option_instruction_var,
            width=150
        )
        self.option_instruction_menu.grid(row=0, column=3, padx=(0, 20))
        
        # Order type
        ctk.CTkLabel(details_frame, text="Order Type:", font=("Roboto", 12)).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(10, 0))
        self.option_order_type_var = ctk.StringVar(value="LIMIT")
        option_order_types = ["MARKET", "LIMIT", "STOP", "STOP_LIMIT", "NET_DEBIT", "NET_CREDIT"]
        self.option_order_type_menu = ctk.CTkOptionMenu(
            details_frame,
            values=option_order_types,
            variable=self.option_order_type_var,
            command=self.on_option_order_type_change,
            width=150
        )
        self.option_order_type_menu.grid(row=1, column=1, pady=(10, 0))
        
        # Price
        self.option_price_label = ctk.CTkLabel(details_frame, text="Limit Price:", font=("Roboto", 12))
        self.option_price_label.grid(row=1, column=2, sticky="w", padx=(0, 10), pady=(10, 0))
        self.option_price_entry = ctk.CTkEntry(details_frame, width=100)
        self.option_price_entry.grid(row=1, column=3, pady=(10, 0))
    
    def create_spreads_tab(self):
        """Create spreads order entry tab."""
        container = ctk.CTkFrame(self.tab_spreads)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Strategy selection
        strategy_frame = ctk.CTkFrame(container)
        strategy_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(strategy_frame, text="Strategy:", font=("Roboto", 14)).pack(side="left", padx=(0, 10))
        self.strategy_var = ctk.StringVar(value="VERTICAL")
        strategies = [
            "VERTICAL", "CALENDAR", "DIAGONAL", "STRADDLE", "STRANGLE",
            "BUTTERFLY", "CONDOR", "IRON_CONDOR", "COLLAR_WITH_STOCK"
        ]
        self.strategy_menu = ctk.CTkOptionMenu(
            strategy_frame,
            values=strategies,
            variable=self.strategy_var,
            command=self.on_strategy_change,
            width=200
        )
        self.strategy_menu.pack(side="left")
        
        # Strategy description
        self.strategy_desc_label = ctk.CTkLabel(
            container,
            text="Select a strategy to see its description",
            font=("Roboto", 12),
            wraplength=600
        )
        self.strategy_desc_label.pack(pady=(0, 20))
        
        # Legs container
        self.legs_frame = ctk.CTkScrollableFrame(container)
        self.legs_frame.pack(fill="both", expand=True)
        
        # Initialize with vertical spread
        self.on_strategy_change("VERTICAL")
    
    def create_conditional_tab(self):
        """Create conditional order entry tab."""
        container = ctk.CTkFrame(self.tab_conditional)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Order type selection
        order_type_frame = ctk.CTkFrame(container)
        order_type_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(order_type_frame, text="Conditional Type:", font=("Roboto", 14)).pack(side="left", padx=(0, 10))
        self.conditional_type_var = ctk.StringVar(value="ONE_CANCELS_OTHER")
        conditional_types = ["ONE_CANCELS_OTHER", "ONE_TRIGGERS_OTHER", "BRACKET"]
        self.conditional_type_menu = ctk.CTkOptionMenu(
            order_type_frame,
            values=conditional_types,
            variable=self.conditional_type_var,
            command=self.on_conditional_type_change,
            width=200
        )
        self.conditional_type_menu.pack(side="left")
        
        # Conditional orders container
        self.conditional_frame = ctk.CTkScrollableFrame(container)
        self.conditional_frame.pack(fill="both", expand=True)
        
        # Initialize with OCO
        self.on_conditional_type_change("ONE_CANCELS_OTHER")
    
    def on_order_type_change(self, *args):
        """Handle order type change in equity tab."""
        order_type = self.order_type_var.get()
        
        # Hide all price fields first
        self.limit_price_label.pack_forget()
        self.limit_price_entry.pack_forget()
        self.stop_price_label.pack_forget()
        self.stop_price_entry.pack_forget()
        self.trail_amount_label.pack_forget()
        self.trail_amount_entry.pack_forget()
        
        # Show relevant fields
        if order_type in ["LIMIT", "LIMIT_ON_CLOSE"]:
            self.limit_price_label.pack(anchor="w", pady=(0, 5))
            self.limit_price_entry.pack(anchor="w", pady=(0, 10))
        elif order_type == "STOP":
            self.stop_price_label.pack(anchor="w", pady=(0, 5))
            self.stop_price_entry.pack(anchor="w", pady=(0, 10))
        elif order_type == "STOP_LIMIT":
            self.limit_price_label.pack(anchor="w", pady=(0, 5))
            self.limit_price_entry.pack(anchor="w", pady=(0, 10))
            self.stop_price_label.pack(anchor="w", pady=(0, 5))
            self.stop_price_entry.pack(anchor="w", pady=(0, 10))
        elif order_type == "TRAILING_STOP":
            self.trail_amount_label.pack(anchor="w", pady=(0, 5))
            self.trail_amount_entry.pack(anchor="w", pady=(0, 10))
    
    def on_option_order_type_change(self, *args):
        """Handle order type change in options tab."""
        order_type = self.option_order_type_var.get()
        
        if order_type == "MARKET":
            self.option_price_label.configure(text="Market Order")
            self.option_price_entry.configure(state="disabled")
        elif order_type in ["LIMIT", "STOP_LIMIT"]:
            self.option_price_label.configure(text="Limit Price:")
            self.option_price_entry.configure(state="normal")
        elif order_type in ["NET_DEBIT", "NET_CREDIT"]:
            self.option_price_label.configure(text="Net Price:")
            self.option_price_entry.configure(state="normal")
    
    def on_strategy_change(self, strategy):
        """Handle strategy change in spreads tab."""
        # Clear existing legs
        for widget in self.legs_frame.winfo_children():
            widget.destroy()
        
        # Update description
        descriptions = {
            "VERTICAL": "Buy and sell options of the same type with same expiration but different strikes",
            "CALENDAR": "Buy and sell options of the same type and strike with different expirations",
            "DIAGONAL": "Buy and sell options of the same type with different strikes and expirations",
            "STRADDLE": "Buy or sell both a call and put at the same strike and expiration",
            "STRANGLE": "Buy or sell both a call and put at different strikes with same expiration",
            "BUTTERFLY": "Combination of bull and bear spreads with three different strikes",
            "CONDOR": "Similar to butterfly but with four different strikes",
            "IRON_CONDOR": "Sell out-of-money call and put spreads",
            "COLLAR_WITH_STOCK": "Own stock, buy protective put, sell covered call"
        }
        
        self.strategy_desc_label.configure(text=descriptions.get(strategy, ""))
        
        # Create appropriate leg inputs based on strategy
        if strategy == "VERTICAL":
            self.create_vertical_spread_inputs()
        elif strategy == "CALENDAR":
            self.create_calendar_spread_inputs()
        elif strategy == "STRADDLE":
            self.create_straddle_inputs()
        # Add more strategies as needed
    
    def create_vertical_spread_inputs(self):
        """Create input fields for vertical spread."""
        # Title
        ctk.CTkLabel(
            self.legs_frame,
            text="Vertical Spread Setup",
            font=("Roboto", 16, "bold")
        ).pack(pady=(0, 10))
        
        # Underlying symbol
        symbol_frame = ctk.CTkFrame(self.legs_frame)
        symbol_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(symbol_frame, text="Underlying:", font=("Roboto", 12)).pack(side="left", padx=(0, 10))
        self.spread_symbol_entry = ctk.CTkEntry(symbol_frame, width=150)
        self.spread_symbol_entry.pack(side="left")
        
        # Option type
        type_frame = ctk.CTkFrame(self.legs_frame)
        type_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(type_frame, text="Option Type:", font=("Roboto", 12)).pack(side="left", padx=(0, 10))
        self.spread_type_var = ctk.StringVar(value="CALL")
        ctk.CTkOptionMenu(
            type_frame,
            values=["CALL", "PUT"],
            variable=self.spread_type_var,
            width=100
        ).pack(side="left")
        
        # Expiration
        exp_frame = ctk.CTkFrame(self.legs_frame)
        exp_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(exp_frame, text="Expiration:", font=("Roboto", 12)).pack(side="left", padx=(0, 10))
        self.spread_exp_entry = ctk.CTkEntry(exp_frame, width=150, placeholder_text="YYYY-MM-DD")
        self.spread_exp_entry.pack(side="left")
        
        # Leg 1 - Buy
        leg1_frame = ctk.CTkFrame(self.legs_frame)
        leg1_frame.pack(fill="x", pady=(10, 5))
        
        ctk.CTkLabel(leg1_frame, text="Buy Strike:", font=("Roboto", 12, "bold")).pack(side="left", padx=(0, 10))
        self.buy_strike_entry = ctk.CTkEntry(leg1_frame, width=100)
        self.buy_strike_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(leg1_frame, text="Contracts:", font=("Roboto", 12)).pack(side="left", padx=(0, 10))
        self.buy_contracts_entry = ctk.CTkEntry(leg1_frame, width=80)
        self.buy_contracts_entry.pack(side="left")
        
        # Leg 2 - Sell
        leg2_frame = ctk.CTkFrame(self.legs_frame)
        leg2_frame.pack(fill="x", pady=(5, 10))
        
        ctk.CTkLabel(leg2_frame, text="Sell Strike:", font=("Roboto", 12, "bold")).pack(side="left", padx=(0, 10))
        self.sell_strike_entry = ctk.CTkEntry(leg2_frame, width=100)
        self.sell_strike_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(leg2_frame, text="Contracts:", font=("Roboto", 12)).pack(side="left", padx=(0, 10))
        self.sell_contracts_entry = ctk.CTkEntry(leg2_frame, width=80)
        self.sell_contracts_entry.pack(side="left")
        
        # Net price
        price_frame = ctk.CTkFrame(self.legs_frame)
        price_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkLabel(price_frame, text="Net Debit/Credit:", font=("Roboto", 12)).pack(side="left", padx=(0, 10))
        self.spread_price_entry = ctk.CTkEntry(price_frame, width=100)
        self.spread_price_entry.pack(side="left")
    
    def create_calendar_spread_inputs(self):
        """Create input fields for calendar spread."""
        # Similar structure but with two expiration dates
        pass
    
    def create_straddle_inputs(self):
        """Create input fields for straddle."""
        # Buy/sell both call and put at same strike
        pass
    
    def on_conditional_type_change(self, cond_type):
        """Handle conditional order type change."""
        # Clear existing widgets
        for widget in self.conditional_frame.winfo_children():
            widget.destroy()
        
        if cond_type == "ONE_CANCELS_OTHER":
            self.create_oco_inputs()
        elif cond_type == "ONE_TRIGGERS_OTHER":
            self.create_oto_inputs()
        elif cond_type == "BRACKET":
            self.create_bracket_inputs()
    
    def create_oco_inputs(self):
        """Create OCO order inputs."""
        ctk.CTkLabel(
            self.conditional_frame,
            text="One Cancels Other (OCO) Order",
            font=("Roboto", 16, "bold")
        ).pack(pady=(0, 10))
        
        ctk.CTkLabel(
            self.conditional_frame,
            text="Create two orders - when one fills, the other is automatically cancelled",
            font=("Roboto", 12)
        ).pack(pady=(0, 20))
        
        # Order 1
        order1_label = ctk.CTkLabel(
            self.conditional_frame,
            text="Order 1 - Limit Order",
            font=("Roboto", 14, "bold")
        )
        order1_label.pack(pady=(10, 5))
        
        # Order 2
        order2_label = ctk.CTkLabel(
            self.conditional_frame,
            text="Order 2 - Stop Order",
            font=("Roboto", 14, "bold")
        )
        order2_label.pack(pady=(20, 5))
    
    def create_oto_inputs(self):
        """Create OTO order inputs."""
        pass
    
    def create_bracket_inputs(self):
        """Create bracket order inputs."""
        pass
    
    def search_symbol(self):
        """Search for symbol and get quote."""
        symbol = self.symbol_entry.get().upper()
        if not symbol:
            return
        
        try:
            logger.info(f"Getting quote for {symbol}")
            # Get quote
            quotes = self.client.get_quotes([symbol])
            logger.info(f"Quote response type: {type(quotes)}")
            
            # QuoteResponse now has __contains__ method
            if symbol in quotes:
                quote_data = quotes[symbol]
                logger.info(f"Quote data type: {type(quote_data)}")
                
                # Access quote data from the nested structure
                if hasattr(quote_data, 'quote') and quote_data.quote:
                    quote = quote_data.quote
                    last_price = getattr(quote, 'lastPrice', 0)
                    bid_price = getattr(quote, 'bidPrice', 0)
                    ask_price = getattr(quote, 'askPrice', 0)
                    volume = getattr(quote, 'totalVolume', 0)
                    
                    # Also try to get regular market data
                    if hasattr(quote_data, 'regular') and quote_data.regular:
                        regular = quote_data.regular
                        last_price = last_price or getattr(regular, 'regularMarketLastPrice', 0)
                        volume = volume or getattr(regular, 'regularMarketVolume', 0)
                    
                    quote_text = f"{symbol}: Last: ${last_price:.2f} "
                    quote_text += f"Bid: ${bid_price:.2f} Ask: ${ask_price:.2f} "
                    quote_text += f"Volume: {volume:,}"
                    self.quote_label.configure(text=quote_text)
                else:
                    self.quote_label.configure(text=f"{symbol}: No quote data available")
            else:
                self.quote_label.configure(text="Symbol not found")
                logger.warning(f"Symbol {symbol} not in response. Available symbols: {list(quotes.keys())}")
        except Exception as e:
            logger.error(f"Error getting quote: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.quote_label.configure(text="Error getting quote")
    
    def load_option_chain(self):
        """Load option chain for the selected symbol."""
        symbol = self.option_symbol_entry.get().upper()
        if not symbol:
            messagebox.showwarning("Input Error", "Please enter an underlying symbol")
            return
        
        # Update status
        self.selected_option_label.configure(text=f"Loading options for {symbol}...")
        self.update_idletasks()  # Force UI update
        
        try:
            # Get option chain from API
            # Get expiration dates
            expirations = self._get_option_expirations(symbol)
            
            if not expirations:
                self.selected_option_label.configure(text=f"No options available for {symbol}")
                messagebox.showwarning(
                    "No Options", 
                    f"No option expirations found for {symbol}. This may be a non-optionable security."
                )
                return
                
            self.expiration_menu.configure(values=expirations)
            if expirations:
                self.expiration_var.set(expirations[0])
            
            # Load option chain data
            self._load_option_chain_data(symbol, expirations[0] if expirations else None)
            
            # Subscribe to real-time option quotes if streaming is available
            if hasattr(self.parent, 'streamer_client') and self.parent.streamer_client:
                self._subscribe_to_option_quotes()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error loading option chain: {e}")
            logger.error(f"Response content: {e.response.text if hasattr(e, 'response') else 'No response'}")
            self.selected_option_label.configure(text="Error loading option chain")
            
            if hasattr(e, 'response') and e.response.status_code == 400:
                messagebox.showerror("Error", f"Invalid symbol or request: {symbol}")
            elif hasattr(e, 'response') and e.response.status_code == 401:
                messagebox.showerror("Error", "Authentication failed. Please reconnect to Schwab.")
            else:
                messagebox.showerror("Error", f"Failed to load option chain: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading option chain: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.selected_option_label.configure(text="Error loading option chain")
            messagebox.showerror("Error", f"Failed to load option chain: {str(e)}")
    
    def _get_option_expirations(self, symbol: str) -> List[str]:
        """Get available option expiration dates."""
        try:
            # Get option expirations from the API
            if hasattr(self.client, 'get_option_expiration_chain'):
                logger.info(f"Calling get_option_expiration_chain for {symbol}")
                response = self.client.get_option_expiration_chain(symbol)
                logger.info(f"Option expiration response type: {type(response)}")
                logger.info(f"Option expiration response for {symbol}: {response}")
                
                # Check different possible response formats
                if isinstance(response, dict):
                    # Log all keys for debugging
                    logger.info(f"Response keys: {list(response.keys())}")
                    
                    # Check for error responses
                    if 'errors' in response or 'error' in response:
                        error_msg = response.get('errors', response.get('error', 'Unknown error'))
                        logger.error(f"API returned error: {error_msg}")
                        messagebox.showerror("API Error", f"Failed to get options for {symbol}: {error_msg}")
                        return []
                    
                    # Try different keys that might contain expiration data
                    if 'expirationList' in response:
                        exp_list = response['expirationList']
                        logger.info(f"Found expirationList with {len(exp_list)} items")
                        
                        # Handle different formats of expiration data
                        result = []
                        for exp in exp_list:
                            if isinstance(exp, dict):
                                # Extract date from dict format
                                exp_date = exp.get('expirationDate', exp.get('date', str(exp)))
                                result.append(exp_date)
                            else:
                                # Direct string format
                                result.append(str(exp))
                        
                        logger.info(f"Processed expiration dates: {result[:5]}...")  # Log first 5
                        return sorted(result)
                        
                    elif 'expirationDates' in response:
                        return sorted(response['expirationDates'])
                    elif 'data' in response and isinstance(response['data'], dict):
                        if 'expirationList' in response['data']:
                            return sorted(response['data']['expirationList'])
                    else:
                        logger.warning(f"Unexpected response format. Full response: {json.dumps(response, indent=2)}")
                        
                else:
                    logger.error(f"Response is not a dict, it's: {type(response)}")
                    
                return []
            else:
                # If method not available, return empty list
                logger.warning("Option expiration chain API not implemented")
                logger.warning(f"Client type: {type(self.client)}")
                logger.warning(f"Client methods: {[m for m in dir(self.client) if not m.startswith('_')]}")
                return []
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error getting option expirations: {e}")
            if hasattr(e, 'response'):
                logger.error(f"Status code: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Failed to get option expirations: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _load_option_chain_data(self, symbol: str, expiration: str):
        """Load option chain data for specific expiration."""
        # Clear existing data
        for item in self.option_tree.get_children():
            self.option_tree.delete(item)
        
        if not expiration:
            return
            
        try:
            option_type = self.option_type_var.get()
            
            # Get option chain from API
            if hasattr(self.client, 'get_option_chain'):
                # Convert option type to API format
                contract_type = None
                if option_type == "CALL":
                    contract_type = "CALL"
                elif option_type == "PUT":
                    contract_type = "PUT"
                else:
                    contract_type = "ALL"
                
                # API call to get option chain for symbol
                response = self.client.get_option_chain(
                    symbol=symbol,
                    contract_type=contract_type,
                    include_underlying_quote=True,
                    strike_count=20,  # Get 20 strikes around ATM
                    option_detail_flag=True
                )
                
                # Parse the response
                self.option_symbols = []
                
                # Handle different response structures
                if 'callExpDateMap' in response or 'putExpDateMap' in response:
                    # Process calls
                    if option_type in ["CALL", "BOTH"] and 'callExpDateMap' in response:
                        for exp_date, strikes in response['callExpDateMap'].items():
                            if expiration and exp_date.startswith(expiration):
                                for strike, option_list in strikes.items():
                                    for option in option_list:
                                        self._add_option_to_tree(option)
                    
                    # Process puts
                    if option_type in ["PUT", "BOTH"] and 'putExpDateMap' in response:
                        for exp_date, strikes in response['putExpDateMap'].items():
                            if expiration and exp_date.startswith(expiration):
                                for strike, option_list in strikes.items():
                                    for option in option_list:
                                        self._add_option_to_tree(option)
                else:
                    logger.warning(f"Unexpected option chain response structure: {response.keys()}")
                    messagebox.showwarning(
                        "No Data",
                        f"No option data found for {symbol} with expiration {expiration}"
                    )
                
                # Update status
                if self.option_symbols:
                    self.selected_option_label.configure(
                        text=f"Loaded {len(self.option_symbols)} options for {symbol}"
                    )
                else:
                    self.selected_option_label.configure(
                        text=f"No options found for {symbol}"
                    )
                    
            else:
                # API not implemented yet
                messagebox.showwarning(
                    "Not Implemented", 
                    "Option chain API is not yet implemented. Please check for updates."
                )
                
        except Exception as e:
            logger.error(f"Failed to load option chain: {e}")
            messagebox.showerror("Error", f"Failed to load option chain: {str(e)}")
    
    def _add_option_to_tree(self, option: Dict[str, Any]):
        """Add an option to the tree view."""
        try:
            # Extract option data with safe defaults
            symbol = option.get('symbol', '')
            strike_price = float(option.get('strikePrice', 0))
            bid = float(option.get('bid', 0))
            ask = float(option.get('ask', 0))
            last = float(option.get('last', 0))
            volume = int(option.get('totalVolume', 0))
            open_interest = int(option.get('openInterest', 0))
            
            # Greeks might be nested
            greeks = option.get('greeks', {})
            if isinstance(greeks, dict):
                implied_vol = float(greeks.get('volatility', 0))
                delta = float(greeks.get('delta', 0))
                theta = float(greeks.get('theta', 0))
                gamma = float(greeks.get('gamma', 0))
                vega = float(greeks.get('vega', 0))
            else:
                implied_vol = float(option.get('volatility', 0))
                delta = float(option.get('delta', 0))
                theta = float(option.get('theta', 0))
                gamma = float(option.get('gamma', 0))
                vega = float(option.get('vega', 0))
            
            # Add to tree
            self.option_tree.insert("", "end", values=(
                symbol,
                f"{strike_price:.2f}",
                f"{bid:.2f}",
                f"{ask:.2f}",
                f"{last:.2f}",
                f"{volume:,}",
                f"{open_interest:,}",
                f"{implied_vol:.2f}",
                f"{delta:.3f}",
                f"{theta:.4f}",
                f"{gamma:.4f}",
                f"{vega:.4f}"
            ))
            self.option_symbols.append(symbol)
            
        except Exception as e:
            logger.error(f"Failed to add option to tree: {e}, option data: {option}")
    
    def on_expiration_change(self, value):
        """Handle expiration date change."""
        symbol = self.option_symbol_entry.get().upper()
        if symbol and value:
            self._load_option_chain_data(symbol, value)
    
    def on_option_type_change(self, value):
        """Handle option type change."""
        symbol = self.option_symbol_entry.get().upper()
        expiration = self.expiration_var.get()
        if symbol and expiration:
            self._load_option_chain_data(symbol, expiration)
    
    def refresh_option_chain(self):
        """Refresh the current option chain."""
        symbol = self.option_symbol_entry.get().upper()
        expiration = self.expiration_var.get()
        if symbol and expiration:
            self.selected_option_label.configure(text=f"Refreshing options for {symbol}...")
            self.update_idletasks()
            self._load_option_chain_data(symbol, expiration)
    
    def _subscribe_to_option_quotes(self):
        """Subscribe to real-time option quotes."""
        if not hasattr(self, 'option_symbols') or not self.option_symbols:
            return
            
        try:
            # Subscribe through parent's streamer
            parent_app = self.parent
            if parent_app.streamer_client and parent_app.asyncio_loop:
                asyncio.run_coroutine_threadsafe(
                    parent_app.streamer_client.subscribe_option(
                        self.option_symbols[:50],  # Limit to 50 symbols
                        callback=self._on_option_quote_update
                    ),
                    parent_app.asyncio_loop
                )
        except Exception as e:
            logger.error(f"Failed to subscribe to option quotes: {e}")
    
    def _on_option_quote_update(self, service: str, data: List[Dict]):
        """Handle real-time option quote updates."""
        try:
            for quote in data:
                symbol = quote.get("key")
                if symbol:
                    # Update the option in the tree
                    for item in self.option_tree.get_children():
                        values = self.option_tree.item(item)['values']
                        if values and values[0] == symbol:
                            # Update bid, ask, last, volume
                            new_values = list(values)
                            new_values[2] = f"{quote.get('2', 0):.2f}"  # Bid
                            new_values[3] = f"{quote.get('3', 0):.2f}"  # Ask
                            new_values[4] = f"{quote.get('1', 0):.2f}"  # Last
                            new_values[5] = f"{quote.get('8', 0):,}"    # Volume
                            
                            self.option_tree.item(item, values=new_values)
                            break
        except Exception as e:
            logger.error(f"Error updating option quotes: {e}")
    
    
    def on_option_select(self, event):
        """Handle option selection from the chain."""
        selection = self.option_tree.selection()
        if selection:
            item = self.option_tree.item(selection[0])
            values = item['values']
            self.selected_option = values[0]  # Symbol
            
            # Extract option details
            strike = values[1]  # Strike price
            bid = values[2]     # Bid price
            ask = values[3]     # Ask price
            last = values[4]    # Last price
            
            # Update display
            self.selected_option_label.configure(
                text=f"Selected: {self.selected_option} (Strike: ${strike})"
            )
            
            # Auto-populate price field based on order type
            if hasattr(self, 'option_order_type_var') and hasattr(self, 'option_price_entry'):
                order_type = self.option_order_type_var.get()
                if order_type == "LIMIT":
                    # Use mid-price for limit orders
                    try:
                        bid_float = float(bid.replace(',', ''))
                        ask_float = float(ask.replace(',', ''))
                        if bid_float > 0 and ask_float > 0:
                            mid_price = (bid_float + ask_float) / 2
                            self.option_price_entry.delete(0, 'end')
                            self.option_price_entry.insert(0, f"{mid_price:.2f}")
                    except:
                        pass
    
    def preview_order(self):
        """Preview the order before submission."""
        # Determine which tab is active
        current_tab = self.tabview.get()
        
        order_details = None
        if current_tab == "Equity":
            order_details = self.get_equity_order_details()
        elif current_tab == "Options":
            order_details = self.get_option_order_details()
        elif current_tab == "Spreads":
            order_details = self.get_spread_order_details()
        elif current_tab == "Conditional":
            order_details = self.get_conditional_order_details()
        
        if order_details:
            # Show preview dialog
            preview_text = self.format_order_preview(order_details)
            
            result = messagebox.askyesno(
                "Order Preview",
                f"{preview_text}\n\nDo you want to submit this order?",
                icon="question"
            )
            
            if result:
                self.submit_button.configure(state="normal")
            else:
                self.submit_button.configure(state="disabled")
    
    def get_equity_order_details(self):
        """Get order details from equity tab."""
        try:
            return {
                "type": "equity",
                "account": self.account_var.get(),
                "symbol": self.symbol_entry.get().upper(),
                "quantity": int(self.quantity_entry.get()),
                "order_type": self.order_type_var.get(),
                "instruction": self.instruction_var.get(),
                "limit_price": self.limit_price_entry.get() if self.limit_price_entry.winfo_viewable() else None,
                "stop_price": self.stop_price_entry.get() if self.stop_price_entry.winfo_viewable() else None,
                "duration": self.duration_var.get(),
                "session": self.session_var.get(),
                "all_or_none": self.all_or_none_var.get()
            }
        except ValueError as e:
            messagebox.showerror("Input Error", "Please check your input values")
            return None
    
    def get_option_order_details(self):
        """Get order details from options tab."""
        if not self.selected_option:
            messagebox.showwarning("Selection Error", "Please select an option from the chain")
            return None
        
        try:
            return {
                "type": "option",
                "account": self.account_var.get(),  # Use same account selection
                "symbol": self.selected_option,
                "quantity": int(self.option_quantity_entry.get()),
                "order_type": self.option_order_type_var.get(),
                "instruction": self.option_instruction_var.get(),
                "limit_price": self.option_price_entry.get() if self.option_price_entry.cget("state") == "normal" else None,
                "duration": "DAY"  # Default for options
            }
        except ValueError as e:
            messagebox.showerror("Input Error", "Please check your input values")
            return None
    
    def get_spread_order_details(self):
        """Get order details from spreads tab."""
        # Implementation depends on selected strategy
        strategy = self.strategy_var.get()
        
        if strategy == "VERTICAL":
            try:
                return {
                    "type": "spread",
                    "strategy": strategy,
                    "account": self.account_var.get(),
                    "underlying": self.spread_symbol_entry.get().upper(),
                    "option_type": self.spread_type_var.get(),
                    "expiration": self.spread_exp_entry.get(),
                    "legs": [
                        {
                            "strike": float(self.buy_strike_entry.get()),
                            "quantity": int(self.buy_contracts_entry.get()),
                            "instruction": "BUY_TO_OPEN"
                        },
                        {
                            "strike": float(self.sell_strike_entry.get()),
                            "quantity": int(self.sell_contracts_entry.get()),
                            "instruction": "SELL_TO_OPEN"
                        }
                    ],
                    "net_price": float(self.spread_price_entry.get()) if self.spread_price_entry.get() else None
                }
            except ValueError as e:
                messagebox.showerror("Input Error", "Please check your input values")
                return None
        
        return None
    
    def get_conditional_order_details(self):
        """Get order details from conditional tab."""
        # Implementation depends on conditional type
        return None
    
    def format_order_preview(self, order_details):
        """Format order details for preview."""
        if order_details["type"] == "equity":
            preview = f"Equity Order\n"
            preview += f"Account: {order_details['account']}\n"
            preview += f"Symbol: {order_details['symbol']}\n"
            preview += f"Quantity: {order_details['quantity']}\n"
            preview += f"Instruction: {order_details['instruction']}\n"
            preview += f"Order Type: {order_details['order_type']}\n"
            
            if order_details.get("limit_price"):
                preview += f"Limit Price: ${order_details['limit_price']}\n"
            if order_details.get("stop_price"):
                preview += f"Stop Price: ${order_details['stop_price']}\n"
            
            preview += f"Duration: {order_details['duration']}\n"
            preview += f"Session: {order_details['session']}"
            
        elif order_details["type"] == "option":
            preview = f"Option Order\n"
            preview += f"Account: {order_details['account']}\n"
            preview += f"Option: {order_details['symbol']}\n"
            preview += f"Contracts: {order_details['quantity']}\n"
            preview += f"Instruction: {order_details['instruction']}\n"
            preview += f"Order Type: {order_details['order_type']}\n"
            
            if order_details.get("limit_price"):
                preview += f"Limit Price: ${order_details['limit_price']}"
        
        elif order_details["type"] == "spread":
            preview = f"{order_details['strategy']} Spread\n"
            preview += f"Account: {order_details['account']}\n"
            preview += f"Underlying: {order_details['underlying']}\n"
            preview += f"Type: {order_details['option_type']}\n"
            preview += f"Expiration: {order_details['expiration']}\n"
            
            for i, leg in enumerate(order_details['legs']):
                preview += f"\nLeg {i+1}: {leg['instruction']} {leg['quantity']} @ ${leg['strike']}"
            
            if order_details.get("net_price"):
                preview += f"\nNet Price: ${order_details['net_price']}"
        
        return preview
    
    def submit_order(self):
        """Submit the order."""
        current_tab = self.tabview.get()
        
        try:
            if current_tab == "Equity":
                self.submit_equity_order()
            elif current_tab == "Options":
                self.submit_option_order()
            elif current_tab == "Spreads":
                self.submit_spread_order()
            elif current_tab == "Conditional":
                self.submit_conditional_order()
            
            # Close dialog on successful submission
            self.destroy()
            
        except Exception as e:
            logger.error(f"Error submitting order: {e}")
            messagebox.showerror("Order Error", f"Failed to submit order: {str(e)}")
    
    def submit_equity_order(self):
        """Submit equity order."""
        order_details = self.get_equity_order_details()
        if not order_details:
            return
        
        # Build order based on type
        if order_details["order_type"] == "MARKET":
            order = self.client.create_market_order(
                order_details["symbol"],
                order_details["quantity"],
                order_details["instruction"]
            )
        elif order_details["order_type"] == "LIMIT":
            order = self.client.create_limit_order(
                order_details["symbol"],
                order_details["quantity"],
                order_details["instruction"],
                float(order_details["limit_price"])
            )
        # Add other order types...
        
        # Place the order
        response = self.client.place_order(order_details["account"], order)
        
        if self.on_submit:
            self.on_submit(response)
        
        messagebox.showinfo("Order Submitted", "Your order has been submitted successfully!")
    
    def submit_option_order(self):
        """Submit option order."""
        order_details = self.get_option_order_details()
        if not order_details:
            return
        
        try:
            # Create order structure for options
            from schwab.models.generated.trading_models import (
                Order, OrderType, OrderStrategyType, OrderLeg, OrderLegType,
                PositionEffect, QuantityType, DividendCapitalGains,
                ComplexOrderStrategyType
            )
            from schwab.models.generated.trading_models import Session as OrderSession
            from schwab.models.generated.trading_models import Duration as OrderDuration
            from schwab.models.generated.trading_models import Instruction as OrderInstruction
            from decimal import Decimal
            
            # Determine instruction and position effect
            instruction_str = order_details["instruction"]
            if instruction_str == "BUY_TO_OPEN":
                instruction = OrderInstruction.BUY_TO_OPEN
                position_effect = PositionEffect.OPENING
            elif instruction_str == "BUY_TO_CLOSE":
                instruction = OrderInstruction.BUY_TO_CLOSE
                position_effect = PositionEffect.CLOSING
            elif instruction_str == "SELL_TO_OPEN":
                instruction = OrderInstruction.SELL_TO_OPEN
                position_effect = PositionEffect.OPENING
            elif instruction_str == "SELL_TO_CLOSE":
                instruction = OrderInstruction.SELL_TO_CLOSE
                position_effect = PositionEffect.CLOSING
            else:
                raise ValueError(f"Invalid instruction: {instruction_str}")
            
            # Create order
            quantity = Decimal(str(order_details["quantity"]))
            
            order = Order(
                session=OrderSession.NORMAL,
                duration=OrderDuration.DAY,
                order_type=OrderType[order_details["order_type"]],
                complex_order_strategy_type=ComplexOrderStrategyType.NONE,
                quantity=quantity,
                filled_quantity=Decimal("0"),
                remaining_quantity=quantity,
                order_strategy_type=OrderStrategyType.SINGLE,
                order_leg_collection=[
                    OrderLeg(
                        order_leg_type=OrderLegType.OPTION,
                        leg_id=1,
                        instrument={
                            "symbol": order_details["symbol"],
                            "instrument_id": 0,
                            "type": "OPTION"
                        },
                        instruction=instruction,
                        position_effect=position_effect,
                        quantity=quantity,
                        quantity_type=QuantityType.ALL_SHARES
                    )
                ]
            )
            
            # Add price for limit orders
            if order_details["order_type"] == "LIMIT" and order_details["limit_price"]:
                order.price = Decimal(str(order_details["limit_price"]))
            
            # Place the order
            response = self.client.place_order(order_details["account"], order)
            
            if self.on_submit:
                self.on_submit(response)
            
            messagebox.showinfo("Order Submitted", f"Option order for {order_details['symbol']} has been submitted successfully!")
            
        except Exception as e:
            logger.error(f"Error submitting option order: {e}")
            raise
    
    def submit_spread_order(self):
        """Submit spread order."""
        # Implementation for spread order submission
        pass
    
    def submit_conditional_order(self):
        """Submit conditional order."""
        # Implementation for conditional order submission
        pass


class SchwabPortfolioGUI(ctk.CTk):
    """Main GUI application class."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize variables
        self.client = None
        self.auth = None
        self.portfolio_manager = None
        self.order_monitor = None
        self.streamer_client = None
        self.accounts = []
        self.update_thread = None
        self.stop_updates = threading.Event()
        self.update_queue = queue.Queue()
        
        # Start processing queue in main thread
        self.process_update_queue()
        self.asyncio_loop = None
        self.asyncio_thread = None
        self.watched_symbols = set()  # Symbols to stream quotes for
        
        # Window configuration
        self.title("Schwab Portfolio Manager")
        self.geometry("1400x900")
        self.minsize(1200, 800)
        
        # Check and upgrade database
        check_and_upgrade_db()
        
        # Create main layout
        self.create_layout()
        
        # Try to load saved credentials and connect
        self.load_credentials()
        
        # Set up window close handler
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_layout(self):
        """Create the main application layout."""
        # Main container
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True)
        
        # Top toolbar
        self.create_toolbar(main_container)
        
        # Content area with sidebar
        content_frame = ctk.CTkFrame(main_container)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sidebar
        self.create_sidebar(content_frame)
        
        # Main content area
        self.main_content = ctk.CTkFrame(content_frame)
        self.main_content.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Create tabview for different views
        self.tabview = ctk.CTkTabview(self.main_content)
        self.tabview.pack(fill="both", expand=True)
        
        # Add tabs
        self.tab_portfolio = self.tabview.add("Portfolio")
        self.tab_positions = self.tabview.add("Positions")
        self.tab_orders = self.tabview.add("Orders")
        self.tab_activity = self.tabview.add("Activity")
        self.tab_performance = self.tabview.add("Performance")
        
        # Create content for each tab
        self.create_portfolio_tab()
        self.create_positions_tab()
        self.create_orders_tab()
        self.create_activity_tab()
        self.create_performance_tab()
        
        # Status bar
        self.create_status_bar(main_container)
    
    def create_toolbar(self, parent):
        """Create the top toolbar."""
        toolbar = ctk.CTkFrame(parent, height=50)
        toolbar.pack(fill="x", padx=10, pady=(10, 0))
        
        # Logo/Title
        title_label = ctk.CTkLabel(
            toolbar,
            text="Schwab Portfolio Manager",
            font=("Roboto", 20, "bold")
        )
        title_label.pack(side="left", padx=10)
        
        # Connection status
        self.connection_label = ctk.CTkLabel(
            toolbar,
            text="● Disconnected",
            font=("Roboto", 12),
            text_color="red"
        )
        self.connection_label.pack(side="left", padx=20)
        
        # Right side buttons
        settings_button = ctk.CTkButton(
            toolbar,
            text="Settings",
            command=self.show_settings,
            width=100
        )
        settings_button.pack(side="right", padx=5)
        
        refresh_button = ctk.CTkButton(
            toolbar,
            text="Refresh",
            command=self.refresh_data,
            width=100
        )
        refresh_button.pack(side="right", padx=5)
        
        # Connect button (visible when disconnected)
        self.connect_button = ctk.CTkButton(
            toolbar,
            text="Connect",
            command=self.show_auth_dialog,
            width=100,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.connect_button.pack(side="right", padx=5)
    
    def create_sidebar(self, parent):
        """Create the sidebar with account selection and quick actions."""
        sidebar = ctk.CTkFrame(parent, width=250)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        # Account selection
        account_label = ctk.CTkLabel(
            sidebar,
            text="Accounts",
            font=("Roboto", 16, "bold")
        )
        account_label.pack(pady=(10, 5))
        
        self.account_listbox = ctk.CTkScrollableFrame(sidebar, height=150)
        self.account_listbox.pack(fill="x", padx=10, pady=5)
        
        # Quick actions
        actions_label = ctk.CTkLabel(
            sidebar,
            text="Quick Actions",
            font=("Roboto", 16, "bold")
        )
        actions_label.pack(pady=(20, 10))
        
        # New order button - now opens comprehensive dialog
        new_order_button = ctk.CTkButton(
            sidebar,
            text="New Order",
            command=self.show_comprehensive_order_dialog,
            height=40
        )
        new_order_button.pack(fill="x", padx=10, pady=5)
        
        # Cancel all orders button
        cancel_all_button = ctk.CTkButton(
            sidebar,
            text="Cancel All Orders",
            command=self.cancel_all_orders,
            height=40,
            fg_color="red",
            hover_color="darkred"
        )
        cancel_all_button.pack(fill="x", padx=10, pady=5)
        
        # Export data button
        export_button = ctk.CTkButton(
            sidebar,
            text="Export Data",
            command=self.export_data,
            height=40
        )
        export_button.pack(fill="x", padx=10, pady=5)
        
        # Market status
        market_label = ctk.CTkLabel(
            sidebar,
            text="Market Status",
            font=("Roboto", 16, "bold")
        )
        market_label.pack(pady=(20, 10))
        
        self.market_status_label = ctk.CTkLabel(
            sidebar,
            text="Checking...",
            font=("Roboto", 12)
        )
        self.market_status_label.pack()
    
    def create_portfolio_tab(self):
        """Create portfolio overview tab."""
        # Summary cards
        cards_frame = ctk.CTkFrame(self.tab_portfolio)
        cards_frame.pack(fill="x", padx=10, pady=10)
        
        # Total value card
        self.total_value_card = self.create_info_card(
            cards_frame,
            "Total Value",
            "$0.00",
            "blue"
        )
        self.total_value_card.pack(side="left", fill="both", expand=True, padx=5)
        
        # Day change card
        self.day_change_card = self.create_info_card(
            cards_frame,
            "Day Change",
            "$0.00 (0.00%)",
            "green"
        )
        self.day_change_card.pack(side="left", fill="both", expand=True, padx=5)
        
        # Cash balance card
        self.cash_balance_card = self.create_info_card(
            cards_frame,
            "Cash Balance",
            "$0.00",
            "orange"
        )
        self.cash_balance_card.pack(side="left", fill="both", expand=True, padx=5)
        
        # Buying power card
        self.buying_power_card = self.create_info_card(
            cards_frame,
            "Buying Power",
            "$0.00",
            "purple"
        )
        self.buying_power_card.pack(side="left", fill="both", expand=True, padx=5)
        
        # Portfolio composition chart
        chart_frame = ctk.CTkFrame(self.tab_portfolio)
        chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.create_portfolio_chart(chart_frame)
    
    def create_positions_tab(self):
        """Create positions tab with detailed holdings view."""
        # Positions table
        columns = ("Symbol", "Quantity", "Avg Cost", "Market Value", "Day Change", "Total G/L", "% of Portfolio")
        
        tree_frame = ctk.CTkFrame(self.tab_positions)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configure ttk style for larger font
        style = ttk.Style()
        style.configure("Positions.Treeview", font=("Roboto", 12), rowheight=25)
        style.configure("Positions.Treeview.Heading", font=("Roboto", 13, "bold"))
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        self.positions_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            style="Positions.Treeview"
        )
        
        vsb.config(command=self.positions_tree.yview)
        hsb.config(command=self.positions_tree.xview)
        
        # Configure columns with appropriate widths
        column_widths = {
            "Symbol": 80,
            "Quantity": 80,
            "Avg Cost": 100,
            "Market Value": 120,
            "Day Change": 180,
            "Total G/L": 120,
            "% of Portfolio": 100
        }
        
        for col in columns:
            self.positions_tree.heading(col, text=col)
            self.positions_tree.column(col, width=column_widths.get(col, 120))
        
        # Pack treeview and scrollbars
        self.positions_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-click event
        self.positions_tree.bind("<Double-Button-1>", self.on_position_double_click)
    
    def create_orders_tab(self):
        """Create orders tab with active orders view."""
        # Orders controls
        controls_frame = ctk.CTkFrame(self.tab_orders)
        controls_frame.pack(fill="x", padx=10, pady=10)
        
        # Filter options
        ctk.CTkLabel(controls_frame, text="Filter:", font=("Roboto", 12)).pack(side="left", padx=(0, 10))
        
        self.order_filter_var = ctk.StringVar(value="ALL")
        order_filters = ["ALL", "WORKING", "FILLED", "CANCELED", "REJECTED"]
        self.order_filter_menu = ctk.CTkOptionMenu(
            controls_frame,
            values=order_filters,
            variable=self.order_filter_var,
            command=self.filter_orders,
            width=150
        )
        self.order_filter_menu.pack(side="left", padx=(0, 20))
        
        # Refresh button
        refresh_orders_button = ctk.CTkButton(
            controls_frame,
            text="Refresh Orders",
            command=self.refresh_orders,
            width=120
        )
        refresh_orders_button.pack(side="right", padx=5)
        
        # Orders table
        columns = ("Order ID", "Symbol", "Type", "Qty", "Price", "Status", "Time", "Account")
        
        tree_frame = ctk.CTkFrame(self.tab_orders)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Create treeview with scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        self.orders_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.orders_tree.yview)
        hsb.config(command=self.orders_tree.xview)
        
        # Configure columns
        for col in columns:
            self.orders_tree.heading(col, text=col)
            self.orders_tree.column(col, width=100)
        
        # Pack
        self.orders_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Context menu for orders
        self.create_order_context_menu()
    
    def create_activity_tab(self):
        """Create activity/transactions tab."""
        # Date range selection
        date_frame = ctk.CTkFrame(self.tab_activity)
        date_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(date_frame, text="Date Range:", font=("Roboto", 12)).pack(side="left", padx=(0, 10))
        
        self.date_range_var = ctk.StringVar(value="Today")
        date_ranges = ["Today", "This Week", "This Month", "Last 30 Days", "Last 90 Days", "Year to Date"]
        self.date_range_menu = ctk.CTkOptionMenu(
            date_frame,
            values=date_ranges,
            variable=self.date_range_var,
            command=self.update_activity,
            width=150
        )
        self.date_range_menu.pack(side="left")
        
        # Activity table
        columns = ("Date", "Type", "Symbol", "Description", "Quantity", "Price", "Amount")
        
        tree_frame = ctk.CTkFrame(self.tab_activity)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Create treeview
        self.activity_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.activity_tree.heading(col, text=col)
            self.activity_tree.column(col, width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.activity_tree.yview)
        self.activity_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.activity_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_performance_tab(self):
        """Create performance analysis tab."""
        # Performance metrics
        metrics_frame = ctk.CTkFrame(self.tab_performance)
        metrics_frame.pack(fill="x", padx=10, pady=10)
        
        # Time period selection
        period_frame = ctk.CTkFrame(metrics_frame)
        period_frame.pack(side="left")
        
        ctk.CTkLabel(period_frame, text="Period:", font=("Roboto", 12)).pack(side="left", padx=(0, 10))
        
        self.perf_period_var = ctk.StringVar(value="1M")
        periods = ["1D", "1W", "1M", "3M", "6M", "YTD", "1Y", "ALL"]
        self.perf_period_menu = ctk.CTkOptionMenu(
            period_frame,
            values=periods,
            variable=self.perf_period_var,
            command=self.update_performance,
            width=100
        )
        self.perf_period_menu.pack(side="left")
        
        # Performance chart
        self.perf_chart_frame = ctk.CTkFrame(self.tab_performance)
        self.perf_chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create initial performance chart
        self.create_performance_chart()
    
    def create_status_bar(self, parent):
        """Create status bar at bottom of window."""
        status_bar = ctk.CTkFrame(parent, height=30)
        status_bar.pack(fill="x", side="bottom", padx=10, pady=(0, 10))
        
        # Last update time
        self.last_update_label = ctk.CTkLabel(
            status_bar,
            text="Last Update: Never",
            font=("Roboto", 10)
        )
        self.last_update_label.pack(side="left", padx=10)
        
        # Auto-refresh toggle
        self.auto_refresh_var = ctk.BooleanVar(value=True)
        self.auto_refresh_check = ctk.CTkCheckBox(
            status_bar,
            text="Auto Refresh",
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh
        )
        self.auto_refresh_check.pack(side="right", padx=10)
    
    def create_info_card(self, parent, title, value, color):
        """Create an info card widget."""
        card = ctk.CTkFrame(parent)
        
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=("Roboto", 12),
            text_color="gray"
        )
        title_label.pack(pady=(10, 5))
        
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=("Roboto", 20, "bold")
        )
        value_label.pack(pady=(0, 10))
        
        # Store labels for updates
        card.title_label = title_label
        card.value_label = value_label
        
        return card
    
    def create_portfolio_chart(self, parent):
        """Create portfolio composition pie chart."""
        # Create matplotlib figure
        self.portfolio_figure = plt.Figure(figsize=(6, 4), dpi=100)
        self.portfolio_ax = self.portfolio_figure.add_subplot(111)
        
        # Initial empty chart
        self.portfolio_ax.pie([1], labels=["No Data"], autopct='%1.1f%%')
        self.portfolio_ax.set_title("Portfolio Composition")
        
        # Create canvas
        self.portfolio_canvas = FigureCanvasTkAgg(self.portfolio_figure, parent)
        self.portfolio_canvas.draw()
        self.portfolio_canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def create_performance_chart(self):
        """Create performance line chart."""
        # Create matplotlib figure
        self.perf_figure = plt.Figure(figsize=(8, 5), dpi=100)
        self.perf_ax = self.perf_figure.add_subplot(111)
        
        # Initial empty chart
        self.perf_ax.plot([0, 1], [0, 0], 'b-')
        self.perf_ax.set_title("Portfolio Performance")
        self.perf_ax.set_xlabel("Time")
        self.perf_ax.set_ylabel("Value ($)")
        self.perf_ax.grid(True, alpha=0.3)
        
        # Create canvas
        self.perf_canvas = FigureCanvasTkAgg(self.perf_figure, self.perf_chart_frame)
        self.perf_canvas.draw()
        self.perf_canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def create_order_context_menu(self):
        """Create context menu for orders."""
        self.order_context_menu = tk.Menu(self, tearoff=0)
        self.order_context_menu.add_command(label="Cancel Order", command=self.cancel_selected_order)
        self.order_context_menu.add_command(label="Modify Order", command=self.modify_selected_order)
        self.order_context_menu.add_separator()
        self.order_context_menu.add_command(label="Copy Order ID", command=self.copy_order_id)
        
        # Bind right-click
        self.orders_tree.bind("<Button-3>", self.show_order_context_menu)
    
    def show_comprehensive_order_dialog(self):
        """Show the comprehensive order entry dialog."""
        if not self.client:
            messagebox.showwarning("Not Connected", "Please connect to Schwab first")
            return
        
        if not self.accounts:
            messagebox.showwarning("No Accounts", "No accounts available")
            return
        
        dialog = ComprehensiveOrderEntryDialog(
            self,
            self.client,
            self.accounts,
            on_submit=self.on_order_submitted
        )
    
    def on_order_submitted(self, response):
        """Handle order submission response."""
        # Refresh orders list
        self.refresh_orders()
        
        # Show notification
        messagebox.showinfo("Order Submitted", "Order has been submitted successfully!")
    
    # ... (rest of the methods remain the same as in the original file)
    
    def load_credentials(self):
        """Load saved credentials from database."""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # Get credentials
            c.execute("SELECT * FROM credentials LIMIT 1")
            creds = c.fetchone()
            
            if creds:
                # Try to connect
                self.connect_to_schwab(
                    creds[1],  # trading_client_id
                    creds[2],  # trading_client_secret
                    creds[3],  # redirect_uri
                    creds[4],  # market_data_client_id
                    creds[5]   # market_data_client_secret
                )
            else:
                # No credentials found, show authentication dialog
                self.show_auth_dialog()
            
            conn.close()
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            # Show auth dialog on error
            self.show_auth_dialog()
    
    def show_settings(self):
        """Show settings dialog."""
        settings_dialog = ctk.CTkToplevel(self)
        settings_dialog.title("Settings")
        settings_dialog.geometry("600x400")
        settings_dialog.transient(self)
        settings_dialog.grab_set()
        
        # Center the window
        settings_dialog.update_idletasks()
        x = (settings_dialog.winfo_screenwidth() // 2) - (settings_dialog.winfo_width() // 2)
        y = (settings_dialog.winfo_screenheight() // 2) - (settings_dialog.winfo_height() // 2)
        settings_dialog.geometry(f"+{x}+{y}")
        
        # Create tabs
        tabview = ctk.CTkTabview(settings_dialog)
        tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        # API Settings tab
        api_tab = tabview.add("API Settings")
        credentials_tab = tabview.add("Credentials")
        display_tab = tabview.add("Display")
        auth_tab = tabview.add("Authentication")
        
        # API Settings
        ctk.CTkLabel(api_tab, text="API Configuration", font=("Roboto", 16, "bold")).pack(pady=(10, 20))
        
        # Refresh interval
        refresh_frame = ctk.CTkFrame(api_tab)
        refresh_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(refresh_frame, text="Auto-refresh interval (seconds):").pack(side="left", padx=(0, 10))
        refresh_entry = ctk.CTkEntry(refresh_frame, width=100)
        refresh_entry.insert(0, "30")
        refresh_entry.pack(side="left")
        
        # Streaming quality
        qos_frame = ctk.CTkFrame(api_tab)
        qos_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(qos_frame, text="Streaming Quality:").pack(side="left", padx=(0, 10))
        qos_var = ctk.StringVar(value="REAL_TIME")
        qos_menu = ctk.CTkOptionMenu(
            qos_frame,
            values=["EXPRESS", "REAL_TIME", "FAST", "MODERATE", "SLOW", "DELAYED"],
            variable=qos_var
        )
        qos_menu.pack(side="left")
        
        # Credentials tab
        ctk.CTkLabel(credentials_tab, text="API Credentials", font=("Roboto", 16, "bold")).pack(pady=(10, 20))
        ctk.CTkLabel(
            credentials_tab, 
            text="Credentials are stored securely in the local database",
            text_color="gray"
        ).pack()
        
        # Display tab
        ctk.CTkLabel(display_tab, text="Display Settings", font=("Roboto", 16, "bold")).pack(pady=(10, 20))
        
        # Theme selection
        theme_frame = ctk.CTkFrame(display_tab)
        theme_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(theme_frame, text="Theme:").pack(side="left", padx=(0, 10))
        theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["Light", "Dark", "System"],
            variable=theme_var,
            command=lambda v: ctk.set_appearance_mode(v)
        )
        theme_menu.pack(side="left")
        
        # Authentication tab
        ctk.CTkLabel(auth_tab, text="Authentication Management", font=("Roboto", 16, "bold")).pack(pady=(10, 20))
        
        # Token info
        if self.auth and self.auth.token_expiry:
            token_info_frame = ctk.CTkFrame(auth_tab)
            token_info_frame.pack(fill="x", pady=10)
            
            ctk.CTkLabel(token_info_frame, text="Token Status:", font=("Roboto", 12, "bold")).pack(anchor="w", padx=10, pady=5)
            
            # Check if token is valid
            if self.auth.token_expiry > datetime.now():
                status_text = f"Valid until: {self.auth.token_expiry.strftime('%Y-%m-%d %H:%M:%S')}"
                status_color = "green"
            else:
                status_text = "Expired"
                status_color = "red"
                
            ctk.CTkLabel(
                token_info_frame, 
                text=status_text,
                text_color=status_color
            ).pack(anchor="w", padx=20, pady=5)
        
        # Authentication actions
        auth_actions_frame = ctk.CTkFrame(auth_tab)
        auth_actions_frame.pack(fill="x", pady=20)
        
        # Re-authenticate button
        reauth_button = ctk.CTkButton(
            auth_actions_frame,
            text="Re-authenticate",
            command=lambda: [settings_dialog.destroy(), self.handle_auth_error()],
            width=200
        )
        reauth_button.pack(pady=5)
        
        # Clear credentials button
        clear_creds_button = ctk.CTkButton(
            auth_actions_frame,
            text="Clear All Credentials",
            command=self.clear_all_credentials,
            width=200,
            fg_color="red",
            hover_color="darkred"
        )
        clear_creds_button.pack(pady=5)
        
        # Close button
        close_button = ctk.CTkButton(
            settings_dialog,
            text="Close",
            command=settings_dialog.destroy
        )
        close_button.pack(pady=(0, 20))
    
    def show_auth_dialog(self):
        """Show authentication dialog for entering OAuth credentials."""
        auth_dialog = ctk.CTkToplevel(self)
        auth_dialog.title("Schwab API Authentication")
        auth_dialog.geometry("600x500")
        auth_dialog.transient(self)
        auth_dialog.grab_set()
        
        # Center the window
        auth_dialog.update_idletasks()
        x = (auth_dialog.winfo_screenwidth() // 2) - (auth_dialog.winfo_width() // 2)
        y = (auth_dialog.winfo_screenheight() // 2) - (auth_dialog.winfo_height() // 2)
        auth_dialog.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = ctk.CTkFrame(auth_dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(
            main_frame,
            text="Schwab API Authentication",
            font=("Roboto", 20, "bold")
        ).pack(pady=(0, 10))
        
        # Instructions
        instructions = ctk.CTkTextbox(main_frame, height=100, width=500)
        instructions.pack(pady=(0, 20))
        instructions.insert("1.0", 
            "To use this application, you need Schwab API credentials.\n\n"
            "1. Go to https://developer.schwab.com\n"
            "2. Create an app to get your Client ID and Secret\n"
            "3. Set redirect URI to: https://localhost:8443/callback\n"
            "4. Enter your credentials below"
        )
        instructions.configure(state="disabled")
        
        # Trading API Credentials
        ctk.CTkLabel(
            main_frame,
            text="Trading API Credentials",
            font=("Roboto", 16, "bold")
        ).pack(pady=(10, 5))
        
        # Client ID
        id_frame = ctk.CTkFrame(main_frame)
        id_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(id_frame, text="Client ID:", width=120, anchor="w").pack(side="left", padx=(0, 10))
        client_id_entry = ctk.CTkEntry(id_frame, width=350)
        client_id_entry.pack(side="left", fill="x", expand=True)
        
        # Client Secret
        secret_frame = ctk.CTkFrame(main_frame)
        secret_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(secret_frame, text="Client Secret:", width=120, anchor="w").pack(side="left", padx=(0, 10))
        client_secret_entry = ctk.CTkEntry(secret_frame, width=350, show="*")
        client_secret_entry.pack(side="left", fill="x", expand=True)
        
        # Redirect URI
        uri_frame = ctk.CTkFrame(main_frame)
        uri_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(uri_frame, text="Redirect URI:", width=120, anchor="w").pack(side="left", padx=(0, 10))
        redirect_uri_entry = ctk.CTkEntry(uri_frame, width=350)
        redirect_uri_entry.insert(0, "https://localhost:8443/callback")
        redirect_uri_entry.pack(side="left", fill="x", expand=True)
        
        # Market Data API Credentials (Optional)
        ctk.CTkLabel(
            main_frame,
            text="Market Data API Credentials (Optional)",
            font=("Roboto", 16, "bold")
        ).pack(pady=(20, 5))
        
        # Market Data Client ID
        market_id_frame = ctk.CTkFrame(main_frame)
        market_id_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(market_id_frame, text="Client ID:", width=120, anchor="w").pack(side="left", padx=(0, 10))
        market_id_entry = ctk.CTkEntry(market_id_frame, width=350)
        market_id_entry.pack(side="left", fill="x", expand=True)
        
        # Market Data Client Secret
        market_secret_frame = ctk.CTkFrame(main_frame)
        market_secret_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(market_secret_frame, text="Client Secret:", width=120, anchor="w").pack(side="left", padx=(0, 10))
        market_secret_entry = ctk.CTkEntry(market_secret_frame, width=350, show="*")
        market_secret_entry.pack(side="left", fill="x", expand=True)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        
        def save_and_authenticate():
            """Save credentials and start authentication."""
            trading_id = client_id_entry.get().strip()
            trading_secret = client_secret_entry.get().strip()
            redirect_uri = redirect_uri_entry.get().strip()
            market_id = market_id_entry.get().strip() or None
            market_secret = market_secret_entry.get().strip() or None
            
            if not trading_id or not trading_secret or not redirect_uri:
                messagebox.showerror("Error", "Trading API credentials are required")
                return
            
            # Save credentials to database
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                
                # Clear existing credentials
                c.execute("DELETE FROM credentials")
                
                # Insert new credentials
                c.execute("""
                    INSERT INTO credentials 
                    (trading_client_id, trading_client_secret, redirect_uri, 
                     market_data_client_id, market_data_client_secret)
                    VALUES (?, ?, ?, ?, ?)
                """, (trading_id, trading_secret, redirect_uri, market_id, market_secret))
                
                conn.commit()
                conn.close()
                
                # Close dialog
                auth_dialog.destroy()
                
                # Start authentication
                self.connect_to_schwab(trading_id, trading_secret, redirect_uri, market_id, market_secret)
                
            except Exception as e:
                logger.error(f"Failed to save credentials: {e}")
                messagebox.showerror("Error", f"Failed to save credentials: {str(e)}")
        
        # Connect button
        connect_button = ctk.CTkButton(
            button_frame,
            text="Connect to Schwab",
            command=save_and_authenticate,
            width=200
        )
        connect_button.pack(side="left", padx=(0, 10))
        
        # Cancel button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=auth_dialog.destroy,
            width=100
        )
        cancel_button.pack(side="left")
    
    def refresh_data(self):
        """Refresh all data."""
        if self.client and self.portfolio_manager:
            try:
                # Check if token needs refresh before making API calls
                self.ensure_valid_token()
                
                # Update portfolio
                self.portfolio_manager.update()
                
                # Update UI
                self.update_portfolio_display()
                self.update_positions_display()
                self.refresh_orders()
                
                # Update last refresh time
                self.last_update_label.configure(
                    text=f"Last Update: {datetime.now().strftime('%H:%M:%S')}"
                )
            except ValueError as ve:
                # Token expired and refresh failed
                logger.error(f"Authentication error: {ve}")
                self.handle_auth_error()
            except Exception as e:
                logger.error(f"Error refreshing data: {e}")
                if "401" in str(e) or "unauthorized" in str(e).lower():
                    self.handle_auth_error()
                else:
                    messagebox.showerror("Refresh Error", f"Failed to refresh data: {str(e)}")
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh functionality."""
        if self.auto_refresh_var.get():
            # Start auto-refresh
            if self.client:
                self.start_updates()
        else:
            # Stop auto-refresh
            self.stop_updates.set()
    
    def on_closing(self):
        """Handle window closing event."""
        # Stop update thread
        self.stop_updates.set()
        if self.update_thread:
            self.update_thread.join(timeout=1)
        
        # Stop streaming
        if self.streamer_client and self.asyncio_loop:
            # Stop streamer
            future = asyncio.run_coroutine_threadsafe(
                self.streamer_client.stop(),
                self.asyncio_loop
            )
            try:
                future.result(timeout=2)
            except:
                pass
            
            # Stop asyncio loop
            self.asyncio_loop.call_soon_threadsafe(self.asyncio_loop.stop)
            if self.asyncio_thread:
                self.asyncio_thread.join(timeout=2)
        
        # Close connections
        if self.order_monitor:
            self.order_monitor.stop_monitoring()
        
        # Stop async tasks
        if hasattr(self, 'asyncio_loop') and self.asyncio_loop:
            try:
                # Cancel all tasks
                if hasattr(asyncio, 'all_tasks'):
                    pending = asyncio.all_tasks(self.asyncio_loop)
                else:
                    # For older Python versions
                    pending = asyncio.Task.all_tasks(self.asyncio_loop)
                for task in pending:
                    task.cancel()
            except:
                pass
        
        # Close streaming connection
        if hasattr(self, 'streamer_client') and self.streamer_client:
            try:
                if self.asyncio_loop:
                    asyncio.run_coroutine_threadsafe(
                        self.streamer_client.disconnect(),
                        self.asyncio_loop
                    )
            except:
                pass
        
        # Destroy window
        self.destroy()
    
    # Placeholder methods for remaining functionality
    def connect_to_schwab(self, trading_id, trading_secret, redirect_uri, market_id, market_secret):
        """Connect to Schwab API."""
        try:
            # Initialize auth
            self.auth = SchwabAuth(trading_id, trading_secret, redirect_uri)
            
            # Check if we have saved tokens
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT * FROM tokens WHERE api_type='trading' LIMIT 1")
            token_data = c.fetchone()
            conn.close()
            
            if token_data:
                # Try to use existing tokens
                self.auth.access_token = token_data[2]
                self.auth.refresh_token = token_data[3]
                if token_data[4]:  # Check if expiry is not empty
                    try:
                        self.auth.token_expiry = datetime.fromisoformat(token_data[4])
                    except ValueError:
                        logger.warning("Invalid token expiry format, will need to re-authenticate")
                        self.auth.token_expiry = datetime.now() - timedelta(days=1)  # Force expired
                
                # Check if token is expired
                if self.auth.token_expiry and self.auth.token_expiry <= datetime.now():
                    # Try to refresh
                    try:
                        logger.info("Access token expired, attempting to refresh...")
                        self.auth.refresh_access_token()
                        self.save_tokens()
                        logger.info("Token refreshed successfully")
                    except Exception as e:
                        logger.error(f"Token refresh failed: {e}")
                        # Refresh failed, need new auth
                        messagebox.showinfo(
                            "Authentication Required", 
                            "Your session has expired. Please re-authenticate."
                        )
                        self.start_oauth_flow()
                        return
                else:
                    logger.info("Using existing valid token from database")
            else:
                # No tokens, start OAuth flow
                self.start_oauth_flow()
                return
            
            # Initialize client
            self.client = SchwabClient(trading_id, trading_secret, redirect_uri, auth=self.auth)
            
            # Get accounts
            account_numbers = self.client.get_account_numbers()
            # Store both account numbers and hash values
            self.account_data = [(acc.account_number, acc.hash_value) for acc in account_numbers.accounts]
            self.accounts = [acc.hash_value for acc in account_numbers.accounts]  # Use hash values for API calls
            
            # Update account list in UI
            for widget in self.account_listbox.winfo_children():
                widget.destroy()
            
            for account_number, hash_value in self.account_data:
                account_frame = ctk.CTkFrame(self.account_listbox)
                account_frame.pack(fill="x", pady=2)
                
                account_label = ctk.CTkLabel(
                    account_frame,
                    text=f"Account: {account_number[-4:]}",  # Show last 4 digits of plain account number
                    font=("Roboto", 12)
                )
                account_label.pack(side="left", padx=5)
            
            # Initialize portfolio manager
            self.portfolio_manager = PortfolioManager(self.client)
            
            # Add accounts to portfolio manager
            for account in self.accounts:
                self.portfolio_manager.add_account(account)
            
            # Initialize order monitor
            self.order_monitor = OrderMonitor(self.client)
            
            # Start WebSocket streaming
            self.start_streaming()
            
            # Update connection status
            self.connection_label.configure(text="● Connected", text_color="green")
            self.connect_button.pack_forget()  # Hide connect button when connected
            
            # Start auto-refresh if enabled
            if self.auto_refresh_var.get():
                self.start_updates()
            
            # Initial data refresh
            self.refresh_data()
            
            messagebox.showinfo("Success", "Connected to Schwab successfully!")
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            self.connection_label.configure(text="● Disconnected", text_color="red")
    
    def start_oauth_flow(self):
        """Start the OAuth authentication flow."""
        # Get authorization URL
        auth_url = self.auth.get_authorization_url()
        
        # Show dialog with instructions
        oauth_dialog = ctk.CTkToplevel(self)
        oauth_dialog.title("Schwab OAuth Authentication")
        oauth_dialog.geometry("600x400")
        oauth_dialog.transient(self)
        oauth_dialog.grab_set()
        
        # Center the window
        oauth_dialog.update_idletasks()
        x = (oauth_dialog.winfo_screenwidth() // 2) - (oauth_dialog.winfo_width() // 2)
        y = (oauth_dialog.winfo_screenheight() // 2) - (oauth_dialog.winfo_height() // 2)
        oauth_dialog.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = ctk.CTkFrame(oauth_dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(
            main_frame,
            text="Complete Authentication",
            font=("Roboto", 20, "bold")
        ).pack(pady=(0, 20))
        
        # Instructions
        instructions = ctk.CTkTextbox(main_frame, height=150, width=500)
        instructions.pack(pady=(0, 20))
        instructions.insert("1.0", 
            "Please follow these steps to authenticate:\n\n"
            "1. Click 'Open Browser' to open the Schwab login page\n"
            "2. Log in with your Schwab credentials\n"
            "3. Authorize the application\n"
            "4. You'll be redirected to a page that says 'connection refused'\n"
            "5. Copy the ENTIRE URL from your browser\n"
            "6. Paste it below and click 'Complete Authentication'"
        )
        instructions.configure(state="disabled")
        
        # URL entry
        url_frame = ctk.CTkFrame(main_frame)
        url_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(url_frame, text="Callback URL:").pack(anchor="w", pady=(0, 5))
        url_entry = ctk.CTkEntry(url_frame, placeholder_text="Paste the full URL here...")
        url_entry.pack(fill="x")
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x")
        
        def open_browser():
            """Open the authorization URL in browser."""
            webbrowser.open(auth_url)
        
        def complete_auth():
            """Complete the authentication with the callback URL."""
            callback_url = url_entry.get().strip()
            if not callback_url:
                messagebox.showerror("Error", "Please paste the callback URL")
                return
            
            try:
                # Extract authorization code from URL
                parsed = urlparse(callback_url)
                params = parse_qs(parsed.query)
                
                if 'code' not in params:
                    messagebox.showerror("Error", "No authorization code found in URL")
                    return
                
                auth_code = params['code'][0]
                
                # Exchange code for tokens
                self.auth.exchange_code_for_tokens(auth_code)
                
                # Save tokens
                self.save_tokens()
                
                # Close dialog
                oauth_dialog.destroy()
                
                # Continue with connection
                self.finalize_connection()
                
            except Exception as e:
                logger.error(f"OAuth error: {e}")
                messagebox.showerror("Authentication Error", f"Failed to authenticate: {str(e)}")
        
        # Open browser button
        browser_button = ctk.CTkButton(
            button_frame,
            text="Open Browser",
            command=open_browser,
            width=150
        )
        browser_button.pack(side="left", padx=(0, 10))
        
        # Complete button
        complete_button = ctk.CTkButton(
            button_frame,
            text="Complete Authentication",
            command=complete_auth,
            width=200,
            fg_color="green",
            hover_color="darkgreen"
        )
        complete_button.pack(side="left", padx=(0, 10))
        
        # Cancel button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=oauth_dialog.destroy,
            width=100
        )
        cancel_button.pack(side="left")
    
    def save_tokens(self):
        """Save tokens to database."""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # Clear existing tokens
            c.execute("DELETE FROM tokens WHERE api_type='trading'")
            
            # Insert new tokens
            c.execute("""
                INSERT INTO tokens (api_type, access_token, refresh_token, expiry)
                VALUES (?, ?, ?, ?)
            """, (
                "trading",
                self.auth.access_token,
                self.auth.refresh_token,
                self.auth.token_expiry.isoformat() if self.auth.token_expiry else ""
            ))
            
            conn.commit()
            conn.close()
            logger.info("Tokens saved successfully")
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")
            raise
    
    def finalize_connection(self):
        """Finalize the connection after successful authentication."""
        try:
            # Get stored credentials
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT * FROM credentials LIMIT 1")
            creds = c.fetchone()
            conn.close()
            
            if creds:
                # Initialize client with authenticated auth
                self.client = SchwabClient(creds[1], creds[2], creds[3], auth=self.auth)
                
                # Get accounts
                account_numbers = self.client.get_account_numbers()
                self.accounts = [acc.account_number for acc in account_numbers.accounts]
                
                # Update account list in UI
                for widget in self.account_listbox.winfo_children():
                    widget.destroy()
                
                for account in self.accounts:
                    account_frame = ctk.CTkFrame(self.account_listbox)
                    account_frame.pack(fill="x", pady=2)
                    
                    account_label = ctk.CTkLabel(
                        account_frame,
                        text=f"Account: {account[-4:]}",  # Show last 4 digits
                        font=("Roboto", 12)
                    )
                    account_label.pack(side="left", padx=5)
                
                # Initialize portfolio manager
                self.portfolio_manager = PortfolioManager(self.client, self.accounts)
                
                # Initialize order monitor
                self.order_monitor = OrderMonitor(self.client)
                
                # Start WebSocket streaming (disabled for now due to API issues)
                # self.start_streaming()
                
                # Update connection status
                self.connection_label.configure(text="● Connected", text_color="green")
                self.connect_button.pack_forget()  # Hide connect button when connected
                
                # Start auto-refresh if enabled
                if self.auto_refresh_var.get():
                    self.start_updates()
                
                # Initial data refresh
                self.refresh_data()
                
                messagebox.showinfo("Success", "Connected to Schwab successfully!")
                
        except Exception as e:
            logger.error(f"Failed to finalize connection: {e}")
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            self.connection_label.configure(text="● Disconnected", text_color="red")
    
    def ensure_valid_token(self):
        """Ensure we have a valid access token, refreshing if necessary."""
        if not self.auth:
            raise ValueError("Not authenticated")
            
        try:
            # Check if token is expired or will expire soon (within 5 minutes)
            if self.auth.token_expiry and self.auth.token_expiry <= datetime.now() + timedelta(minutes=5):
                logger.info("Token expiring soon, refreshing...")
                self.auth.refresh_access_token()
                self.save_tokens()
                logger.info("Token refreshed successfully")
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            raise ValueError("Token refresh failed, re-authentication required")
    
    def handle_auth_error(self):
        """Handle authentication errors by prompting for re-authentication."""
        # Update UI to show disconnected state
        self.connection_label.configure(text="● Disconnected", text_color="red")
        self.connect_button.pack(side="right", padx=5)  # Show connect button
        
        # Show message to user
        result = messagebox.askyesno(
            "Authentication Required",
            "Your session has expired or is invalid. Would you like to re-authenticate now?",
            icon="warning"
        )
        
        if result:
            # Get stored credentials
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT * FROM credentials LIMIT 1")
            creds = c.fetchone()
            conn.close()
            
            if creds:
                # Re-initialize auth and start OAuth flow
                self.auth = SchwabAuth(creds[1], creds[2], creds[3])
                self.start_oauth_flow()
            else:
                # No credentials, show setup dialog
                self.show_auth_dialog()
    
    def clear_all_credentials(self):
        """Clear all stored credentials and tokens."""
        result = messagebox.askyesno(
            "Confirm Clear",
            "This will delete all stored credentials and tokens. You will need to re-authenticate. Continue?",
            icon="warning"
        )
        
        if result:
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                
                # Clear credentials
                c.execute("DELETE FROM credentials")
                
                # Clear tokens
                c.execute("DELETE FROM tokens")
                
                conn.commit()
                conn.close()
                
                # Reset auth state
                self.auth = None
                self.client = None
                self.portfolio_manager = None
                self.order_monitor = None
                
                # Update UI
                self.connection_label.configure(text="● Disconnected", text_color="red")
                self.connect_button.pack(side="right", padx=5)
                
                # Clear account list
                for widget in self.account_listbox.winfo_children():
                    widget.destroy()
                
                messagebox.showinfo("Success", "All credentials cleared. Please re-authenticate.")
                
                # Show auth dialog
                self.show_auth_dialog()
                
            except Exception as e:
                logger.error(f"Failed to clear credentials: {e}")
                messagebox.showerror("Error", f"Failed to clear credentials: {str(e)}")
    
    def cancel_all_orders(self):
        """Cancel all open orders."""
        if not self.client or not self.order_management:
            messagebox.showwarning("Not Connected", "Please connect to Schwab first")
            return
            
        result = messagebox.askyesno(
            "Confirm Cancel All",
            "Are you sure you want to cancel ALL open orders?",
            icon="warning"
        )
        
        if result:
            try:
                # Cancel all orders for all accounts
                for account in self.accounts:
                    self.order_management.cancel_all_orders(account)
                
                messagebox.showinfo("Success", "All orders cancelled successfully")
                self.refresh_orders()
                
            except Exception as e:
                logger.error(f"Failed to cancel all orders: {e}")
                messagebox.showerror("Error", f"Failed to cancel orders: {str(e)}")
    
    def export_data(self):
        """Export portfolio data."""
        if not self.portfolio_manager:
            messagebox.showwarning("Not Connected", "Please connect to Schwab first")
            return
            
        from tkinter import filedialog
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    writer.writerow([
                        "Account", "Symbol", "Quantity", "Average Cost", 
                        "Current Price", "Market Value", "Gain/Loss", "Gain/Loss %"
                    ])
                    
                    # Write positions
                    for account_num in self.portfolio_manager._positions:
                        positions_dict = self.portfolio_manager._positions.get(account_num, {})
                        for symbol, position in positions_dict.items():
                            writer.writerow([
                                account_num[-4:],  # Last 4 digits
                                symbol,
                                position.quantity,
                                f"{position.average_cost:.2f}",
                                f"{position.current_price:.2f}",
                                f"{position.market_value:.2f}",
                                f"{position.unrealized_gain_loss:.2f}",
                                f"{position.unrealized_gain_loss_percent:.2f}%"
                            ])
                
                messagebox.showinfo("Success", f"Data exported to {filename}")
                
            except Exception as e:
                logger.error(f"Failed to export data: {e}")
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def on_position_double_click(self, event):
        """Handle position double-click."""
        selection = self.positions_tree.selection()
        if not selection:
            return
            
        item = self.positions_tree.item(selection[0])
        values = item['values']
        if values:
            symbol = values[0]
            
            # Open order dialog with symbol pre-filled
            dialog = ComprehensiveOrderEntryDialog(
                self,
                self.client,
                self.accounts,
                on_submit=self.on_order_submitted
            )
            
            # Pre-fill the symbol
            dialog.symbol_entry.insert(0, symbol)
            dialog.search_symbol()
    
    def filter_orders(self, filter_type):
        """Filter orders display."""
        # Refresh orders with filter
        self.refresh_orders()
    
    def refresh_orders(self):
        """Refresh orders list."""
        if not self.client:
            return
            
        # Clear existing orders
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)
            
        try:
            filter_status = self.order_filter_var.get()
            
            # Get orders for all accounts
            for account in self.accounts:
                orders = self.client.get_orders(
                    account,
                    from_entered_time=datetime.now() - timedelta(days=7),
                    to_entered_time=datetime.now(),
                    status=filter_status if filter_status != "ALL" else None
                )
                
                # Add orders to tree
                for order in orders.orders:
                    # Extract relevant info
                    symbol = order.order_leg_collection[0].instrument.get("symbol", "")
                    quantity = order.order_leg_collection[0].quantity
                    order_type = order.order_type.value
                    price = order.price if hasattr(order, 'price') else "MARKET"
                    status = order.status.value if hasattr(order, 'status') else "UNKNOWN"
                    
                    self.orders_tree.insert("", "end", values=(
                        order.order_id,
                        symbol,
                        order_type,
                        quantity,
                        price,
                        status,
                        order.entered_time.strftime("%m/%d %H:%M") if hasattr(order, 'entered_time') else "",
                        account[-4:]  # Last 4 digits
                    ))
                    
        except Exception as e:
            logger.error(f"Failed to refresh orders: {e}")
    
    def show_order_context_menu(self, event):
        """Show order context menu."""
        # Select row under mouse
        item = self.orders_tree.identify_row(event.y)
        if item:
            self.orders_tree.selection_set(item)
            self.order_context_menu.post(event.x_root, event.y_root)
    
    def cancel_selected_order(self):
        """Cancel selected order."""
        selection = self.orders_tree.selection()
        if not selection:
            return
            
        item = self.orders_tree.item(selection[0])
        values = item['values']
        if values:
            order_id = values[0]
            account = None
            
            # Find full account number
            for acc in self.accounts:
                if acc.endswith(str(values[7])):
                    account = acc
                    break
                    
            if account:
                result = messagebox.askyesno(
                    "Confirm Cancel",
                    f"Cancel order {order_id}?",
                    icon="question"
                )
                
                if result:
                    try:
                        self.client.cancel_order(account, order_id)
                        messagebox.showinfo("Success", "Order cancelled successfully")
                        self.refresh_orders()
                    except Exception as e:
                        logger.error(f"Failed to cancel order: {e}")
                        messagebox.showerror("Error", f"Failed to cancel order: {str(e)}")
    
    def modify_selected_order(self):
        """Modify selected order."""
        selection = self.orders_tree.selection()
        if not selection:
            return
            
        messagebox.showinfo("Not Implemented", "Order modification is not yet implemented")
    
    def copy_order_id(self):
        """Copy order ID to clipboard."""
        selection = self.orders_tree.selection()
        if not selection:
            return
            
        item = self.orders_tree.item(selection[0])
        values = item['values']
        if values:
            order_id = str(values[0])
            self.clipboard_clear()
            self.clipboard_append(order_id)
            messagebox.showinfo("Copied", f"Order ID {order_id} copied to clipboard")
    
    def update_activity(self, date_range):
        """Update activity display."""
        if not self.client:
            return
            
        # Clear existing activity
        for item in self.activity_tree.get_children():
            self.activity_tree.delete(item)
            
        # Determine date range
        end_date = datetime.now()
        if date_range == "Today":
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == "This Week":
            start_date = end_date - timedelta(days=end_date.weekday())
        elif date_range == "This Month":
            start_date = end_date.replace(day=1)
        elif date_range == "Last 30 Days":
            start_date = end_date - timedelta(days=30)
        elif date_range == "Last 90 Days":
            start_date = end_date - timedelta(days=90)
        else:  # Year to Date
            start_date = end_date.replace(month=1, day=1)
            
        # Get transactions for each account
        # Note: This requires transaction API to be implemented
        messagebox.showinfo("Not Implemented", "Transaction history API is not yet implemented")
    
    def update_performance(self, period):
        """Update performance display."""
        if not self.portfolio_manager:
            return
            
        try:
            # Clear previous chart
            self.perf_ax.clear()
            
            # Get performance data (this would need historical data API)
            # For now, show current value as a flat line
            total_value = self.portfolio_manager.get_total_value()
            
            self.perf_ax.plot([0, 1], [total_value, total_value], 'b-', linewidth=2)
            self.perf_ax.set_title(f"Portfolio Performance - {period}")
            self.perf_ax.set_xlabel("Time")
            self.perf_ax.set_ylabel("Value ($)")
            self.perf_ax.grid(True, alpha=0.3)
            self.perf_ax.set_ylim(total_value * 0.95, total_value * 1.05)
            
            self.perf_canvas.draw()
            
        except Exception as e:
            logger.error(f"Failed to update performance: {e}")
    
    def update_portfolio_display(self):
        """Update portfolio display."""
        if not self.portfolio_manager:
            return
            
        try:
            # Update summary cards
            total_value = self.portfolio_manager.get_total_value()
            total_cash = self.portfolio_manager.get_total_cash()
            total_gain_loss = self.portfolio_manager.get_total_unrealized_gain_loss()
            total_gain_loss_pct = self.portfolio_manager.get_total_unrealized_gain_loss_percent()
            
            self.total_value_card.value_label.configure(text=f"${total_value:,.2f}")
            self.cash_balance_card.value_label.configure(text=f"${total_cash:,.2f}")
            
            # Day change
            color = "green" if total_gain_loss >= 0 else "red"
            self.day_change_card.value_label.configure(
                text=f"${total_gain_loss:,.2f} ({total_gain_loss_pct:.2f}%)",
                text_color=color
            )
            
            # Update buying power
            total_buying_power = sum(
                account.buying_power for account in self.portfolio_manager.accounts.values()
            )
            self.buying_power_card.value_label.configure(text=f"${total_buying_power:,.2f}")
            
            # Update portfolio composition chart
            self.portfolio_ax.clear()
            
            # Get position values by symbol
            positions = {}
            for account_num in self.portfolio_manager._positions:
                positions_dict = self.portfolio_manager._positions.get(account_num, {})
                for symbol, position in positions_dict.items():
                    market_value = float(position.market_value or 0)
                    if symbol in positions:
                        positions[symbol] += market_value
                    else:
                        positions[symbol] = market_value
            
            if positions:
                # Sort by value and take top 10
                sorted_positions = sorted(positions.items(), key=lambda x: x[1], reverse=True)[:10]
                
                labels = []
                values = []
                for symbol, value in sorted_positions:
                    if value > 0:
                        labels.append(symbol)
                        values.append(value)
                
                if values:
                    self.portfolio_ax.pie(values, labels=labels, autopct='%1.1f%%')
                    self.portfolio_ax.set_title("Top Holdings")
            else:
                self.portfolio_ax.text(0.5, 0.5, "No Positions", 
                                     ha='center', va='center', transform=self.portfolio_ax.transAxes)
            
            self.portfolio_canvas.draw()
            
        except Exception as e:
            logger.error(f"Failed to update portfolio display: {e}")
    
    def update_positions_display(self):
        """Update positions display."""
        if not self.portfolio_manager:
            return
            
        try:
            # Clear existing positions
            for item in self.positions_tree.get_children():
                self.positions_tree.delete(item)
            
            # Add positions
            total_value = self.portfolio_manager.get_total_value()
            
            # Get positions from portfolio manager's internal structure
            for account_num in self.portfolio_manager._positions:
                positions_dict = self.portfolio_manager._positions.get(account_num, {})
                for symbol, position in positions_dict.items():
                    try:
                        # Get position values
                        market_value = float(position.market_value or 0)
                        quantity = float(position.quantity)
                        avg_cost = float(position.average_cost)
                        unrealized_gl = float(position.unrealized_gain_loss)
                        unrealized_gl_pct = float(position.unrealized_gain_loss_percent)
                        
                        pct_of_portfolio = (market_value / float(total_value) * 100) if total_value > 0 else 0
                        
                        self.positions_tree.insert("", "end", values=(
                            symbol,
                            f"{quantity:,.0f}",
                            f"${avg_cost:.2f}",
                            f"${market_value:,.2f}",
                            f"${unrealized_gl:,.2f} ({unrealized_gl_pct:.2f}%)",
                            f"${unrealized_gl:,.2f}",
                            f"{pct_of_portfolio:.1f}%"
                        ))
                    except Exception as e:
                        logger.error(f"Error displaying position {symbol}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to update positions display: {e}")
    
    def start_updates(self):
        """Start auto-update thread."""
        if self.update_thread and self.update_thread.is_alive():
            return
            
        self.stop_updates.clear()
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
    
    def process_update_queue(self):
        """Process updates from background thread in main thread."""
        try:
            while True:
                try:
                    action, data = self.update_queue.get_nowait()
                    if action == "update_displays":
                        self.update_portfolio_display()
                        self.update_positions_display()
                        self.last_update_label.configure(
                            text=f"Last Update: {datetime.now().strftime('%H:%M:%S')}"
                        )
                    elif action == "auth_error":
                        self.handle_auth_error()
                except queue.Empty:
                    break
        except Exception as e:
            logger.error(f"Error processing update queue: {e}")
        
        # Schedule next check
        self.after(100, self.process_update_queue)
    
    def _update_loop(self):
        """Background update loop."""
        while not self.stop_updates.is_set():
            try:
                # Check token validity before updates
                if self.auth and self.auth.token_expiry:
                    if self.auth.token_expiry <= datetime.now() + timedelta(minutes=5):
                        try:
                            self.auth.refresh_access_token()
                            self.save_tokens()
                        except Exception as e:
                            logger.error(f"Token refresh in update loop failed: {e}")
                            # Schedule auth error handling in main thread
                            self.update_queue.put(("auth_error", None))
                            break
                
                # Update portfolio data
                if self.portfolio_manager:
                    self.portfolio_manager.update()
                    
                # Update UI in main thread using thread-safe method
                try:
                    self.update_queue.put(("update_displays", None))
                except:
                    # If queue doesn't exist, skip update
                    pass
                
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                if "401" in str(e) or "unauthorized" in str(e).lower():
                    # Schedule auth error handling in main thread
                    self.update_queue.put(("auth_error", None))
                    break
                
            # Wait 30 seconds before next update
            self.stop_updates.wait(30)
    
    def start_streaming(self):
        """Start WebSocket streaming."""
        try:
            # Get user preferences for streamer info
            user_prefs = self.client.get_user_preference()
            
            if not user_prefs.streamer_info:
                logger.warning("No streamer info available")
                return
                
            streamer_info = user_prefs.streamer_info[0]
            
            # Start asyncio event loop in separate thread
            if not self.asyncio_loop:
                self.asyncio_loop = asyncio.new_event_loop()
                self.asyncio_thread = threading.Thread(
                    target=self._run_asyncio_loop,
                    daemon=True
                )
                self.asyncio_thread.start()
            
            # Create streamer client
            future = asyncio.run_coroutine_threadsafe(
                self._create_streamer(streamer_info),
                self.asyncio_loop
            )
            future.result(timeout=10)
            
            # Subscribe to initial symbols
            self._subscribe_to_positions()
            
            logger.info("WebSocket streaming started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start streaming: {e}")
    
    def _run_asyncio_loop(self):
        """Run asyncio event loop in thread."""
        asyncio.set_event_loop(self.asyncio_loop)
        self.asyncio_loop.run_forever()
    
    async def _create_streamer(self, streamer_info):
        """Create and start streamer client."""
        self.streamer_client = StreamerClient(self.auth, streamer_info)
        await self.streamer_client.start()
        
        # Set quality of service
        await self.streamer_client.set_qos(QOSLevel.REAL_TIME)
    
    def _subscribe_to_positions(self):
        """Subscribe to quotes for all positions."""
        if not self.portfolio_manager or not self.streamer_client:
            return
            
        try:
            # Get all symbols from positions
            symbols = set()
            for account_num in self.portfolio_manager._positions:
                positions_dict = self.portfolio_manager._positions.get(account_num, {})
                for symbol, position in positions_dict.items():
                    if symbol:  # Symbol is the key, so just add it
                        symbols.add(symbol)
            
            # Add to watched symbols
            self.watched_symbols.update(symbols)
            
            # Subscribe to quotes
            if symbols:
                asyncio.run_coroutine_threadsafe(
                    self.streamer_client.subscribe_quote(
                        list(symbols),
                        callback=self._on_quote_update
                    ),
                    self.asyncio_loop
                )
                
        except Exception as e:
            logger.error(f"Failed to subscribe to positions: {e}")
    
    def _on_quote_update(self, service: str, data: List[Dict]):
        """Handle real-time quote updates."""
        try:
            for quote in data:
                symbol = quote.get("key")
                if symbol:
                    # Update in portfolio manager
                    if hasattr(self.portfolio_manager, '_update_position_quote'):
                        self.portfolio_manager._update_position_quote(symbol, quote)
                    
                    # Update UI if this position is displayed
                    self.after(0, self._update_position_row, symbol, quote)
                    
        except Exception as e:
            logger.error(f"Error handling quote update: {e}")
    
    def _update_position_row(self, symbol: str, quote: Dict):
        """Update position row with real-time data."""
        # Find and update the position in the treeview
        for item in self.positions_tree.get_children():
            values = self.positions_tree.item(item)['values']
            if values and values[0] == symbol:
                # Update market value and day change
                last_price = quote.get("1", 0)  # Field 1 is last price
                change = quote.get("11", 0)  # Field 11 is net change
                change_pct = quote.get("12", 0)  # Field 12 is percent change
                
                # Update specific columns
                new_values = list(values)
                if last_price:
                    # Update market value (price * quantity)
                    quantity = values[1]
                    new_values[3] = f"${last_price * quantity:,.2f}"
                if change is not None:
                    # Update day change
                    new_values[4] = f"${change:.2f} ({change_pct:.2f}%)"
                
                self.positions_tree.item(item, values=new_values)
                break
    
    def add_symbol_to_watchlist(self, symbol: str):
        """Add symbol to streaming watchlist."""
        if not self.streamer_client or symbol in self.watched_symbols:
            return
            
        self.watched_symbols.add(symbol)
        
        # Subscribe to quote
        asyncio.run_coroutine_threadsafe(
            self.streamer_client.subscribe_quote(
                [symbol],
                callback=self._on_quote_update
            ),
            self.asyncio_loop
        )
    
    def remove_symbol_from_watchlist(self, symbol: str):
        """Remove symbol from streaming watchlist."""
        if not self.streamer_client or symbol not in self.watched_symbols:
            return
            
        self.watched_symbols.remove(symbol)
        
        # Unsubscribe
        asyncio.run_coroutine_threadsafe(
            self.streamer_client.unsubscribe(
                StreamerService.QUOTE,
                [symbol]
            ),
            self.asyncio_loop
        )


def main():
    """Main entry point."""
    app = SchwabPortfolioGUI()
    app.mainloop()


if __name__ == "__main__":
    main()