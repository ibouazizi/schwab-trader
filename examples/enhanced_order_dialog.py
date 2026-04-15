#!/usr/bin/env python3
"""
Enhanced Order Dialog for Schwab Portfolio GUI

This module provides a comprehensive order entry dialog that supports:
- Equity orders (all types)
- Option orders with chain loading
- Multi-leg spread orders
- Conditional orders
- Advanced order types (trailing stops, OCO, brackets)
"""

import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from typing import Dict, List, Optional, Any, Tuple
import asyncio
import threading

# Schwab imports
try:
    from schwab import SchwabClient
    from schwab.models.generated.trading_models import (
        Order, OrderType, Session as OrderSession, Duration as OrderDuration,
        Instruction as OrderInstruction, ComplexOrderStrategyType,
        OrderStrategyType, OrderLeg, OrderLegType, PositionEffect,
        RequestedDestination, StopPriceLinkBasis, StopPriceLinkType,
        StopType, TaxLotMethod, SpecialInstruction
    )
except ImportError:
    # For development without schwab package
    Order = OrderType = OrderSession = OrderDuration = None
    OrderInstruction = ComplexOrderStrategyType = OrderStrategyType = None
    OrderLeg = OrderLegType = PositionEffect = None

logger = logging.getLogger(__name__)

class EnhancedOrderDialog(ctk.CTkToplevel):
    """Enhanced order entry dialog with comprehensive order type support."""
    
    def __init__(self, parent, client: 'SchwabClient', accounts: List[Tuple[str, str]], 
                 symbol: str = None, quantity: int = None, instruction: str = None):
        super().__init__(parent)
        
        self.parent = parent
        self.client = client
        self.accounts = accounts  # List of (account_number, hash_value) tuples
        self.initial_symbol = symbol
        self.initial_quantity = quantity
        self.initial_instruction = instruction
        
        # Option chain data
        self.option_chain_data = {}
        self.selected_option = None
        self.option_symbols = []
        
        # Setup window
        self.title("Enhanced Order Entry")
        self.geometry("900x700")
        self.transient(parent)
        self.grab_set()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # Create UI
        self.create_widgets()
        
        # Set initial values if provided
        if symbol:
            self.symbol_entry.insert(0, symbol)
        if quantity:
            self.quantity_entry.insert(0, str(quantity))
        if instruction:
            self.instruction_var.set(instruction)
        
        # Bind theme change detection
        self.bind("<Configure>", self.check_theme_change)
        self._last_appearance = ctk.get_appearance_mode()
    
    def create_labeled_frame(self, parent, text):
        """Create a frame with a label since CTkLabelFrame doesn't exist."""
        container = ctk.CTkFrame(parent)
        label = ctk.CTkLabel(container, text=text, font=("Roboto", 12, "bold"))
        label.pack(pady=(5, 5), padx=10, anchor="w")
        
        inner_frame = ctk.CTkFrame(container)
        inner_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        return container, inner_frame
    
    def setup_ttk_theme(self):
        """Configure ttk styles to match customtkinter theme."""
        style = ttk.Style()
        
        # Get current customtkinter appearance mode
        appearance_mode = ctk.get_appearance_mode()
        
        if appearance_mode == "Dark":
            # Dark theme colors
            bg_color = "#212121"
            fg_color = "#DCE4EE"
            select_bg = "#1f538d"
            tab_bg = "#2b2b2b"
            active_tab_bg = "#1f538d"
            
            # Configure Notebook style
            style.configure("TNotebook", 
                          background=bg_color,
                          borderwidth=0)
            style.configure("TNotebook.Tab",
                          background=tab_bg,
                          foreground=fg_color,
                          padding=[20, 10],
                          borderwidth=0)
            style.map("TNotebook.Tab",
                     background=[("selected", active_tab_bg), ("active", "#3d3d3d")],
                     foreground=[("selected", "white"), ("active", fg_color)])
            
            # Configure Treeview style for option chain
            style.configure("Treeview",
                          background=bg_color,
                          foreground=fg_color,
                          fieldbackground=bg_color,
                          borderwidth=0)
            style.map('Treeview', background=[('selected', select_bg)])
            style.configure("Treeview.Heading",
                          background=tab_bg,
                          foreground=fg_color,
                          borderwidth=0)
            style.map("Treeview.Heading",
                    background=[('active', '#3d3d3d')])
            
            # Configure Scrollbar style
            style.configure("Vertical.TScrollbar",
                          background=tab_bg,
                          borderwidth=0,
                          arrowcolor=fg_color,
                          troughcolor=bg_color)
            style.configure("Horizontal.TScrollbar",
                          background=tab_bg,
                          borderwidth=0,
                          arrowcolor=fg_color,
                          troughcolor=bg_color)
        else:
            # Light theme colors
            bg_color = "#F9F9FA"
            fg_color = "#1C1C1C"
            select_bg = "#36719F"
            tab_bg = "#E0E0E0"
            active_tab_bg = "#36719F"
            
            # Configure Notebook style
            style.configure("TNotebook", 
                          background=bg_color,
                          borderwidth=0)
            style.configure("TNotebook.Tab",
                          background=tab_bg,
                          foreground=fg_color,
                          padding=[20, 10],
                          borderwidth=0)
            style.map("TNotebook.Tab",
                     background=[("selected", active_tab_bg), ("active", "#D0D0D0")],
                     foreground=[("selected", "white"), ("active", fg_color)])
            
            # Configure Treeview style
            style.configure("Treeview",
                          background=bg_color,
                          foreground=fg_color,
                          fieldbackground=bg_color,
                          borderwidth=0)
            style.map('Treeview', background=[('selected', select_bg)])
            style.configure("Treeview.Heading",
                          background=tab_bg,
                          foreground=fg_color,
                          borderwidth=0)
            style.map("Treeview.Heading",
                    background=[('active', '#C0C0C0')])
            
            # Configure Scrollbar style
            style.configure("Vertical.TScrollbar",
                          background=tab_bg,
                          borderwidth=0,
                          arrowcolor=fg_color,
                          troughcolor=bg_color)
            style.configure("Horizontal.TScrollbar",
                          background=tab_bg,
                          borderwidth=0,
                          arrowcolor=fg_color,
                          troughcolor=bg_color)
    
    def check_theme_change(self, event=None):
        """Check if theme has changed and update accordingly."""
        current_appearance = ctk.get_appearance_mode()
        if current_appearance != self._last_appearance:
            self._last_appearance = current_appearance
            self.setup_ttk_theme()
    
    def create_widgets(self):
        """Create all dialog widgets."""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Enhanced Order Entry",
            font=("Roboto", 24, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Apply theme to ttk widgets
        self.setup_ttk_theme()
        
        # Create notebook for different order types
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=(0, 10))
        
        # Add tabs
        self.equity_frame = ctk.CTkFrame(self.notebook)
        self.option_frame = ctk.CTkFrame(self.notebook)
        self.spread_frame = ctk.CTkFrame(self.notebook)
        self.conditional_frame = ctk.CTkFrame(self.notebook)
        
        self.notebook.add(self.equity_frame, text="Equity")
        self.notebook.add(self.option_frame, text="Options")
        self.notebook.add(self.spread_frame, text="Spreads")
        self.notebook.add(self.conditional_frame, text="Conditional")
        
        # Create content for each tab
        self.create_equity_tab()
        self.create_option_tab()
        self.create_spread_tab()
        self.create_conditional_tab()
        
        # Common buttons at bottom
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Preview button
        preview_btn = ctk.CTkButton(
            button_frame,
            text="Preview Order",
            command=self.preview_order,
            width=120
        )
        preview_btn.pack(side="left", padx=(0, 5))
        
        # Submit button
        submit_btn = ctk.CTkButton(
            button_frame,
            text="Submit Order",
            command=self.submit_order,
            width=120,
            fg_color="green",
            hover_color="darkgreen"
        )
        submit_btn.pack(side="left", padx=(0, 5))
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            width=100
        )
        cancel_btn.pack(side="right")
    
    def create_equity_tab(self):
        """Create equity order entry tab."""
        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(self.equity_frame)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Account selection
        ctk.CTkLabel(scroll_frame, text="Account:", font=("Roboto", 12, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.account_var = ctk.StringVar(value=f"*{self.accounts[0][0][-4:]}" if self.accounts else "")
        account_menu = ctk.CTkOptionMenu(
            scroll_frame,
            values=[f"*{acc[0][-4:]}" for acc in self.accounts],
            variable=self.account_var,
            width=200
        )
        account_menu.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Symbol
        ctk.CTkLabel(scroll_frame, text="Symbol:", font=("Roboto", 12, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.symbol_entry = ctk.CTkEntry(scroll_frame, width=200)
        self.symbol_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Instruction
        ctk.CTkLabel(scroll_frame, text="Action:", font=("Roboto", 12, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        self.instruction_var = ctk.StringVar(value="BUY")
        instruction_menu = ctk.CTkOptionMenu(
            scroll_frame,
            values=["BUY", "SELL", "BUY_TO_COVER", "SELL_SHORT"],
            variable=self.instruction_var,
            width=200
        )
        instruction_menu.grid(row=2, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Quantity
        ctk.CTkLabel(scroll_frame, text="Quantity:", font=("Roboto", 12, "bold")).grid(row=3, column=0, sticky="w", pady=5)
        self.quantity_entry = ctk.CTkEntry(scroll_frame, width=200)
        self.quantity_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Order Type
        ctk.CTkLabel(scroll_frame, text="Order Type:", font=("Roboto", 12, "bold")).grid(row=4, column=0, sticky="w", pady=5)
        self.order_type_var = ctk.StringVar(value="MARKET")
        order_type_menu = ctk.CTkOptionMenu(
            scroll_frame,
            values=["MARKET", "LIMIT", "STOP", "STOP_LIMIT", "TRAILING_STOP", 
                   "MARKET_ON_CLOSE", "LIMIT_ON_CLOSE"],
            variable=self.order_type_var,
            command=self.on_order_type_change,
            width=200
        )
        order_type_menu.grid(row=4, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Price fields frame
        self.price_frame = ctk.CTkFrame(scroll_frame)
        self.price_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)
        
        # Create price input fields
        self.limit_price_label = ctk.CTkLabel(self.price_frame, text="Limit Price:")
        self.limit_price_entry = ctk.CTkEntry(self.price_frame, width=150)
        
        self.stop_price_label = ctk.CTkLabel(self.price_frame, text="Stop Price:")
        self.stop_price_entry = ctk.CTkEntry(self.price_frame, width=150)
        
        self.trail_amount_label = ctk.CTkLabel(self.price_frame, text="Trail Amount:")
        self.trail_amount_entry = ctk.CTkEntry(self.price_frame, width=150)
        
        # Duration
        ctk.CTkLabel(scroll_frame, text="Duration:", font=("Roboto", 12, "bold")).grid(row=6, column=0, sticky="w", pady=5)
        self.duration_var = ctk.StringVar(value="DAY")
        duration_menu = ctk.CTkOptionMenu(
            scroll_frame,
            values=["DAY", "GTC", "IOC", "FOK", "GTD", "EXT", "GTC_EXT"],
            variable=self.duration_var,
            width=200
        )
        duration_menu.grid(row=6, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Session
        ctk.CTkLabel(scroll_frame, text="Session:", font=("Roboto", 12, "bold")).grid(row=7, column=0, sticky="w", pady=5)
        self.session_var = ctk.StringVar(value="NORMAL")
        session_menu = ctk.CTkOptionMenu(
            scroll_frame,
            values=["NORMAL", "AM", "PM", "SEAMLESS"],
            variable=self.session_var,
            width=200
        )
        session_menu.grid(row=7, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Advanced options
        advanced_frame = ctk.CTkFrame(scroll_frame)
        advanced_frame.grid(row=8, column=0, columnspan=2, sticky="ew", pady=10)
        
        ctk.CTkLabel(advanced_frame, text="Advanced Options", font=("Roboto", 14, "bold")).pack(pady=(0, 10))
        
        # Special instructions
        self.special_var = ctk.StringVar(value="NONE")
        ctk.CTkLabel(advanced_frame, text="Special Instruction:").pack(anchor="w")
        special_menu = ctk.CTkOptionMenu(
            advanced_frame,
            values=["NONE", "ALL_OR_NONE", "DO_NOT_REDUCE", "AON_DO_NOT_REDUCE"],
            variable=self.special_var,
            width=200
        )
        special_menu.pack(fill="x", pady=(0, 10))
        
        # Tax lot method
        self.tax_lot_var = ctk.StringVar(value="FIFO")
        ctk.CTkLabel(advanced_frame, text="Tax Lot Method:").pack(anchor="w")
        tax_lot_menu = ctk.CTkOptionMenu(
            advanced_frame,
            values=["FIFO", "LIFO", "HIGH_COST", "LOW_COST", "AVERAGE_COST", "SPECIFIC_LOT"],
            variable=self.tax_lot_var,
            width=200
        )
        tax_lot_menu.pack(fill="x", pady=(0, 10))
        
        # Configure grid weights
        scroll_frame.grid_columnconfigure(1, weight=1)
    
    def create_option_tab(self):
        """Create option order entry tab."""
        # Main container
        main_container = ctk.CTkFrame(self.option_frame)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top section for option chain controls
        top_frame = ctk.CTkFrame(main_container)
        top_frame.pack(fill="x", pady=(0, 10))
        
        # Symbol entry
        symbol_frame = ctk.CTkFrame(top_frame)
        symbol_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(symbol_frame, text="Underlying Symbol:").pack(side="left", padx=(0, 10))
        self.option_symbol_entry = ctk.CTkEntry(symbol_frame, width=100)
        self.option_symbol_entry.pack(side="left", padx=(0, 10))
        
        # Load chain button
        load_btn = ctk.CTkButton(
            symbol_frame,
            text="Load Option Chain",
            command=self.load_option_chain,
            width=120
        )
        load_btn.pack(side="left", padx=(0, 10))
        
        # Option type
        self.option_type_var = ctk.StringVar(value="CALL")
        ctk.CTkLabel(symbol_frame, text="Type:").pack(side="left", padx=(10, 5))
        option_type_menu = ctk.CTkOptionMenu(
            symbol_frame,
            values=["CALL", "PUT"],
            variable=self.option_type_var,
            command=lambda x: self.filter_option_chain(),
            width=80
        )
        option_type_menu.pack(side="left", padx=(0, 10))
        
        # Expiration selection
        exp_frame = ctk.CTkFrame(top_frame)
        exp_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(exp_frame, text="Expiration:").pack(side="left", padx=(0, 10))
        self.expiration_var = ctk.StringVar()
        self.expiration_menu = ctk.CTkOptionMenu(
            exp_frame,
            values=["Select Symbol First"],
            variable=self.expiration_var,
            command=lambda x: self.filter_option_chain(),
            width=150
        )
        self.expiration_menu.pack(side="left", padx=(0, 10))
        
        # Strike filter
        ctk.CTkLabel(exp_frame, text="Strike Range:").pack(side="left", padx=(10, 5))
        self.strike_filter_var = ctk.StringVar(value="ALL")
        strike_filter_menu = ctk.CTkOptionMenu(
            exp_frame,
            values=["ALL", "ITM", "ATM", "OTM", "NEAR_MONEY"],
            variable=self.strike_filter_var,
            command=lambda x: self.filter_option_chain(),
            width=100
        )
        strike_filter_menu.pack(side="left")
        
        # Option chain display
        chain_frame = ctk.CTkFrame(main_container)
        chain_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Create treeview for option chain
        columns = ('Strike', 'Bid', 'Ask', 'Last', 'Volume', 'OI', 'IV', 'Delta', 'Gamma', 'Theta', 'Vega')
        self.option_tree = ttk.Treeview(chain_frame, columns=columns, show='headings', height=10)
        
        # Configure columns
        for col in columns:
            self.option_tree.heading(col, text=col)
            width = 80 if col in ['Strike', 'Bid', 'Ask', 'Last'] else 60
            self.option_tree.column(col, width=width)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(chain_frame, orient="vertical", command=self.option_tree.yview)
        h_scroll = ttk.Scrollbar(chain_frame, orient="horizontal", command=self.option_tree.xview)
        self.option_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Grid layout
        self.option_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        chain_frame.grid_rowconfigure(0, weight=1)
        chain_frame.grid_columnconfigure(0, weight=1)
        
        # Bind selection event
        self.option_tree.bind('<<TreeviewSelect>>', self.on_option_select)
        
        # Selected option display
        self.selected_option_label = ctk.CTkLabel(
            main_container,
            text="No option selected",
            font=("Roboto", 12)
        )
        self.selected_option_label.pack(pady=5)
        
        # Option order details
        details_frame = ctk.CTkFrame(main_container)
        details_frame.pack(fill="x", pady=(10, 0))
        
        # Account
        ctk.CTkLabel(details_frame, text="Account:").grid(row=0, column=0, sticky="w", pady=5)
        self.option_account_var = ctk.StringVar(value=f"*{self.accounts[0][0][-4:]}" if self.accounts else "")
        option_account_menu = ctk.CTkOptionMenu(
            details_frame,
            values=[f"*{acc[0][-4:]}" for acc in self.accounts],
            variable=self.option_account_var,
            width=150
        )
        option_account_menu.grid(row=0, column=1, sticky="w", pady=5, padx=(10, 20))
        
        # Instruction
        ctk.CTkLabel(details_frame, text="Action:").grid(row=0, column=2, sticky="w", pady=5)
        self.option_instruction_var = ctk.StringVar(value="BUY_TO_OPEN")
        option_instruction_menu = ctk.CTkOptionMenu(
            details_frame,
            values=["BUY_TO_OPEN", "BUY_TO_CLOSE", "SELL_TO_OPEN", "SELL_TO_CLOSE"],
            variable=self.option_instruction_var,
            width=150
        )
        option_instruction_menu.grid(row=0, column=3, sticky="w", pady=5, padx=(10, 0))
        
        # Quantity
        ctk.CTkLabel(details_frame, text="Contracts:").grid(row=1, column=0, sticky="w", pady=5)
        self.option_quantity_entry = ctk.CTkEntry(details_frame, width=150)
        self.option_quantity_entry.grid(row=1, column=1, sticky="w", pady=5, padx=(10, 20))
        self.option_quantity_entry.insert(0, "1")
        
        # Order type
        ctk.CTkLabel(details_frame, text="Order Type:").grid(row=1, column=2, sticky="w", pady=5)
        self.option_order_type_var = ctk.StringVar(value="LIMIT")
        option_order_type_menu = ctk.CTkOptionMenu(
            details_frame,
            values=["MARKET", "LIMIT", "STOP", "STOP_LIMIT"],
            variable=self.option_order_type_var,
            command=self.on_option_order_type_change,
            width=150
        )
        option_order_type_menu.grid(row=1, column=3, sticky="w", pady=5, padx=(10, 0))
        
        # Price fields
        self.option_price_frame = ctk.CTkFrame(details_frame)
        self.option_price_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=10)
        
        self.option_limit_label = ctk.CTkLabel(self.option_price_frame, text="Limit Price:")
        self.option_limit_entry = ctk.CTkEntry(self.option_price_frame, width=100)
        
        self.option_stop_label = ctk.CTkLabel(self.option_price_frame, text="Stop Price:")
        self.option_stop_entry = ctk.CTkEntry(self.option_price_frame, width=100)
        
        # Show limit price by default
        self.option_limit_label.grid(row=0, column=0, padx=(0, 5))
        self.option_limit_entry.grid(row=0, column=1, padx=(0, 20))
    
    def create_spread_tab(self):
        """Create spread order entry tab."""
        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(self.spread_frame)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Spread type selection
        ctk.CTkLabel(scroll_frame, text="Spread Type:", font=("Roboto", 14, "bold")).pack(pady=(0, 10))
        
        self.spread_type_var = ctk.StringVar(value="VERTICAL")
        spread_types = [
            ("Vertical Spread", "VERTICAL"),
            ("Calendar Spread", "CALENDAR"),
            ("Diagonal Spread", "DIAGONAL"),
            ("Straddle", "STRADDLE"),
            ("Strangle", "STRANGLE"),
            ("Iron Condor", "IRON_CONDOR"),
            ("Butterfly", "BUTTERFLY"),
            ("Custom", "CUSTOM")
        ]
        
        for text, value in spread_types:
            radio = ctk.CTkRadioButton(
                scroll_frame,
                text=text,
                variable=self.spread_type_var,
                value=value,
                command=self.on_spread_type_change
            )
            radio.pack(anchor="w", pady=2)
        
        # Spread legs container
        self.spread_legs_frame = ctk.CTkFrame(scroll_frame)
        self.spread_legs_frame.pack(fill="both", expand=True, pady=(20, 0))
        
        # Initialize with vertical spread
        self.on_spread_type_change()
    
    def create_conditional_tab(self):
        """Create conditional order entry tab."""
        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(self.conditional_frame)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Conditional type selection
        ctk.CTkLabel(scroll_frame, text="Conditional Type:", font=("Roboto", 14, "bold")).pack(pady=(0, 10))
        
        self.conditional_type_var = ctk.StringVar(value="OCO")
        conditional_types = [
            ("One-Cancels-Other (OCO)", "OCO"),
            ("One-Triggers-Other (OTO)", "OTO"),
            ("Bracket Order", "BRACKET"),
            ("If-Then Order", "IF_THEN")
        ]
        
        for text, value in conditional_types:
            radio = ctk.CTkRadioButton(
                scroll_frame,
                text=text,
                variable=self.conditional_type_var,
                value=value,
                command=self.on_conditional_type_change
            )
            radio.pack(anchor="w", pady=2)
        
        # Conditional orders container
        self.conditional_orders_frame = ctk.CTkFrame(scroll_frame)
        self.conditional_orders_frame.pack(fill="both", expand=True, pady=(20, 0))
        
        # Initialize with OCO
        self.on_conditional_type_change()
    
    def on_order_type_change(self, value):
        """Handle order type change for equity orders."""
        # Clear price frame
        for widget in self.price_frame.winfo_children():
            widget.grid_forget()
        
        row = 0
        if value in ["LIMIT", "LIMIT_ON_CLOSE"]:
            self.limit_price_label.grid(row=row, column=0, sticky="w", padx=(0, 10))
            self.limit_price_entry.grid(row=row, column=1, sticky="w")
            row += 1
        
        if value in ["STOP", "STOP_LIMIT"]:
            self.stop_price_label.grid(row=row, column=0, sticky="w", padx=(0, 10))
            self.stop_price_entry.grid(row=row, column=1, sticky="w")
            row += 1
        
        if value == "STOP_LIMIT":
            self.limit_price_label.grid(row=row, column=0, sticky="w", padx=(0, 10))
            self.limit_price_entry.grid(row=row, column=1, sticky="w")
            row += 1
        
        if value == "TRAILING_STOP":
            self.trail_amount_label.grid(row=row, column=0, sticky="w", padx=(0, 10))
            self.trail_amount_entry.grid(row=row, column=1, sticky="w")
    
    def on_option_order_type_change(self, value):
        """Handle order type change for option orders."""
        # Clear price frame
        for widget in self.option_price_frame.winfo_children():
            widget.grid_forget()
        
        col = 0
        if value in ["LIMIT", "STOP_LIMIT"]:
            self.option_limit_label.grid(row=0, column=col, padx=(0, 5))
            self.option_limit_entry.grid(row=0, column=col+1, padx=(0, 20))
            col += 2
        
        if value in ["STOP", "STOP_LIMIT"]:
            self.option_stop_label.grid(row=0, column=col, padx=(0, 5))
            self.option_stop_entry.grid(row=0, column=col+1, padx=(0, 20))
    
    def on_spread_type_change(self):
        """Handle spread type change."""
        # Clear existing legs
        for widget in self.spread_legs_frame.winfo_children():
            widget.destroy()
        
        spread_type = self.spread_type_var.get()
        
        # Add appropriate leg inputs based on spread type
        if spread_type == "VERTICAL":
            self.create_vertical_spread_inputs()
        elif spread_type == "CALENDAR":
            self.create_calendar_spread_inputs()
        elif spread_type == "IRON_CONDOR":
            self.create_iron_condor_inputs()
        # Add more spread types as needed
    
    def create_vertical_spread_inputs(self):
        """Create input fields for vertical spread."""
        ctk.CTkLabel(
            self.spread_legs_frame,
            text="Vertical Spread Setup",
            font=("Roboto", 12, "bold")
        ).pack(pady=(0, 10))
        
        # Common fields
        common_frame = ctk.CTkFrame(self.spread_legs_frame)
        common_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(common_frame, text="Symbol:").grid(row=0, column=0, sticky="w", pady=5)
        self.vert_symbol_entry = ctk.CTkEntry(common_frame, width=100)
        self.vert_symbol_entry.grid(row=0, column=1, pady=5, padx=(10, 20))
        
        ctk.CTkLabel(common_frame, text="Expiration:").grid(row=0, column=2, sticky="w", pady=5)
        self.vert_exp_entry = ctk.CTkEntry(common_frame, width=100, placeholder_text="MM/DD/YYYY")
        self.vert_exp_entry.grid(row=0, column=3, pady=5, padx=(10, 0))
        
        ctk.CTkLabel(common_frame, text="Type:").grid(row=1, column=0, sticky="w", pady=5)
        self.vert_type_var = ctk.StringVar(value="CALL")
        vert_type_menu = ctk.CTkOptionMenu(
            common_frame,
            values=["CALL", "PUT"],
            variable=self.vert_type_var,
            width=100
        )
        vert_type_menu.grid(row=1, column=1, pady=5, padx=(10, 20))
        
        ctk.CTkLabel(common_frame, text="Strategy:").grid(row=1, column=2, sticky="w", pady=5)
        self.vert_strategy_var = ctk.StringVar(value="DEBIT")
        vert_strategy_menu = ctk.CTkOptionMenu(
            common_frame,
            values=["DEBIT", "CREDIT"],
            variable=self.vert_strategy_var,
            width=100
        )
        vert_strategy_menu.grid(row=1, column=3, pady=5, padx=(10, 0))
        
        # Leg details
        legs_frame = ctk.CTkFrame(self.spread_legs_frame)
        legs_frame.pack(fill="x")
        
        # Buy leg
        ctk.CTkLabel(legs_frame, text="Buy Strike:").grid(row=0, column=0, sticky="w", pady=5)
        self.vert_buy_strike = ctk.CTkEntry(legs_frame, width=100)
        self.vert_buy_strike.grid(row=0, column=1, pady=5, padx=(10, 20))
        
        # Sell leg
        ctk.CTkLabel(legs_frame, text="Sell Strike:").grid(row=0, column=2, sticky="w", pady=5)
        self.vert_sell_strike = ctk.CTkEntry(legs_frame, width=100)
        self.vert_sell_strike.grid(row=0, column=3, pady=5, padx=(10, 0))
        
        # Quantity
        ctk.CTkLabel(legs_frame, text="Contracts:").grid(row=1, column=0, sticky="w", pady=5)
        self.vert_quantity = ctk.CTkEntry(legs_frame, width=100)
        self.vert_quantity.grid(row=1, column=1, pady=5, padx=(10, 20))
        self.vert_quantity.insert(0, "1")
        
        # Net price
        ctk.CTkLabel(legs_frame, text="Net Price:").grid(row=1, column=2, sticky="w", pady=5)
        self.vert_price = ctk.CTkEntry(legs_frame, width=100)
        self.vert_price.grid(row=1, column=3, pady=5, padx=(10, 0))
    
    def create_calendar_spread_inputs(self):
        """Create input fields for calendar spread."""
        ctk.CTkLabel(
            self.spread_legs_frame,
            text="Calendar Spread Setup",
            font=("Roboto", 12, "bold")
        ).pack(pady=(0, 10))
        
        # Implementation for calendar spread inputs
        # ... (similar to vertical spread but with different expiration dates)
    
    def create_iron_condor_inputs(self):
        """Create input fields for iron condor."""
        ctk.CTkLabel(
            self.spread_legs_frame,
            text="Iron Condor Setup",
            font=("Roboto", 12, "bold")
        ).pack(pady=(0, 10))
        
        # Implementation for iron condor inputs (4 legs)
        # ... (more complex with put and call spreads)
    
    def on_conditional_type_change(self):
        """Handle conditional type change."""
        # Clear existing orders
        for widget in self.conditional_orders_frame.winfo_children():
            widget.destroy()
        
        conditional_type = self.conditional_type_var.get()
        
        # Add appropriate order inputs based on conditional type
        if conditional_type == "OCO":
            self.create_oco_inputs()
        elif conditional_type == "BRACKET":
            self.create_bracket_inputs()
        # Add more conditional types as needed
    
    def create_oco_inputs(self):
        """Create input fields for OCO orders."""
        ctk.CTkLabel(
            self.conditional_orders_frame,
            text="One-Cancels-Other (OCO) Setup",
            font=("Roboto", 12, "bold")
        ).pack(pady=(0, 10))
        
        # Order 1
        order1_container, order1_frame = self.create_labeled_frame(
            self.conditional_orders_frame, "Order 1"
        )
        order1_container.pack(fill="x", pady=(0, 10))
        
        # Add basic order 1 inputs
        self._create_order_inputs(order1_frame, "oco1")
        
        # Order 2
        order2_container, order2_frame = self.create_labeled_frame(
            self.conditional_orders_frame, "Order 2"
        )
        order2_container.pack(fill="x")
        
        # Add basic order 2 inputs
        self._create_order_inputs(order2_frame, "oco2")
    
    def create_bracket_inputs(self):
        """Create input fields for bracket orders."""
        ctk.CTkLabel(
            self.conditional_orders_frame,
            text="Bracket Order Setup",
            font=("Roboto", 12, "bold")
        ).pack(pady=(0, 10))
        
        # Main order
        main_container, main_frame = self.create_labeled_frame(
            self.conditional_orders_frame, "Main Order"
        )
        main_container.pack(fill="x", pady=(0, 10))
        
        # Add main order inputs
        self._create_order_inputs(main_frame, "bracket_main")
        
        # Profit target
        profit_container, profit_frame = self.create_labeled_frame(
            self.conditional_orders_frame, "Profit Target"
        )
        profit_container.pack(fill="x", pady=(0, 10))
        
        # Add profit target inputs
        self._create_order_inputs(profit_frame, "bracket_profit", simplified=True)
        
        # Stop loss
        stop_container, stop_frame = self.create_labeled_frame(
            self.conditional_orders_frame, "Stop Loss"
        )
        stop_container.pack(fill="x")
        
        # Add stop loss inputs
        self._create_order_inputs(stop_frame, "bracket_stop", simplified=True)
    
    def _create_order_inputs(self, parent, prefix, simplified=False):
        """Create standard order input fields."""
        # Store references to inputs
        if not hasattr(self, 'conditional_inputs'):
            self.conditional_inputs = {}
        
        # Symbol (only for non-simplified)
        if not simplified:
            symbol_frame = ctk.CTkFrame(parent)
            symbol_frame.pack(fill="x", pady=5)
            ctk.CTkLabel(symbol_frame, text="Symbol:", width=100).pack(side="left")
            symbol_entry = ctk.CTkEntry(symbol_frame, width=150)
            symbol_entry.pack(side="left", padx=(5, 0))
            self.conditional_inputs[f"{prefix}_symbol"] = symbol_entry
        
        # Order type
        type_frame = ctk.CTkFrame(parent)
        type_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(type_frame, text="Order Type:", width=100).pack(side="left")
        type_var = ctk.StringVar(value="LIMIT")
        type_menu = ctk.CTkOptionMenu(
            type_frame,
            values=["MARKET", "LIMIT", "STOP", "STOP_LIMIT"],
            variable=type_var,
            width=150
        )
        type_menu.pack(side="left", padx=(5, 0))
        self.conditional_inputs[f"{prefix}_type"] = type_var
        
        # Quantity (only for non-simplified)
        if not simplified:
            qty_frame = ctk.CTkFrame(parent)
            qty_frame.pack(fill="x", pady=5)
            ctk.CTkLabel(qty_frame, text="Quantity:", width=100).pack(side="left")
            qty_entry = ctk.CTkEntry(qty_frame, width=150)
            qty_entry.pack(side="left", padx=(5, 0))
            self.conditional_inputs[f"{prefix}_quantity"] = qty_entry
        
        # Price
        price_frame = ctk.CTkFrame(parent)
        price_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(price_frame, text="Price:", width=100).pack(side="left")
        price_entry = ctk.CTkEntry(price_frame, width=150)
        price_entry.pack(side="left", padx=(5, 0))
        self.conditional_inputs[f"{prefix}_price"] = price_entry
    
    def load_option_chain(self):
        """Load option chain for the entered symbol."""
        symbol = self.option_symbol_entry.get().strip().upper()
        if not symbol:
            messagebox.showerror("Error", "Please enter a symbol")
            return
        
        try:
            # Show loading message
            self.selected_option_label.configure(text="Loading option chain...")
            self.update_idletasks()
            
            # Get option chain from API
            if hasattr(self.client, 'get_option_chain'):
                chain_data = self.client.get_option_chain(
                    symbol=symbol,
                    contract_type="ALL",
                    include_underlying_quote=True
                )
                
                if chain_data:
                    self.option_chain_data = chain_data
                    self.process_option_chain(chain_data)
                else:
                    messagebox.showwarning("No Data", f"No options found for {symbol}")
            else:
                messagebox.showwarning(
                    "Not Available",
                    "Option chain API not available. Please check for updates."
                )
        
        except Exception as e:
            logger.error(f"Failed to load option chain: {e}")
            messagebox.showerror("Error", f"Failed to load option chain: {str(e)}")
            self.selected_option_label.configure(text="Failed to load option chain")
    
    def process_option_chain(self, chain_data):
        """Process and display option chain data."""
        # Extract expiration dates
        expirations = set()
        
        # Process call options
        if 'callExpDateMap' in chain_data:
            for exp_date in chain_data['callExpDateMap'].keys():
                # Format: "2024-01-19:7"
                date_part = exp_date.split(':')[0]
                expirations.add(date_part)
        
        # Process put options
        if 'putExpDateMap' in chain_data:
            for exp_date in chain_data['putExpDateMap'].keys():
                date_part = exp_date.split(':')[0]
                expirations.add(date_part)
        
        # Update expiration menu
        if expirations:
            exp_list = sorted(list(expirations))
            self.expiration_menu.configure(values=exp_list)
            self.expiration_var.set(exp_list[0])
            
            # Filter and display chain
            self.filter_option_chain()
        else:
            self.selected_option_label.configure(text="No options available")
    
    def filter_option_chain(self):
        """Filter and display option chain based on selections."""
        if not self.option_chain_data:
            return
        
        # Clear existing items
        for item in self.option_tree.get_children():
            self.option_tree.delete(item)
        
        option_type = self.option_type_var.get()
        expiration = self.expiration_var.get()
        strike_filter = self.strike_filter_var.get()
        
        # Get the appropriate option map
        if option_type == "CALL":
            option_map = self.option_chain_data.get('callExpDateMap', {})
        else:
            option_map = self.option_chain_data.get('putExpDateMap', {})
        
        # Find matching expiration
        exp_key = None
        for key in option_map.keys():
            if key.startswith(expiration):
                exp_key = key
                break
        
        if not exp_key:
            return
        
        # Get strikes for this expiration
        strikes = option_map.get(exp_key, {})
        
        # Get underlying price for filtering
        underlying_price = None
        if 'underlying' in self.option_chain_data:
            underlying = self.option_chain_data['underlying']
            if 'last' in underlying:
                underlying_price = float(underlying['last'])
        
        # Add options to tree
        self.option_symbols = []
        for strike_str, option_list in sorted(strikes.items(), key=lambda x: float(x[0])):
            strike = float(strike_str)
            
            # Apply strike filter
            if strike_filter != "ALL" and underlying_price:
                if strike_filter == "ITM":
                    if option_type == "CALL" and strike >= underlying_price:
                        continue
                    if option_type == "PUT" and strike <= underlying_price:
                        continue
                elif strike_filter == "OTM":
                    if option_type == "CALL" and strike <= underlying_price:
                        continue
                    if option_type == "PUT" and strike >= underlying_price:
                        continue
                elif strike_filter == "ATM":
                    if abs(strike - underlying_price) > underlying_price * 0.02:
                        continue
                elif strike_filter == "NEAR_MONEY":
                    if abs(strike - underlying_price) > underlying_price * 0.05:
                        continue
            
            # Add option to tree
            for option in option_list:
                self.add_option_to_tree(option)
        
        # Update status
        count = len(self.option_symbols)
        self.selected_option_label.configure(
            text=f"Loaded {count} {option_type} options for {expiration}"
        )
    
    def add_option_to_tree(self, option: Dict[str, Any]):
        """Add an option to the tree view."""
        try:
            # Extract option data
            symbol = option.get('symbol', '')
            strike = float(option.get('strikePrice', 0))
            bid = float(option.get('bid', 0))
            ask = float(option.get('ask', 0))
            last = float(option.get('last', 0))
            volume = int(option.get('totalVolume', 0))
            open_interest = int(option.get('openInterest', 0))
            
            # Greeks
            iv = float(option.get('volatility', 0))
            delta = float(option.get('delta', 0))
            gamma = float(option.get('gamma', 0))
            theta = float(option.get('theta', 0))
            vega = float(option.get('vega', 0))
            
            # Add to tree
            self.option_tree.insert("", "end", values=(
                f"{strike:.2f}",
                f"{bid:.2f}",
                f"{ask:.2f}",
                f"{last:.2f}",
                f"{volume:,}",
                f"{open_interest:,}",
                f"{iv:.2f}",
                f"{delta:.3f}",
                f"{gamma:.4f}",
                f"{theta:.4f}",
                f"{vega:.4f}"
            ), tags=(symbol,))
            
            self.option_symbols.append(symbol)
            
        except Exception as e:
            logger.error(f"Failed to add option to tree: {e}")
    
    def on_option_select(self, event):
        """Handle option selection from chain."""
        selection = self.option_tree.selection()
        if selection:
            item = self.option_tree.item(selection[0])
            values = item['values']
            tags = item['tags']
            
            if tags:
                self.selected_option = tags[0]
                strike = values[0]
                bid = values[1]
                ask = values[2]
                
                # Update display
                self.selected_option_label.configure(
                    text=f"Selected: {self.selected_option} (Strike: ${strike})"
                )
                
                # Auto-populate price for limit orders
                if self.option_order_type_var.get() == "LIMIT":
                    try:
                        # Use mid-price
                        bid_float = float(str(bid).replace(',', ''))
                        ask_float = float(str(ask).replace(',', ''))
                        if bid_float > 0 and ask_float > 0:
                            mid_price = (bid_float + ask_float) / 2
                            self.option_limit_entry.delete(0, 'end')
                            self.option_limit_entry.insert(0, f"{mid_price:.2f}")
                    except:
                        pass
    
    def preview_order(self):
        """Preview the order before submission."""
        try:
            # Determine active tab
            current_tab = self.notebook.index(self.notebook.select())
            
            if current_tab == 0:  # Equity
                order_details = self.get_equity_order_details()
            elif current_tab == 1:  # Options
                order_details = self.get_option_order_details()
            elif current_tab == 2:  # Spreads
                order_details = self.get_spread_order_details()
            elif current_tab == 3:  # Conditional
                order_details = self.get_conditional_order_details()
            else:
                return
            
            if order_details:
                # Format preview
                preview_text = self.format_order_preview(order_details)
                
                # Show preview dialog
                result = messagebox.askyesno(
                    "Order Preview",
                    f"{preview_text}\n\nDo you want to submit this order?"
                )
                
                if result:
                    self.submit_order()
        
        except Exception as e:
            logger.error(f"Error in preview: {e}")
            messagebox.showerror("Error", f"Failed to preview order: {str(e)}")
    
    def get_equity_order_details(self) -> Dict[str, Any]:
        """Get equity order details from form."""
        return {
            "type": "EQUITY",
            "account": self._get_account_hash(self.account_var.get()),
            "symbol": self.symbol_entry.get().strip().upper(),
            "quantity": int(self.quantity_entry.get()),
            "instruction": self.instruction_var.get(),
            "order_type": self.order_type_var.get(),
            "duration": self.duration_var.get(),
            "session": self.session_var.get(),
            "limit_price": self._get_price(self.limit_price_entry),
            "stop_price": self._get_price(self.stop_price_entry),
            "trail_amount": self._get_price(self.trail_amount_entry),
            "special_instruction": self.special_var.get() if self.special_var.get() != "NONE" else None,
            "tax_lot_method": self.tax_lot_var.get()
        }
    
    def get_option_order_details(self) -> Dict[str, Any]:
        """Get option order details from form."""
        if not self.selected_option:
            raise ValueError("No option selected")
        
        return {
            "type": "OPTION",
            "account": self._get_account_hash(self.option_account_var.get()),
            "symbol": self.selected_option,
            "quantity": int(self.option_quantity_entry.get()),
            "instruction": self.option_instruction_var.get(),
            "order_type": self.option_order_type_var.get(),
            "duration": "DAY",  # Default for options
            "session": "NORMAL",
            "limit_price": self._get_price(self.option_limit_entry),
            "stop_price": self._get_price(self.option_stop_entry)
        }
    
    def get_spread_order_details(self) -> Dict[str, Any]:
        """Get spread order details from form."""
        spread_type = self.spread_type_var.get()
        
        if spread_type == "VERTICAL":
            return {
                "type": "SPREAD",
                "spread_type": "VERTICAL",
                "symbol": self.vert_symbol_entry.get().strip().upper(),
                "expiration": self.vert_exp_entry.get(),
                "option_type": self.vert_type_var.get(),
                "strategy": self.vert_strategy_var.get(),
                "buy_strike": float(self.vert_buy_strike.get()),
                "sell_strike": float(self.vert_sell_strike.get()),
                "quantity": int(self.vert_quantity.get()),
                "net_price": float(self.vert_price.get()) if self.vert_price.get() else None
            }
        
        # Add other spread types
        return None
    
    def get_conditional_order_details(self) -> Dict[str, Any]:
        """Get conditional order details from form."""
        # Implementation for conditional orders
        return None
    
    def format_order_preview(self, details: Dict[str, Any]) -> str:
        """Format order details for preview."""
        lines = ["Order Preview", "=" * 30]
        
        order_type = details.get("type", "")
        
        if order_type == "EQUITY":
            lines.extend([
                f"Type: Equity Order",
                f"Symbol: {details['symbol']}",
                f"Action: {details['instruction']}",
                f"Quantity: {details['quantity']} shares",
                f"Order Type: {details['order_type']}",
                f"Duration: {details['duration']}",
                f"Session: {details['session']}"
            ])
            
            if details['limit_price']:
                lines.append(f"Limit Price: ${details['limit_price']:.2f}")
            if details['stop_price']:
                lines.append(f"Stop Price: ${details['stop_price']:.2f}")
            if details['trail_amount']:
                lines.append(f"Trail Amount: ${details['trail_amount']:.2f}")
            
        elif order_type == "OPTION":
            lines.extend([
                f"Type: Option Order",
                f"Symbol: {details['symbol']}",
                f"Action: {details['instruction']}",
                f"Contracts: {details['quantity']}",
                f"Order Type: {details['order_type']}"
            ])
            
            if details['limit_price']:
                lines.append(f"Limit Price: ${details['limit_price']:.2f}")
            if details['stop_price']:
                lines.append(f"Stop Price: ${details['stop_price']:.2f}")
        
        elif order_type == "SPREAD":
            spread_type = details.get('spread_type', '')
            if spread_type == "VERTICAL":
                lines.extend([
                    f"Type: Vertical Spread",
                    f"Symbol: {details['symbol']}",
                    f"Expiration: {details['expiration']}",
                    f"Type: {details['option_type']}",
                    f"Strategy: {details['strategy']}",
                    f"Buy Strike: ${details['buy_strike']:.2f}",
                    f"Sell Strike: ${details['sell_strike']:.2f}",
                    f"Contracts: {details['quantity']}"
                ])
                
                if details['net_price']:
                    lines.append(f"Net Price: ${details['net_price']:.2f}")
        
        return "\n".join(lines)
    
    def submit_order(self):
        """Submit the order."""
        try:
            # Determine active tab
            current_tab = self.notebook.index(self.notebook.select())
            
            if current_tab == 0:  # Equity
                self.submit_equity_order()
            elif current_tab == 1:  # Options
                self.submit_option_order()
            elif current_tab == 2:  # Spreads
                self.submit_spread_order()
            elif current_tab == 3:  # Conditional
                self.submit_conditional_order()
            
        except Exception as e:
            logger.error(f"Error submitting order: {e}")
            messagebox.showerror("Order Error", f"Failed to submit order: {str(e)}")
    
    def submit_equity_order(self):
        """Submit equity order."""
        details = self.get_equity_order_details()
        
        # Create order based on type
        order_type = details['order_type']
        
        if order_type == "MARKET":
            order = self.client.create_market_order(
                symbol=details['symbol'],
                quantity=details['quantity'],
                instruction=OrderInstruction[details['instruction']],
                session=OrderSession[details['session']],
                duration=OrderDuration[details['duration']]
            )
        elif order_type == "LIMIT":
            order = self.client.create_limit_order(
                symbol=details['symbol'],
                quantity=details['quantity'],
                limit_price=details['limit_price'],
                instruction=OrderInstruction[details['instruction']],
                session=OrderSession[details['session']],
                duration=OrderDuration[details['duration']]
            )
        # Add other order types...
        
        # Place order
        self.client.place_order(details['account'], order)
        
        messagebox.showinfo("Success", f"Order submitted for {details['symbol']}")
        self.destroy()
    
    def submit_option_order(self):
        """Submit option order."""
        details = self.get_option_order_details()
        
        # Map instruction to order instruction and position effect
        instruction_map = {
            "BUY_TO_OPEN": (OrderInstruction.BUY, PositionEffect.OPENING),
            "BUY_TO_CLOSE": (OrderInstruction.BUY, PositionEffect.CLOSING),
            "SELL_TO_OPEN": (OrderInstruction.SELL, PositionEffect.OPENING),
            "SELL_TO_CLOSE": (OrderInstruction.SELL, PositionEffect.CLOSING)
        }
        
        instruction, position_effect = instruction_map[details['instruction']]
        
        # Create option order
        order = Order(
            session=OrderSession.NORMAL,
            duration=OrderDuration.DAY,
            order_type=OrderType[details['order_type']],
            complex_order_strategy_type=ComplexOrderStrategyType.NONE,
            quantity=Decimal(str(details['quantity'])),
            filled_quantity=Decimal("0"),
            remaining_quantity=Decimal(str(details['quantity'])),
            order_strategy_type=OrderStrategyType.SINGLE,
            order_leg_collection=[
                OrderLeg(
                    order_leg_type=OrderLegType.OPTION,
                    leg_id=1,
                    instrument={
                        "symbol": details['symbol'],
                        "instrument_id": 0,
                        "type": "OPTION"
                    },
                    instruction=instruction,
                    position_effect=position_effect,
                    quantity=Decimal(str(details['quantity']))
                )
            ]
        )
        
        # Add price if limit order
        if details['order_type'] == "LIMIT" and details['limit_price']:
            order.price = Decimal(str(details['limit_price']))
        
        # Place order
        self.client.place_order(details['account'], order)
        
        messagebox.showinfo("Success", f"Option order submitted for {details['symbol']}")
        self.destroy()
    
    def submit_spread_order(self):
        """Submit spread order."""
        # Implementation for spread orders
        messagebox.showinfo("Not Implemented", "Spread orders coming soon!")
    
    def submit_conditional_order(self):
        """Submit conditional order."""
        # Implementation for conditional orders
        messagebox.showinfo("Not Implemented", "Conditional orders coming soon!")
    
    def _get_account_hash(self, display_value: str) -> str:
        """Get account hash from display value."""
        return next((acc[1] for acc in self.accounts if f"*{acc[0][-4:]}" == display_value), None)
    
    def _get_price(self, entry_widget) -> Optional[float]:
        """Get price from entry widget."""
        try:
            value = entry_widget.get().strip()
            if value:
                return float(value)
        except:
            pass
        return None

# Example usage
if __name__ == "__main__":
    # For testing without the full GUI
    root = ctk.CTk()
    root.withdraw()
    
    # Mock client and accounts
    client = None
    accounts = [("12345678", "HASH1234"), ("87654321", "HASH5678")]
    
    dialog = EnhancedOrderDialog(
        root,
        client,
        accounts,
        symbol="AAPL",
        quantity=100,
        instruction="BUY"
    )
    
    root.mainloop()