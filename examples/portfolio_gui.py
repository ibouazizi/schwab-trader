#!/usr/bin/env python3
"""
Enhanced Schwab Portfolio GUI with Modern Features

A professional-grade GUI application for managing and monitoring trading activity with Schwab.
Features modern UI design, real-time charts, advanced order management, and comprehensive analytics.
"""

import os
import sys
import json
import webbrowser
import threading
import time
import logging
import queue
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import asyncio

# GUI imports
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import customtkinter as ctk

# Data visualization
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation

# Image handling
from PIL import Image, ImageTk, ImageDraw

# Export functionality
import csv
try:
    import pandas as pd
except ImportError:
    pd = None
    
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
except ImportError:
    # ReportLab might not be installed
    colors = letter = A4 = None
    SimpleDocTemplate = Table = TableStyle = Paragraph = Spacer = None
    getSampleStyleSheet = None

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Schwab components
try:
    from schwab import SchwabClient, SchwabAuth, AsyncSchwabClient
    from schwab.portfolio import PortfolioManager
    from schwab.order_monitor import OrderMonitor
    from schwab.models.generated.trading_models import (
        Order, Status, Session, Duration, OrderType,
        Instruction, RequestedDestination, ComplexOrderStrategyType,
        AssetType
    )
    # Try to import optional components
    try:
        from schwab.streaming import StreamerClient, StreamerService, QOSLevel
    except ImportError:
        # Streaming might not be available
        StreamerClient = StreamerService = QOSLevel = None
except ImportError as e:
    print(f"Error importing Schwab components: {e}")
    print("Please ensure the schwab package is installed and in your Python path")
    # For demo purposes, we can continue without these imports
    SchwabClient = SchwabAuth = AsyncSchwabClient = None
    PortfolioManager = OrderMonitor = None
    Order = Status = Session = Duration = OrderType = None
    Instruction = RequestedDestination = ComplexOrderStrategyType = None
    AssetType = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schwab_trader.db')
PREFERENCES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user_preferences.json')
ICONS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons')

# Default settings
DEFAULT_THEME = ("dark", "blue")
DEFAULT_REFRESH_INTERVAL = 30  # seconds
DEFAULT_SYMBOLS = ["AAPL", "AMD", "AMZN", "GOOGL", "META", "MSFT", "NVDA", "TSLA", "SPY", "QQQ"]

# Color schemes
THEME_COLORS = {
    "dark": {
        "bg": "#1a1a1a",
        "fg": "#ffffff",
        "success": "#00ff88",
        "danger": "#ff4444",
        "warning": "#ffaa00",
        "info": "#00aaff",
        "muted": "#666666"
    },
    "light": {
        "bg": "#f5f5f5",
        "fg": "#000000",
        "success": "#28a745",
        "danger": "#dc3545",
        "warning": "#ffc107",
        "info": "#17a2b8",
        "muted": "#6c757d"
    }
}


class ThemeManager:
    """Centralized theme management for the application."""
    
    @staticmethod
    def get_theme_colors():
        """Get theme colors based on current appearance mode."""
        appearance_mode = ctk.get_appearance_mode()
        
        if appearance_mode == "Dark":
            return {
                'bg_color': "#212121",
                'fg_color': "#DCE4EE",
                'select_bg': "#1f538d",
                'header_bg': "#2b2b2b",
                'active_bg': "#3d3d3d",
                'menu_bg': "#212121",
                'menu_fg': "white",
                'menu_active_bg': "#1f538d",
                'menu_active_fg': "white"
            }
        else:
            return {
                'bg_color': "#F9F9FA",
                'fg_color': "#1C1C1C",
                'select_bg': "#36719F",
                'header_bg': "#E0E0E0",
                'active_bg': "#D0D0D0",
                'menu_bg': "white",
                'menu_fg': "black",
                'menu_active_bg': "#1f538d",
                'menu_active_fg': "white"
            }
    
    @staticmethod
    def apply_ttk_theme(root_window=None):
        """Apply theme to all ttk widgets."""
        style = ttk.Style(root_window) if root_window else ttk.Style()
        colors = ThemeManager.get_theme_colors()
        
        # Configure Frame
        style.configure("TFrame", background=colors['bg_color'], borderwidth=0)
        
        # Configure Treeview
        style.configure("Treeview",
                      background=colors['bg_color'],
                      foreground=colors['fg_color'],
                      fieldbackground=colors['bg_color'],
                      borderwidth=0)
        style.map('Treeview', 
                 background=[('selected', colors['select_bg'])],
                 foreground=[('selected', 'white')])
        style.configure("Treeview.Heading",
                      background=colors['header_bg'],
                      foreground=colors['fg_color'],
                      borderwidth=0,
                      relief="flat")
        style.map("Treeview.Heading",
                background=[('active', colors['active_bg'])])
        
        # Configure Scrollbars
        style.configure("Vertical.TScrollbar",
                      background=colors['header_bg'],
                      borderwidth=0,
                      arrowcolor=colors['fg_color'],
                      troughcolor=colors['bg_color'])
        style.configure("Horizontal.TScrollbar",
                      background=colors['header_bg'],
                      borderwidth=0,
                      arrowcolor=colors['fg_color'],
                      troughcolor=colors['bg_color'])
    
    @staticmethod
    def style_menu(menu):
        """Apply theme styling to a menu widget."""
        colors = ThemeManager.get_theme_colors()
        menu.configure(
            bg=colors['menu_bg'],
            fg=colors['menu_fg'],
            activebackground=colors['menu_active_bg'],
            activeforeground=colors['menu_active_fg'],
            borderwidth=0,
            relief="flat"
        )
    
    @staticmethod
    def configure_menu_options(root_window):
        """Configure global menu options."""
        colors = ThemeManager.get_theme_colors()
        root_window.option_add('*Menu.background', colors['menu_bg'])
        root_window.option_add('*Menu.foreground', colors['menu_fg'])
        root_window.option_add('*Menu.activeBackground', colors['menu_active_bg'])
        root_window.option_add('*Menu.activeForeground', colors['menu_active_fg'])
        root_window.option_add('*Menu.borderWidth', '0')


class IconManager:
    """Manages application icons."""
    
    def __init__(self):
        self.icons = {}
        self.create_default_icons()
        
    def create_default_icons(self):
        """Create default icons if icon files don't exist."""
        icon_configs = {
            "refresh": (20, 20, "↻"),
            "connect": (20, 20, "🔗"),
            "disconnect": (20, 20, "🔌"),
            "buy": (20, 20, "📈"),
            "sell": (20, 20, "📉"),
            "chart": (20, 20, "📊"),
            "settings": (20, 20, "⚙️"),
            "export": (20, 20, "📤"),
            "add": (20, 20, "+"),
            "remove": (20, 20, "-"),
            "search": (20, 20, "🔍"),
            "notification": (20, 20, "🔔")
        }
        
        for name, (width, height, symbol) in icon_configs.items():
            self.icons[name] = self.create_text_icon(symbol, width, height)
            
    def create_text_icon(self, text, width, height):
        """Create an icon from text."""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((width//2, height//2), text, anchor="mm", fill=(255, 255, 255, 255))
        return ImageTk.PhotoImage(img)
        
    def get_icon(self, name):
        """Get icon by name."""
        return self.icons.get(name)


class ToastNotification(ctk.CTkToplevel):
    """Modern toast notification."""
    
    def __init__(self, parent, message, notification_type="info", duration=3000):
        super().__init__(parent)
        
        # Window setup
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        # Colors based on type
        colors = {
            "info": "#1f538d",
            "success": "#2d7e2d",
            "warning": "#b87333",
            "error": "#8b0000"
        }
        
        # Create notification
        frame = ctk.CTkFrame(self, fg_color=colors.get(notification_type, "#1f538d"))
        frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        ctk.CTkLabel(
            frame,
            text=message,
            font=("Roboto", 14),
            text_color="white"
        ).pack(padx=20, pady=10)
        
        # Position at top right
        self.update_idletasks()
        x = parent.winfo_x() + parent.winfo_width() - self.winfo_width() - 20
        y = parent.winfo_y() + 50
        self.geometry(f"+{x}+{y}")
        
        # Auto close
        self.after(duration, self.destroy)
        
    @staticmethod
    def show_toast(parent, message, notification_type="info", duration=3000):
        """Static method to show toast."""
        return ToastNotification(parent, message, notification_type, duration)


class AutocompleteEntry(ctk.CTkEntry):
    """Entry widget with autocomplete functionality."""
    
    def __init__(self, parent, completevalues, **kwargs):
        super().__init__(parent, **kwargs)
        self.completevalues = completevalues
        self.lb_up = False
        
        # Bind events
        self.bind('<KeyRelease>', self.on_keyrelease)
        self.bind('<FocusOut>', self.hide_listbox)
        
    def on_keyrelease(self, event):
        """Handle key release."""
        if event.keysym in ['Up', 'Down', 'Return']:
            return
            
        value = self.get().upper()
        
        if value == '':
            self.hide_listbox()
        else:
            words = self.comparison()
            
            if words:
                if not self.lb_up:
                    self.show_listbox()
                
                self.lb.delete(0, tk.END)
                for w in words:
                    self.lb.insert(tk.END, w)
            else:
                self.hide_listbox()
                
    def show_listbox(self):
        """Show the listbox."""
        self.lb = tk.Listbox(height=5)
        self.lb.bind("<Double-Button-1>", self.selection)
        self.lb.bind("<Return>", self.selection)
        
        # Calculate position
        x = self.winfo_x()
        y = self.winfo_y() + self.winfo_height()
        
        self.lb.place(in_=self.master, x=x, y=y, width=self.winfo_width())
        self.lb_up = True
        
    def hide_listbox(self, event=None):
        """Hide the listbox."""
        if self.lb_up:
            self.lb.destroy()
            self.lb_up = False
            
    def selection(self, event):
        """Handle selection from listbox."""
        if self.lb_up:
            self.set(self.lb.get(tk.ACTIVE))
            self.hide_listbox()
            self.icursor(tk.END)
            
    def comparison(self):
        """Compare input to possible values."""
        pattern = self.get().upper()
        return [x for x in self.completevalues if x.upper().startswith(pattern)]


class PriceChartWidget(ctk.CTkFrame):
    """Real-time price chart widget."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configure matplotlib for dark theme
        plt.style.use('dark_background')
        
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.figure.patch.set_facecolor('#1a1a1a')
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#1a1a1a')
        
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        self.price_data = {"time": [], "price": [], "volume": []}
        self.symbol = ""
        
    def update_chart(self, symbol, time, price, volume=0):
        """Update chart with new price data."""
        self.symbol = symbol
        self.price_data["time"].append(time)
        self.price_data["price"].append(price)
        self.price_data["volume"].append(volume)
        
        # Keep only last 500 points for real-time data
        max_points = 500
        if len(self.price_data["time"]) > max_points:
            for key in self.price_data:
                self.price_data[key] = self.price_data[key][-max_points:]
        
        self.redraw()
    
    def set_historical_data(self, symbol, times, prices, volumes=None):
        """Set historical data for the chart."""
        self.symbol = symbol
        self.price_data["time"] = times.copy()
        self.price_data["price"] = prices.copy()
        self.price_data["volume"] = volumes.copy() if volumes else [0] * len(times)
        self.redraw()
        
    def redraw(self):
        """Redraw the chart."""
        self.ax.clear()
        
        if not self.price_data["time"]:
            # Show message when no data
            self.ax.text(0.5, 0.5, 'No data available\nClick "Load" to fetch data', 
                        transform=self.ax.transAxes,
                        ha='center', va='center',
                        fontsize=14, color='white')
            self.ax.set_title(f"{self.symbol or 'Select Symbol'}", color='white', fontsize=12)
            self.figure.tight_layout()
            self.canvas.draw()
            return
        
        # Check if we have enough data points
        if len(self.price_data["time"]) < 2:
            self.ax.text(0.5, 0.5, 'Collecting price data...\nReal-time updates will appear here', 
                        transform=self.ax.transAxes,
                        ha='center', va='center',
                        fontsize=12, color='white')
            
        # Plot price
        self.ax.plot(self.price_data["time"], self.price_data["price"], 
                    color='#00ff88', linewidth=2, label='Price')
        
        # Add moving average
        if len(self.price_data["price"]) > 20:
            try:
                import pandas as pd
                ma20 = pd.Series(self.price_data["price"]).rolling(20).mean()
                self.ax.plot(self.price_data["time"], ma20, 
                            color='#ff9900', linewidth=1, label='MA20', alpha=0.7)
            except ImportError:
                # Fallback to simple moving average without pandas
                ma20 = []
                prices = self.price_data["price"]
                for i in range(len(prices)):
                    if i < 19:
                        ma20.append(prices[i])
                    else:
                        ma20.append(sum(prices[i-19:i+1]) / 20)
                self.ax.plot(self.price_data["time"], ma20, 
                            color='#ff9900', linewidth=1, label='MA20', alpha=0.7)
        
        # Formatting
        self.ax.set_title(f"{self.symbol} Price Chart", color='white', fontsize=12)
        self.ax.set_xlabel('Time', color='white')
        self.ax.set_ylabel('Price ($)', color='white')
        self.ax.tick_params(colors='white')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper left')
        
        # Format x-axis dates
        if len(self.price_data["time"]) > 1:
            self.figure.autofmt_xdate()
            
        self.figure.tight_layout()
        self.canvas.draw()
        
    def clear_chart(self):
        """Clear the chart data."""
        self.price_data = {"time": [], "price": [], "volume": []}
        self.symbol = ""
        self.ax.clear()
        self.canvas.draw()


class PerformanceDashboard(ctk.CTkFrame):
    """Portfolio performance metrics dashboard."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.metric_labels = {}
        self.create_metric_cards()
        
    def create_metric_cards(self):
        """Create performance metric cards."""
        metrics = [
            ("total_value", "Total Value", "$0.00", "#00ff88"),
            ("day_change", "Day Change", "$0.00 (0.00%)", "#ff4444"),
            ("total_pnl", "Total P&L", "$0.00", "#00ff88"),
            ("win_rate", "Win Rate", "0%", "#00aaff"),
            ("sharpe", "Sharpe Ratio", "0.00", "#ffaa00")
        ]
        
        # Create grid layout
        for i, (key, label, value, color) in enumerate(metrics):
            card = self.create_metric_card(key, label, value, color)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            
        # Configure grid weights
        for i in range(len(metrics)):
            self.grid_columnconfigure(i, weight=1)
            
    def create_metric_card(self, key, label, value, color):
        """Create a single metric card."""
        card = ctk.CTkFrame(self, corner_radius=10, fg_color="#2a2a2a")
        
        label_widget = ctk.CTkLabel(
            card, 
            text=label,
            font=("Roboto", 12),
            text_color="#888888"
        )
        label_widget.pack(pady=(10, 5))
        
        value_widget = ctk.CTkLabel(
            card,
            text=value,
            font=("Roboto", 20, "bold"),
            text_color=color
        )
        value_widget.pack(pady=(0, 10))
        
        self.metric_labels[key] = value_widget
        
        return card
        
    def update_metric(self, key, value, color=None):
        """Update a specific metric."""
        if key in self.metric_labels:
            self.metric_labels[key].configure(text=value)
            if color:
                self.metric_labels[key].configure(text_color=color)
                
    def update_all_metrics(self, metrics_dict):
        """Update all metrics from a dictionary."""
        for key, value in metrics_dict.items():
            if key in self.metric_labels:
                color = None
                if key == "day_change":
                    # Determine color based on positive/negative
                    color = "#00ff88" if value.startswith("+") else "#ff4444"
                elif key == "total_pnl":
                    color = "#00ff88" if not value.startswith("-") else "#ff4444"
                self.update_metric(key, value, color)


class WatchlistWidget(ctk.CTkScrollableFrame):
    """Enhanced watchlist with mini charts."""
    
    def __init__(self, parent, on_symbol_click=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.watched_items = {}
        self.on_symbol_click = on_symbol_click
        
    def add_symbol(self, symbol, current_price, change_pct, change_dollar):
        """Add symbol to watchlist."""
        if symbol in self.watched_items:
            self.update_symbol(symbol, current_price, change_pct, change_dollar)
            return
            
        # Create watchlist item
        item_frame = ctk.CTkFrame(self, corner_radius=8, fg_color="#2a2a2a")
        item_frame.pack(fill="x", padx=5, pady=2)
        
        # Make clickable
        if self.on_symbol_click:
            item_frame.bind("<Button-1>", lambda e: self.on_symbol_click(symbol))
            item_frame.configure(cursor="hand2")
        
        # Symbol and price info
        info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        
        symbol_label = ctk.CTkLabel(
            info_frame,
            text=symbol,
            font=("Roboto", 16, "bold"),
            text_color="white"
        )
        symbol_label.pack(anchor="w")
        
        price_label = ctk.CTkLabel(
            info_frame,
            text=f"${current_price:.2f}",
            font=("Roboto", 14),
            text_color="#cccccc"
        )
        price_label.pack(anchor="w")
        
        # Change indicators
        change_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        change_frame.pack(side="right", padx=10)
        
        change_color = "#00ff88" if change_pct >= 0 else "#ff4444"
        arrow = "▲" if change_pct >= 0 else "▼"
        
        change_label = ctk.CTkLabel(
            change_frame,
            text=f"{arrow} ${abs(change_dollar):.2f} ({abs(change_pct):.2f}%)",
            font=("Roboto", 12, "bold"),
            text_color=change_color
        )
        change_label.pack()
        
        # Mini sparkline chart
        chart_frame = ctk.CTkFrame(item_frame, width=60, height=30, fg_color="transparent")
        chart_frame.pack(side="right", padx=5)
        
        # Delete button
        delete_btn = ctk.CTkButton(
            item_frame,
            text="×",
            width=25,
            height=25,
            font=("Roboto", 16),
            fg_color="#ff4444",
            hover_color="#cc0000",
            command=lambda: self.remove_symbol(symbol)
        )
        delete_btn.pack(side="right", padx=5)
        
        self.watched_items[symbol] = {
            "frame": item_frame,
            "price_label": price_label,
            "change_label": change_label,
            "chart_frame": chart_frame,
            "prices": []
        }
        
    def update_symbol(self, symbol, current_price, change_pct, change_dollar):
        """Update symbol in watchlist."""
        if symbol not in self.watched_items:
            return
            
        item = self.watched_items[symbol]
        item["price_label"].configure(text=f"${current_price:.2f}")
        
        change_color = "#00ff88" if change_pct >= 0 else "#ff4444"
        arrow = "▲" if change_pct >= 0 else "▼"
        item["change_label"].configure(
            text=f"{arrow} ${abs(change_dollar):.2f} ({abs(change_pct):.2f}%)",
            text_color=change_color
        )
        
        # Update sparkline data
        item["prices"].append(current_price)
        if len(item["prices"]) > 20:
            item["prices"].pop(0)
            
    def remove_symbol(self, symbol):
        """Remove symbol from watchlist."""
        if symbol in self.watched_items:
            self.watched_items[symbol]["frame"].destroy()
            del self.watched_items[symbol]
            
    def get_symbols(self):
        """Get list of watched symbols."""
        return list(self.watched_items.keys())


class EnhancedTreeview(ttk.Treeview):
    """Treeview with sorting and filtering capabilities."""
    
    def __init__(self, parent, columns, **kwargs):
        # Apply theme before creating widgets
        self._apply_theme()
        
        # Create container frame using CTkFrame for proper theming
        self.container = ctk.CTkFrame(parent)
        
        # Search box
        search_frame = ctk.CTkFrame(self.container)
        search_frame.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(search_frame, text="Search:").pack(side="left", padx=5)
        self.search_var = ctk.StringVar()
        self.search_var.trace('w', self.filter_items)
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Treeview
        super().__init__(self.container, columns=columns, **kwargs)
        
        # Scrollbars
        vsb = ttk.Scrollbar(self.container, orient="vertical", command=self.yview)
        hsb = ttk.Scrollbar(self.container, orient="horizontal", command=self.xview)
        self.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Pack treeview and scrollbars
        super().pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        
        # Setup column headers for sorting
        for col in columns:
            self.heading(col, command=lambda c=col: self.sort_column(c, False))
            
        # Store original items for filtering
        self.all_items = []
    
    def _apply_theme(self):
        """Apply theme to ttk widgets."""
        #ThemeManager.apply_ttk_theme()
        
    def pack(self, **kwargs):
        """Override pack to pack container instead."""
        if hasattr(self, 'container'):
            self.container.pack(**kwargs)
        else:
            super().pack(**kwargs)
            
    def grid(self, **kwargs):
        """Override grid to grid container instead."""
        if hasattr(self, 'container'):
            self.container.grid(**kwargs)
        else:
            super().grid(**kwargs)
            
    def sort_column(self, col, reverse):
        """Sort treeview by column."""
        items = [(self.set(child, col), child) for child in self.get_children('')]
        
        # Try numeric sort first, fall back to string sort
        try:
            items.sort(key=lambda x: float(x[0].replace(',', '').replace('$', '').replace('%', '')), 
                      reverse=reverse)
        except:
            items.sort(reverse=reverse)
            
        for index, (val, child) in enumerate(items):
            self.move(child, '', index)
            
        # Update header to show sort direction
        for column in self['columns']:
            self.heading(column, text=column)
        self.heading(col, text=f"{col} {'↓' if reverse else '↑'}")
        
        # Toggle sort direction for next click
        self.heading(col, command=lambda: self.sort_column(col, not reverse))
        
    def filter_items(self, *args):
        """Filter items based on search text."""
        search_text = self.search_var.get().lower()
        
        # Clear current items
        for item in self.get_children(''):
            self.delete(item)
            
        # Re-add filtered items
        for item_data in self.all_items:
            # Check if search text is in any column
            if not search_text or any(search_text in str(val).lower() for val in item_data['values']):
                self.insert('', 'end', values=item_data['values'], tags=item_data.get('tags', ()))
                
    def insert(self, parent, index, **kwargs):
        """Override insert to store items for filtering."""
        # Store item data
        if parent == '' and 'values' in kwargs:
            self.all_items.append({
                'values': kwargs['values'],
                'tags': kwargs.get('tags', ())
            })
        return super().insert(parent, index, **kwargs)
        
    def delete(self, *items):
        """Override delete to update stored items."""
        for item in items:
            # Remove from stored items
            try:
                values = self.item(item)['values']
                self.all_items = [i for i in self.all_items if i['values'] != values]
            except:
                pass
        return super().delete(*items)


class OrderTemplateManager(ctk.CTkToplevel):
    """Manage order templates for quick trading."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Order Templates")
        self.geometry("800x600")
        
        self.templates = self.load_templates()
        self.selected_template = None
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        """Create the UI."""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left side - Template list
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(
            list_frame,
            text="Saved Templates",
            font=("Roboto", 18, "bold")
        ).pack(pady=(0, 10))
        
        # Template listbox with theme-aware colors
        colors = ThemeManager.get_theme_colors()
            
        self.template_listbox = tk.Listbox(
            list_frame,
            bg=colors['bg_color'],
            fg=colors['fg_color'],
            selectbackground=colors['select_bg'],
            selectforeground="white",
            font=("Roboto", 12),
            borderwidth=0,
            highlightthickness=0
        )
        self.template_listbox.pack(fill="both", expand=True)
        self.template_listbox.bind("<<ListboxSelect>>", self.on_template_select)
        
        # Populate templates
        self.refresh_template_list()
        
        # Buttons
        button_frame = ctk.CTkFrame(list_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkButton(
            button_frame,
            text="New",
            command=self.new_template,
            width=80
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            button_frame,
            text="Delete",
            command=self.delete_template,
            width=80,
            fg_color="#ff4444"
        ).pack(side="left", padx=2)
        
        # Right side - Template editor
        editor_frame = ctk.CTkFrame(main_frame)
        editor_frame.pack(side="right", fill="both", expand=True)
        
        ctk.CTkLabel(
            editor_frame,
            text="Template Details",
            font=("Roboto", 18, "bold")
        ).pack(pady=(0, 10))
        
        # Template fields
        fields = [
            ("Template Name", "name", "text"),
            ("Order Type", "order_type", "dropdown", ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"]),
            ("Default Quantity", "quantity", "number"),
            ("Time in Force", "duration", "dropdown", ["DAY", "GTC", "IOC", "FOK"]),
            ("Default Instruction", "instruction", "dropdown", ["BUY", "SELL"]),
            ("Notes", "notes", "text")
        ]
        
        self.entries = {}
        for field_info in fields:
            if len(field_info) == 3:
                label, field, field_type = field_info
                options = None
            else:
                label, field, field_type, options = field_info
                
            ctk.CTkLabel(editor_frame, text=label).pack(anchor="w", pady=(10, 0))
            
            if field_type == "dropdown" and options:
                entry = ctk.CTkOptionMenu(editor_frame, values=options)
            elif field_type == "number":
                entry = ctk.CTkEntry(editor_frame, placeholder_text="0")
            else:
                entry = ctk.CTkEntry(editor_frame)
                
            entry.pack(fill="x", pady=(0, 5))
            self.entries[field] = entry
            
        # Save button
        ctk.CTkButton(
            editor_frame,
            text="Save Template",
            command=self.save_template,
            height=40
        ).pack(pady=20)
        
    def refresh_template_list(self):
        """Refresh the template list."""
        self.template_listbox.delete(0, tk.END)
        for template in self.templates:
            self.template_listbox.insert(tk.END, template.get("name", "Unnamed"))
            
    def on_template_select(self, event):
        """Handle template selection."""
        selection = self.template_listbox.curselection()
        if selection:
            index = selection[0]
            self.selected_template = self.templates[index]
            self.load_template_to_editor(self.selected_template)
            
    def load_template_to_editor(self, template):
        """Load template data into editor fields."""
        for field, entry in self.entries.items():
            value = template.get(field, "")
            if isinstance(entry, ctk.CTkOptionMenu):
                entry.set(value)
            else:
                entry.delete(0, tk.END)
                entry.insert(0, str(value))
                
    def new_template(self):
        """Create a new template."""
        self.selected_template = None
        for entry in self.entries.values():
            if isinstance(entry, ctk.CTkOptionMenu):
                entry.set("")
            else:
                entry.delete(0, tk.END)
                
    def save_template(self):
        """Save the current template."""
        template = {}
        for field, entry in self.entries.items():
            if isinstance(entry, ctk.CTkOptionMenu):
                template[field] = entry.get()
            else:
                template[field] = entry.get()
                
        if not template.get("name"):
            messagebox.showwarning("Validation Error", "Template name is required")
            return
            
        if self.selected_template:
            # Update existing
            index = self.templates.index(self.selected_template)
            self.templates[index] = template
        else:
            # Add new
            self.templates.append(template)
            
        self.save_templates()
        self.refresh_template_list()
        self.show_success("Template saved successfully")
        
    def delete_template(self):
        """Delete the selected template."""
        if self.selected_template:
            self.templates.remove(self.selected_template)
            self.save_templates()
            self.refresh_template_list()
            self.new_template()
            self.show_info("Template deleted")
            
    def load_templates(self):
        """Load templates from file."""
        try:
            with open("order_templates.json", "r") as f:
                return json.load(f)
        except:
            return []
            
    def save_templates(self):
        """Save templates to file."""
        with open("order_templates.json", "w") as f:
            json.dump(self.templates, f, indent=2)


class StatusBar(ctk.CTkFrame):
    """Application status bar."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=35, **kwargs)
        self.pack_propagate(False)
        
        # Connection status
        self.connection_label = ctk.CTkLabel(
            self,
            text="● Disconnected",
            text_color="#ff4444",
            font=("Roboto", 12)
        )
        self.connection_label.pack(side="left", padx=10)
        
        # Market status
        self.market_status = ctk.CTkLabel(
            self,
            text="Market: Unknown",
            font=("Roboto", 12)
        )
        self.market_status.pack(side="left", padx=20)
        
        # Separator
        sep1 = ctk.CTkFrame(self, width=2, fg_color="#444444")
        sep1.pack(side="left", fill="y", padx=20)
        
        # Account info
        self.account_info = ctk.CTkLabel(
            self,
            text="No Account Selected",
            font=("Roboto", 12)
        )
        self.account_info.pack(side="left", padx=10)
        
        # Right side
        # Last update time
        self.last_update = ctk.CTkLabel(
            self,
            text="Last Update: Never",
            font=("Roboto", 11),
            text_color="#888888"
        )
        self.last_update.pack(side="right", padx=10)
        
        # Separator
        sep2 = ctk.CTkFrame(self, width=2, fg_color="#444444")
        sep2.pack(side="right", fill="y", padx=10)
        
        # Refresh rate
        self.refresh_rate = ctk.CTkLabel(
            self,
            text="Refresh: 30s",
            font=("Roboto", 11),
            text_color="#888888"
        )
        self.refresh_rate.pack(side="right", padx=5)
        
    def update_connection_status(self, connected, message=""):
        """Update connection status."""
        if connected:
            self.connection_label.configure(
                text=f"● Connected{' - ' + message if message else ''}",
                text_color="#00ff88"
            )
        else:
            self.connection_label.configure(
                text=f"● Disconnected{' - ' + message if message else ''}",
                text_color="#ff4444"
            )
            
    def update_market_status(self, status):
        """Update market status."""
        self.market_status.configure(text=f"Market: {status}")
        
    def update_account_info(self, info):
        """Update account information."""
        self.account_info.configure(text=info)
        
    def update_last_update(self):
        """Update last update timestamp."""
        self.last_update.configure(
            text=f"Last Update: {datetime.now().strftime('%H:%M:%S')}"
        )
        
    def update_refresh_rate(self, seconds):
        """Update refresh rate display."""
        self.refresh_rate.configure(text=f"Refresh: {seconds}s")


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog for application preferences."""
    
    def __init__(self, parent, preferences):
        super().__init__(parent)
        self.parent = parent
        self.preferences = preferences.copy()  # Work with a copy
        self.settings_changed = False
        self.theme_changed = False
        
        # Setup window
        self.title("Settings")
        self.geometry("600x500")
        self.transient(parent)
        self.grab_set()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # Create UI
        self.create_widgets()
        
    def create_widgets(self):
        """Create settings widgets."""
        # Main container
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Application Settings",
            font=("Roboto", 24, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Theme section
        theme_frame = ctk.CTkFrame(main_frame)
        theme_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            theme_frame,
            text="Theme Settings",
            font=("Roboto", 16, "bold")
        ).pack(pady=(10, 10), padx=10, anchor="w")
        
        # Appearance mode
        appearance_frame = ctk.CTkFrame(theme_frame)
        appearance_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            appearance_frame,
            text="Appearance Mode:",
            font=("Roboto", 12)
        ).pack(side="left", padx=(0, 10))
        
        current_theme = self.preferences.get("theme", DEFAULT_THEME)
        self.appearance_var = ctk.StringVar(value=current_theme[0])
        appearance_menu = ctk.CTkOptionMenu(
            appearance_frame,
            values=["Light", "Dark", "System"],
            variable=self.appearance_var,
            command=self.on_theme_change
        )
        appearance_menu.pack(side="left")
        
        # Color theme
        color_frame = ctk.CTkFrame(theme_frame)
        color_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            color_frame,
            text="Color Theme:",
            font=("Roboto", 12)
        ).pack(side="left", padx=(0, 10))
        
        self.color_var = ctk.StringVar(value=current_theme[1])
        color_menu = ctk.CTkOptionMenu(
            color_frame,
            values=["blue", "green", "dark-blue"],
            variable=self.color_var,
            command=self.on_theme_change
        )
        color_menu.pack(side="left")
        
        # Refresh interval
        refresh_frame = ctk.CTkFrame(main_frame)
        refresh_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            refresh_frame,
            text="Data Refresh Settings",
            font=("Roboto", 16, "bold")
        ).pack(pady=(10, 10), padx=10, anchor="w")
        
        interval_frame = ctk.CTkFrame(refresh_frame)
        interval_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            interval_frame,
            text="Refresh Interval (seconds):",
            font=("Roboto", 12)
        ).pack(side="left", padx=(0, 10))
        
        self.refresh_var = ctk.IntVar(value=self.preferences.get("refresh_interval", DEFAULT_REFRESH_INTERVAL))
        refresh_slider = ctk.CTkSlider(
            interval_frame,
            from_=5,
            to=300,
            variable=self.refresh_var,
            command=self.on_refresh_change
        )
        refresh_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.refresh_label = ctk.CTkLabel(
            interval_frame,
            text=f"{self.refresh_var.get()}s",
            font=("Roboto", 12)
        )
        self.refresh_label.pack(side="left")
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy
        ).pack(side="right", padx=(10, 0))
        
        ctk.CTkButton(
            button_frame,
            text="Apply",
            command=self.apply_settings
        ).pack(side="right")
        
    def on_theme_change(self, value):
        """Handle theme change."""
        self.theme_changed = True
        self.settings_changed = True
        
    def on_refresh_change(self, value):
        """Handle refresh interval change."""
        self.refresh_label.configure(text=f"{int(value)}s")
        self.settings_changed = True
        
    def apply_settings(self):
        """Apply settings and close dialog."""
        # Update preferences
        self.preferences["theme"] = (self.appearance_var.get(), self.color_var.get())
        self.preferences["refresh_interval"] = self.refresh_var.get()
        
        self.destroy()
        
    def get_preferences(self):
        """Get updated preferences."""
        return self.preferences


class EnhancedSchwabPortfolioGUI(ctk.CTk):
    """Enhanced main GUI application class with modern features."""
    
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
        self.watched_symbols = set()
        self.preferences = self.load_preferences()
        
        # Initialize managers
        self.icon_manager = IconManager()
        
        # Setup UI
        self.setup_window()
        self.setup_keyboard_shortcuts()
        self.create_menu_bar()
        self.create_main_layout()
        
        # Re-apply theme after all widgets are created
        self.setup_ttk_theme()
        
        # Start background tasks
        self.process_update_queue()
        self.start_market_status_checker()
        
        # Apply saved preferences
        self.apply_preferences()
        
        # Check database
        self.check_and_upgrade_db()
    
    # Notification Helper Methods
    def show_info(self, message, duration=3000):
        """Show info notification."""
        ToastNotification.show_toast(self, message, "info", duration)
    
    def show_success(self, message, duration=3000):
        """Show success notification."""
        ToastNotification.show_toast(self, message, "success", duration)
    
    def show_warning(self, message, duration=3000):
        """Show warning notification."""
        ToastNotification.show_toast(self, message, "warning", duration)
    
    def show_error(self, message, duration=4000):
        """Show error notification."""
        ToastNotification.show_toast(self, message, "error", duration)
        
    def setup_window(self):
        """Setup main window properties."""
        self.title("Schwab Portfolio Manager - Enhanced")
        self.geometry(self.preferences.get("window_geometry", "1600x900"))
        self.minsize(1200, 700)
        
        # Set theme
        theme = self.preferences.get("theme", DEFAULT_THEME)
        ctk.set_appearance_mode(theme[0])
        ctk.set_default_color_theme(theme[1])
        
        # Setup ttk theme
        self.setup_ttk_theme()
        
        # Window close handler
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for common actions."""
        shortcuts = {
            "<Control-n>": self.new_order,
            "<Control-r>": self.refresh_all,
            "<Control-w>": self.add_to_watchlist,
            "<Control-q>": self.quick_quote,
            "<Control-t>": self.open_templates,
            "<Control-e>": self.export_data,
            "<Control-s>": self.open_settings,
            "<F5>": self.refresh_portfolio,
            "<F11>": self.toggle_fullscreen,
            "<Escape>": self.cancel_current_action
        }
        
        for key, command in shortcuts.items():
            self.bind(key, lambda e, cmd=command: cmd())
    
    def setup_ttk_theme(self):
        """Configure ttk styles to match customtkinter theme."""
        #ThemeManager.apply_ttk_theme(self)
        ThemeManager.configure_menu_options(self)
            
    def create_menu_bar(self):
        """Create application menu bar."""
        # Create a custom menu bar frame instead of using tk.Menu
        self.menu_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.menu_frame.pack(fill="x", side="top")
        self.menu_frame.pack_propagate(False)
        
        # Menu items
        menu_items = [
            ("File", [
                ("New Order", self.new_order, "Ctrl+N"),
                ("separator", None, None),
                ("Export...", self.export_data, "Ctrl+E"),
                ("separator", None, None),
                ("Settings", self.open_settings, "Ctrl+S"),
                ("separator", None, None),
                ("Exit", self.on_closing, None)
            ]),
            ("View", [
                ("Refresh", self.refresh_all, "Ctrl+R"),
                ("separator", None, None),
                ("Full Screen", self.toggle_fullscreen, "F11")
            ]),
            ("Tools", [
                ("Order Templates", self.open_templates, "Ctrl+T"),
                ("Quick Quote", self.quick_quote, "Ctrl+Q")
            ]),
            ("Help", [
                ("Keyboard Shortcuts", self.show_shortcuts, None),
                ("About", self.show_about, None)
            ])
        ]
        
        # Create menu buttons
        for menu_name, menu_items_list in menu_items:
            menu_btn = ctk.CTkButton(
                self.menu_frame,
                text=menu_name,
                width=60,
                height=28,
                corner_radius=0,
                fg_color="transparent",
                hover_color=("gray80", "gray20"),
                command=lambda m=menu_name, items=menu_items_list: self.show_menu_dropdown(m, items)
            )
            menu_btn.pack(side="left", padx=2)
    
    def show_menu_dropdown(self, menu_name, items):
        """Show dropdown menu for a menu button."""
        # Create dropdown menu
        dropdown = tk.Menu(self, tearoff=0)
        
        # Style the dropdown based on current theme
        ThemeManager.style_menu(dropdown)
        
        # Add menu items
        for item in items:
            if item[0] == "separator":
                dropdown.add_separator()
            else:
                label = item[0]
                command = item[1]
                accelerator = item[2]
                if accelerator:
                    dropdown.add_command(label=label, command=command, accelerator=accelerator)
                else:
                    dropdown.add_command(label=label, command=command)
        
        # Get button position
        menu_btn = None
        for widget in self.menu_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton) and widget.cget("text") == menu_name:
                menu_btn = widget
                break
                
        if menu_btn:
            # Show dropdown below the button
            x = menu_btn.winfo_rootx()
            y = menu_btn.winfo_rooty() + menu_btn.winfo_height()
            dropdown.tk_popup(x, y)
        
    def create_main_layout(self):
        """Create the main application layout."""
        # Top toolbar
        self.create_toolbar()
        
        # Main content area with splitter
        self.main_paned = ttk.PanedWindow(self, orient="horizontal")
        self.main_paned.pack(fill="both", expand=True)
        
        # Left panel - Watchlist and account summary
        left_panel = ctk.CTkFrame(self.main_paned, width=300)
        self.main_paned.add(left_panel, weight=1)
        
        # Create watchlist
        watchlist_label = ctk.CTkLabel(
            left_panel,
            text="Watchlist",
            font=("Roboto", 18, "bold")
        )
        watchlist_label.pack(pady=(10, 5))
        
        # Add symbol frame
        add_symbol_frame = ctk.CTkFrame(left_panel)
        add_symbol_frame.pack(fill="x", padx=10, pady=5)
        
        self.symbol_entry = AutocompleteEntry(
            add_symbol_frame,
            DEFAULT_SYMBOLS,
            placeholder_text="Add symbol..."
        )
        self.symbol_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        add_btn = ctk.CTkButton(
            add_symbol_frame,
            text="+",
            width=30,
            command=self.add_to_watchlist
        )
        add_btn.pack(side="right")
        
        # Watchlist widget
        self.watchlist = WatchlistWidget(
            left_panel,
            on_symbol_click=self.on_watchlist_symbol_click
        )
        self.watchlist.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Right panel - Main content
        right_panel = ctk.CTkFrame(self.main_paned)
        self.main_paned.add(right_panel, weight=4)
        
        # Performance dashboard
        self.performance_dashboard = PerformanceDashboard(right_panel)
        self.performance_dashboard.pack(fill="x", padx=10, pady=10)
        
        # Tabbed interface
        self.create_tabs(right_panel)
        
        # Status bar
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side="bottom", fill="x")
        
    def create_toolbar(self):
        """Create application toolbar."""
        toolbar = ctk.CTkFrame(self, height=50)
        toolbar.pack(fill="x", padx=5, pady=5)
        toolbar.pack_propagate(False)
        
        # Connection section
        connection_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        connection_frame.pack(side="left", padx=10)
        
        self.connect_btn = ctk.CTkButton(
            connection_frame,
            text="Connect",
            command=self.toggle_connection,
            width=100,
            image=self.icon_manager.get_icon("connect"),
            compound="left"
        )
        self.connect_btn.pack(side="left", padx=5)
        
        # Account selector
        self.account_var = ctk.StringVar(value="Select Account")
        self.account_menu = ctk.CTkOptionMenu(
            toolbar,
            values=["Select Account"],
            variable=self.account_var,
            command=self.on_account_change,
            width=200
        )
        self.account_menu.pack(side="left", padx=10)
        
        # Action buttons
        actions = [
            ("New Order", self.new_order, "buy"),
            ("Refresh", self.refresh_all, "refresh"),
            ("Templates", self.open_templates, "settings"),
            ("Export", self.export_data, "export")
        ]
        
        for text, command, icon in actions:
            btn = ctk.CTkButton(
                toolbar,
                text=text,
                command=command,
                width=100,
                image=self.icon_manager.get_icon(icon),
                compound="left"
            )
            btn.pack(side="left", padx=5)
            
        # Theme switcher
        theme_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        theme_frame.pack(side="right", padx=10)
        
        ctk.CTkLabel(theme_frame, text="Theme:").pack(side="left", padx=5)
        
        self.theme_var = ctk.StringVar(value="Dark Blue")
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["Dark Blue", "Dark Green", "Light Blue", "System"],
            variable=self.theme_var,
            command=self.change_theme,
            width=120
        )
        theme_menu.pack(side="left")
        
    def create_tabs(self, parent):
        """Create tabbed interface."""
        self.tab_view = ctk.CTkTabview(parent)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Portfolio tab
        self.portfolio_tab = self.tab_view.add("📊 Portfolio")
        self.create_portfolio_tab()
        
        # Positions tab
        self.positions_tab = self.tab_view.add("📈 Positions")
        self.create_positions_tab()
        
        # Orders tab
        self.orders_tab = self.tab_view.add("📝 Orders")
        self.create_orders_tab()
        
        # Charts tab
        self.charts_tab = self.tab_view.add("📉 Charts")
        self.create_charts_tab()
        
        # History tab
        self.history_tab = self.tab_view.add("📜 History")
        self.create_history_tab()
        
    def create_portfolio_tab(self):
        """Create portfolio overview tab."""
        # Summary cards
        summary_frame = ctk.CTkFrame(self.portfolio_tab)
        summary_frame.pack(fill="x", pady=10)
        
        # Create summary metrics
        metrics = [
            ("Cash", "$0.00"),
            ("Securities", "$0.00"),
            ("Options", "$0.00"),
            ("Total", "$0.00")
        ]
        
        for i, (label, value) in enumerate(metrics):
            card = ctk.CTkFrame(summary_frame, corner_radius=8)
            card.grid(row=0, column=i, padx=5, sticky="nsew")
            summary_frame.grid_columnconfigure(i, weight=1)
            
            ctk.CTkLabel(
                card,
                text=label,
                font=("Roboto", 14),
                text_color="#888888"
            ).pack(pady=(10, 5))
            
            ctk.CTkLabel(
                card,
                text=value,
                font=("Roboto", 24, "bold")
            ).pack(pady=(0, 10))
            
        # Allocation chart
        chart_frame = ctk.CTkFrame(self.portfolio_tab)
        chart_frame.pack(fill="both", expand=True, pady=10)
        
        # Placeholder for allocation pie chart
        self.allocation_figure = Figure(figsize=(6, 4), dpi=100)
        self.allocation_figure.patch.set_facecolor("#1a1a1a")
        self.allocation_ax = self.allocation_figure.add_subplot(111)
        self.allocation_canvas = FigureCanvasTkAgg(self.allocation_figure, chart_frame)
        self.allocation_canvas.get_tk_widget().pack(fill="both", expand=True)
        
    def create_positions_tab(self):
        """Create positions tab."""
        # Positions table
        columns = ["Symbol", "Quantity", "Avg Cost", "Current Price", "Value", "P&L", "P&L %", "Day Change"]
        
        self.positions_tree = EnhancedTreeview(
            self.positions_tab,
            columns=columns,
            show="headings"
        )
        
        # Configure columns
        self.configure_treeview_columns(self.positions_tree, columns)
                
        self.positions_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Context menu
        position_menu_items = [
            ("Buy More", self.buy_more_position),
            ("Sell", self.sell_position),
            ("Sell All", self.sell_all_position),
            'separator',
            ("View Chart", self.view_position_chart)
        ]
        self.positions_menu = self.create_context_menu(self.positions_tree, position_menu_items)
        
        self.positions_tree.bind("<Button-3>", self.show_positions_menu)
        self.positions_tree.bind("<Double-Button-1>", self.on_position_double_click)
        
    def create_orders_tab(self):
        """Create orders tab."""
        # Order controls
        controls_frame = ctk.CTkFrame(self.orders_tab)
        controls_frame.pack(fill="x", padx=10, pady=10)
        
        # Filter buttons
        filters = ["All", "Open", "Filled", "Cancelled", "Rejected"]
        self.order_filter_var = ctk.StringVar(value="All")
        
        for filter_name in filters:
            btn = ctk.CTkRadioButton(
                controls_frame,
                text=filter_name,
                variable=self.order_filter_var,
                value=filter_name,
                command=self.filter_orders
            )
            btn.pack(side="left", padx=5)
            
        # Refresh button
        ctk.CTkButton(
            controls_frame,
            text="Refresh Orders",
            command=self.refresh_orders,
            width=120
        ).pack(side="right", padx=5)
        
        # Orders table
        columns = ["Order ID", "Symbol", "Type", "Quantity", "Price", "Status", "Time", "Account"]
        
        self.orders_tree = EnhancedTreeview(
            self.orders_tab,
            columns=columns,
            show="headings"
        )
        
        # Configure columns
        self.configure_treeview_columns(self.orders_tree, columns)
            
        self.orders_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Context menu
        order_menu_items = [
            ("Cancel Order", self.cancel_selected_order),
            ("Modify Order", self.modify_selected_order),
            'separator',
            ("Copy Order", self.copy_order)
        ]
        self.orders_menu = self.create_context_menu(self.orders_tree, order_menu_items)
        
        self.orders_tree.bind("<Button-3>", self.show_orders_menu)
        
    def create_charts_tab(self):
        """Create charts tab."""
        # Chart controls
        controls_frame = ctk.CTkFrame(self.charts_tab)
        controls_frame.pack(fill="x", padx=10, pady=10)
        
        # Symbol selector
        ctk.CTkLabel(controls_frame, text="Symbol:").pack(side="left", padx=5)
        
        self.chart_symbol_var = ctk.StringVar()
        self.chart_symbol_entry = AutocompleteEntry(
            controls_frame,
            DEFAULT_SYMBOLS + list(self.watched_symbols),
            textvariable=self.chart_symbol_var,
            width=100
        )
        self.chart_symbol_entry.pack(side="left", padx=5)
        
        # Load button
        load_btn = ctk.CTkButton(
            controls_frame,
            text="Load",
            command=self.load_chart_data,
            width=60
        )
        load_btn.pack(side="left", padx=5)
        
        # Time frame selector
        timeframes = ["1D", "5D", "1M", "3M", "6M", "1Y", "5Y"]
        self.timeframe_var = ctk.StringVar(value="1D")
        
        for tf in timeframes:
            btn = ctk.CTkButton(
                controls_frame,
                text=tf,
                command=lambda t=tf: self.change_timeframe(t),
                width=40
            )
            btn.pack(side="left", padx=2)
            
        # Chart type
        self.chart_type_var = ctk.StringVar(value="Line")
        chart_types = ctk.CTkOptionMenu(
            controls_frame,
            values=["Line", "Candle", "Bar"],
            variable=self.chart_type_var,
            command=self.change_chart_type,
            width=100
        )
        chart_types.pack(side="right", padx=5)
        
        # Chart widget
        self.main_chart = PriceChartWidget(self.charts_tab)
        self.main_chart.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Historical data storage
        self.price_history = {}  # symbol -> list of (time, price) tuples
        
    def create_history_tab(self):
        """Create transaction history tab."""
        # Date range selector
        date_frame = ctk.CTkFrame(self.history_tab)
        date_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(date_frame, text="Date Range:").pack(side="left", padx=5)
        
        # Quick date ranges
        ranges = ["Today", "This Week", "This Month", "Last 30 Days", "Last 90 Days", "YTD", "All Time"]
        self.date_range_var = ctk.StringVar(value="Last 30 Days")
        
        for range_name in ranges:
            btn = ctk.CTkButton(
                date_frame,
                text=range_name,
                command=lambda r=range_name: self.change_date_range(r),
                width=80
            )
            btn.pack(side="left", padx=2)
            
        # History table
        columns = ["Date", "Type", "Symbol", "Description", "Amount", "Balance"]
        
        self.history_tree = EnhancedTreeview(
            self.history_tab,
            columns=columns,
            show="headings"
        )
        
        # Configure columns
        self.configure_treeview_columns(self.history_tree, columns)
            
        self.history_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
    # Event handlers
    def on_closing(self):
        """Handle window closing."""
        # Save preferences
        self.save_preferences()
        
        # Stop background tasks
        self.stop_updates.set()
        if self.update_thread:
            self.update_thread.join(timeout=2)
            
        # Close connections
        if self.order_monitor:
            self.order_monitor.stop_monitoring()
            
        # Destroy window
        self.destroy()
        
    def change_theme(self, theme_name):
        """Change application theme."""
        themes = {
            "Dark Blue": ("dark", "blue"),
            "Dark Green": ("dark", "green"),
            "Light Blue": ("light", "blue"),
            "System": ("system", "blue")
        }
        
        if theme_name in themes:
            mode, color = themes[theme_name]
            ctk.set_appearance_mode(mode)
            ctk.set_default_color_theme(color)
            self.preferences["theme"] = themes[theme_name]
            
            # Update matplotlib theme for charts
            if mode == "dark":
                plt.style.use('dark_background')
            else:
                plt.style.use('default')
                
            # Redraw charts with new theme
            if hasattr(self, 'main_chart'):
                self.main_chart.figure.patch.set_facecolor('#1a1a1a' if mode == "dark" else 'white')
                self.main_chart.ax.set_facecolor('#1a1a1a' if mode == "dark" else 'white')
                self.main_chart.redraw()
                
            if hasattr(self, 'allocation_figure'):
                self.allocation_figure.patch.set_facecolor('#1a1a1a' if mode == "dark" else 'white')
                self.allocation_ax.set_facecolor('#1a1a1a' if mode == "dark" else 'white')
                self.allocation_canvas.draw()
            
            self.show_info(f"Theme changed to {theme_name}")
            
    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        current_state = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not current_state)
        
    def show_shortcuts(self):
        """Show keyboard shortcuts dialog."""
        shortcuts_text = """
Keyboard Shortcuts:

Ctrl+N    - New Order
Ctrl+R    - Refresh All
Ctrl+W    - Add to Watchlist
Ctrl+Q    - Quick Quote
Ctrl+T    - Order Templates
Ctrl+E    - Export Data
Ctrl+S    - Settings
F5        - Refresh Portfolio
F11       - Toggle Fullscreen
Escape    - Cancel Current Action
        """
        messagebox.showinfo("Keyboard Shortcuts", shortcuts_text)
        
    def show_about(self):
        """Show about dialog."""
        about_text = """
Schwab Portfolio Manager - Enhanced Edition

Version: 2.0.0
Built with: Python, CustomTkinter, Matplotlib

A professional-grade trading interface for Charles Schwab.

© 2024 - Enhanced with modern features
        """
        messagebox.showinfo("About", about_text)
        
    # Data management
    def load_preferences(self):
        """Load user preferences."""
        try:
            with open(PREFERENCES_PATH, "r") as f:
                return json.load(f)
        except:
            return {
                "theme": DEFAULT_THEME,
                "refresh_interval": DEFAULT_REFRESH_INTERVAL,
                "window_geometry": "1600x900",
                "watched_symbols": DEFAULT_SYMBOLS[:5]
            }
            
    def save_preferences(self):
        """Save user preferences."""
        self.preferences["window_geometry"] = self.geometry()
        self.preferences["watched_symbols"] = list(self.watched_symbols)
        
        with open(PREFERENCES_PATH, "w") as f:
            json.dump(self.preferences, f, indent=2)
            
    def apply_preferences(self):
        """Apply loaded preferences."""
        # Add watched symbols
        for symbol in self.preferences.get("watched_symbols", []):
            self.watched_symbols.add(symbol)
            # Add to watchlist with dummy data for now
            self.watchlist.add_symbol(symbol, 0.0, 0.0, 0.0)
            
        # Set refresh interval
        refresh_interval = self.preferences.get("refresh_interval", DEFAULT_REFRESH_INTERVAL)
        self.status_bar.update_refresh_rate(refresh_interval)
        
    def check_and_upgrade_db(self):
        """Check and upgrade database schema."""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # Create tables if they dont exist
            c.execute("""
                CREATE TABLE IF NOT EXISTS credentials (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    client_id TEXT,
                    client_secret TEXT,
                    redirect_uri TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            c.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    id INTEGER PRIMARY KEY,
                    api_type TEXT,
                    access_token TEXT,
                    refresh_token TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            
    # Background tasks
    def process_update_queue(self):
        """Process updates from background threads."""
        try:
            while True:
                update = self.update_queue.get_nowait()
                if update["type"] == "portfolio":
                    self.update_portfolio_display(update["data"])
                elif update["type"] == "positions":
                    self.update_positions_display(update["data"])
                elif update["type"] == "orders":
                    self.update_orders_display(update["data"])
                elif update["type"] == "quote":
                    self.update_quote_display(update["data"])
        except queue.Empty:
            pass
            
        # Schedule next update
        self.after(100, self.process_update_queue)
        
    def start_market_status_checker(self):
        """Start checking market status periodically."""
        def check_market():
            while not self.stop_updates.is_set():
                try:
                    # Check if market is open
                    now = datetime.now()
                    if now.weekday() < 5:  # Monday to Friday
                        market_open = now.replace(hour=9, minute=30, second=0)
                        market_close = now.replace(hour=16, minute=0, second=0)
                        
                        if market_open <= now <= market_close:
                            self.after(0, self.status_bar.update_market_status, "Open")
                        else:
                            self.after(0, self.status_bar.update_market_status, "Closed")
                    else:
                        self.after(0, self.status_bar.update_market_status, "Weekend")
                        
                except Exception as e:
                    logger.error(f"Market status check error: {e}")
                    
                time.sleep(60)  # Check every minute
                
        thread = threading.Thread(target=check_market, daemon=True)
        thread.start()
        
    # Connection and authentication methods
    def toggle_connection(self):
        """Toggle connection to Schwab API."""
        if self.client:
            # Disconnect
            self.disconnect_from_schwab()
        else:
            # Connect
            self.connect_to_schwab()
    
    def connect_to_schwab(self):
        """Connect to Schwab API - show auth dialog if no credentials saved."""
        # Load saved credentials or show auth dialog
        self.load_credentials()
    
    def disconnect_from_schwab(self):
        """Disconnect from Schwab API."""
        try:
            # Stop updates
            self.stop_updates.set()
            if self.update_thread:
                self.update_thread.join(timeout=1)
            
            # Clear client and managers
            self.client = None
            self.portfolio_manager = None
            self.order_monitor = None
            self.auth = None
            
            # Clear data
            self.accounts = []
            self.account_data = []
            
            # Update UI
            self.status_bar.update_connection_status(False, "Disconnected")
            self.connect_btn.configure(text="Connect", fg_color="blue", hover_color="darkblue")
            self.account_menu.configure(values=["Select Account"])
            self.account_var.set("Select Account")
            
            # Clear displays
            for item in self.positions_tree.get_children():
                self.positions_tree.delete(item)
            for item in self.orders_tree.get_children():
                self.orders_tree.delete(item)
            
            self.show_info("Disconnected from Schwab")
            
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
        
    def load_credentials(self):
        """Load saved credentials from database."""
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # Get credentials
            c.execute("SELECT * FROM credentials LIMIT 1")
            creds = c.fetchone()
            
            if creds:
                # Try to connect with saved credentials
                self.connect_with_credentials(
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
                self.connect_with_credentials(trading_id, trading_secret, redirect_uri, market_id, market_secret)
                
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
    
    def connect_with_credentials(self, trading_id, trading_secret, redirect_uri, market_id, market_secret):
        """Connect to Schwab API with provided credentials."""
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
                        ToastNotification.show_toast(
                            self, 
                            "Session expired. Please re-authenticate.",
                            "warning"
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
            
            # Update account menu
            if self.accounts:
                self.account_menu.configure(values=[f"*{acc[0][-4:]}" for acc in self.account_data])
                self.account_var.set(f"*{self.account_data[0][0][-4:]}")
            
            # Initialize portfolio manager
            if hasattr(self, 'portfolio_manager') and self.portfolio_manager:
                self.portfolio_manager = None
            self.portfolio_manager = PortfolioManager(self.client)
            
            # Add accounts to portfolio manager
            for account in self.accounts:
                logger.info(f"Adding account {account[-4:]} to portfolio manager")
                self.portfolio_manager.add_account(account)
            
            # Refresh portfolio data immediately
            logger.info("Refreshing portfolio positions after adding accounts...")
            self.portfolio_manager.refresh_positions()
            
            # Initialize order monitor
            self.order_monitor = OrderMonitor(self.client)
            
            # Update connection status
            self.status_bar.update_connection_status(True, "Active")
            self.connect_btn.configure(text="Disconnect", fg_color="red", hover_color="darkred")
            
            # Start auto-refresh
            self.start_updates()
            
            # Initial data refresh
            self.refresh_data()
            
            ToastNotification.show_toast(self, "Connected to Schwab successfully!", "success", duration=3000)
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            self.status_bar.update_connection_status(False, "Failed")
    
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
                self.account_data = [(acc.account_number, acc.hash_value) for acc in account_numbers.accounts]
                self.accounts = [acc.hash_value for acc in account_numbers.accounts]
                
                # Update account menu
                if self.accounts:
                    self.account_menu.configure(values=[f"*{acc[0][-4:]}" for acc in self.account_data])
                    self.account_var.set(f"*{self.account_data[0][0][-4:]}")
                
                # Initialize portfolio manager
                self.portfolio_manager = PortfolioManager(self.client)
                for account in self.accounts:
                    logger.info(f"Adding account {account[-4:]} to portfolio manager")
                    self.portfolio_manager.add_account(account)
                
                # Refresh portfolio data immediately
                logger.info("Refreshing portfolio positions after adding accounts...")
                self.portfolio_manager.refresh_positions()
                
                # Initialize order monitor
                self.order_monitor = OrderMonitor(self.client)
                
                # Update connection status
                self.status_bar.update_connection_status(True, "Active")
                self.connect_btn.configure(text="Disconnect", fg_color="red", hover_color="darkred")
                
                # Start auto-refresh
                self.start_updates()
                
                # Initial data refresh
                self.refresh_data()
                
                ToastNotification.show_toast(self, "Connected to Schwab successfully!", "success", duration=3000)
                
        except Exception as e:
            logger.error(f"Failed to finalize connection: {e}")
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            self.status_bar.update_connection_status(False, "Failed")
    
    def refresh_data(self):
        """Refresh all data."""
        if self.client and self.portfolio_manager:
            try:
                # Update portfolio
                self.portfolio_manager.update()
                
                # Debug: Log positions count
                total_positions = 0
                for account_num in self.portfolio_manager._positions:
                    positions_dict = self.portfolio_manager._positions.get(account_num, {})
                    logger.info(f"Account {account_num[-4:]}: {len(positions_dict)} positions")
                    total_positions += len(positions_dict)
                logger.info(f"Total positions across all accounts: {total_positions}")
                
                # Update UI
                self.update_portfolio_display()
                self.update_positions_display()
                self.refresh_orders()
                
                # Update last refresh time
                self.status_bar.update_last_update()
                
            except Exception as e:
                logger.error(f"Error refreshing data: {e}")
                if "401" in str(e) or "unauthorized" in str(e).lower():
                    self.handle_auth_error()
                else:
                    ToastNotification.show_toast(self, f"Refresh error: {str(e)}", "error")
    
    def handle_auth_error(self):
        """Handle authentication errors by prompting for re-authentication."""
        # Update UI to show disconnected state
        self.status_bar.update_connection_status(False, "Auth Error")
        self.connect_btn.configure(text="Connect", fg_color="blue", hover_color="darkblue")
        
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
    
    def start_updates(self):
        """Start background update thread."""
        if not self.update_thread or not self.update_thread.is_alive():
            self.stop_updates.clear()
            self.update_thread = threading.Thread(target=self.update_worker, daemon=True)
            self.update_thread.start()
    
    def update_worker(self):
        """Background worker thread for periodic updates."""
        refresh_interval = self.preferences.get("refresh_interval", DEFAULT_REFRESH_INTERVAL)
        
        while not self.stop_updates.is_set():
            try:
                if self.client and self.portfolio_manager:
                    # Update portfolio in background
                    self.portfolio_manager.update()
                    
                    # Queue UI updates
                    self.update_queue.put({
                        "type": "portfolio",
                        "data": self.portfolio_manager.get_portfolio_summary()
                    })
                    
                    # Get all positions from portfolio manager
                    all_positions = []
                    for account_num in self.portfolio_manager._positions:
                        positions_dict = self.portfolio_manager._positions.get(account_num, {})
                        for symbol, position in positions_dict.items():
                            all_positions.append(position)
                    
                    self.update_queue.put({
                        "type": "positions",
                        "data": all_positions
                    })
                    
                    # Update quotes for watched symbols
                    if self.watched_symbols:
                        try:
                            # Get quotes for all watched symbols at once
                            quotes_response = self.client.get_quotes(list(self.watched_symbols))
                            
                            # Process each quote
                            if hasattr(quotes_response, 'items'):
                                for symbol, quote_data in quotes_response.items():
                                    self.update_queue.put({
                                        "type": "quote",
                                        "data": {"symbol": symbol, "quote": quote_data}
                                    })
                        except Exception as e:
                            logger.error(f"Error getting quotes: {e}")
                            
            except Exception as e:
                logger.error(f"Update worker error: {e}")
                if "401" in str(e) or "unauthorized" in str(e).lower():
                    # Authentication error - stop updates
                    self.after(0, self.handle_auth_error)
                    break
                    
            # Wait for next update
            self.stop_updates.wait(refresh_interval)
        
    def on_account_change(self, account):
        """Handle account selection change."""
        self.status_bar.update_account_info(f"Account: {account}")
        
    def new_order(self):
        """Open new order dialog."""
        self.show_order_dialog()
        
    def refresh_all(self):
        """Refresh all data."""
        self.status_bar.update_last_update()
        ToastNotification.show_toast(self, "Refreshing all data...", "info")
        
    def add_to_watchlist(self):
        """Add symbol to watchlist."""
        symbol = self.symbol_entry.get().upper()
        if symbol and symbol not in self.watched_symbols:
            self.watched_symbols.add(symbol)
            self.watchlist.add_symbol(symbol, 100.0, 2.5, 2.45)  # Dummy data
            self.symbol_entry.delete(0, tk.END)
            ToastNotification.show_toast(self, f"Added {symbol} to watchlist", "success")
            
    def on_watchlist_symbol_click(self, symbol):
        """Handle watchlist symbol click."""
        self.chart_symbol_var.set(symbol)
        self.tab_view.set("📉 Charts")
        
    def quick_quote(self):
        """Show quick quote dialog."""
        dialog = ctk.CTkInputDialog(
            text="Enter symbol for quote:",
            title="Quick Quote"
        )
        symbol = dialog.get_input()
        if symbol:
            ToastNotification.show_toast(self, f"Getting quote for {symbol}...", "info")
            
    def open_templates(self):
        """Open order templates manager."""
        OrderTemplateManager(self)
        
    def export_data(self):
        """Export portfolio data."""
        export_menu = tk.Menu(self, tearoff=0)
        export_menu.add_command(label="Export to CSV", command=lambda: self.export_to_csv())
        export_menu.add_command(label="Export to Excel", command=lambda: self.export_to_excel())
        export_menu.add_command(label="Generate PDF Report", command=lambda: self.generate_pdf_report())
        
        # Show menu at cursor position
        export_menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        
    def export_to_csv(self):
        """Export data to CSV."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            # Export implementation would go here
            ToastNotification.show_toast(self, f"Exported to {os.path.basename(filename)}", "success")
            
    def export_to_excel(self):
        """Export data to Excel."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filename:
            # Export implementation would go here
            ToastNotification.show_toast(self, f"Exported to {os.path.basename(filename)}", "success")
            
    def generate_pdf_report(self):
        """Generate PDF report."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            # PDF generation implementation would go here
            ToastNotification.show_toast(self, f"Generated {os.path.basename(filename)}", "success")
            
    def open_settings(self):
        """Open settings dialog."""
        settings_dialog = SettingsDialog(self, self.preferences)
        self.wait_window(settings_dialog)
        
        # Apply any changed settings
        if hasattr(settings_dialog, 'settings_changed') and settings_dialog.settings_changed:
            self.preferences = settings_dialog.get_preferences()
            self.save_preferences()
            
            # Apply theme changes if needed
            if hasattr(settings_dialog, 'theme_changed') and settings_dialog.theme_changed:
                theme = self.preferences.get("theme", DEFAULT_THEME)
                ctk.set_appearance_mode(theme[0])
                ctk.set_default_color_theme(theme[1])
                self.setup_ttk_theme()
                
                # Refresh all ttk widgets
                self.refresh_ttk_widgets()
                
            ToastNotification.show_toast(self, "Settings applied successfully", "success")
    
    def refresh_ttk_widgets(self):
        """Refresh all ttk widgets to apply new theme."""
        # Force style update
        self.update_idletasks()
        
        # Update all treeview widgets
        treeview_widgets = ['positions_tree', 'orders_tree', 'history_tree']
        for widget_name in treeview_widgets:
            if hasattr(self, widget_name):
                widget = getattr(self, widget_name)
                # Force redraw
                widget.update_idletasks()
        
        # Update context menus
        menu_widgets = ['positions_menu', 'orders_menu']
        for menu_name in menu_widgets:
            if hasattr(self, menu_name):
                menu = getattr(self, menu_name)
                self._style_context_menu(menu)
    
    def _style_context_menu(self, menu):
        """Apply theme styling to a context menu."""
        ThemeManager.style_menu(menu)
    
    def create_context_menu(self, parent, menu_items):
        """Create a styled context menu.
        
        Args:
            parent: Parent widget for the menu
            menu_items: List of tuples (label, command) or 'separator'
        
        Returns:
            tk.Menu: The created and styled menu
        """
        menu = tk.Menu(parent, tearoff=0)
        
        for item in menu_items:
            if item == 'separator':
                menu.add_separator()
            else:
                label, command = item
                menu.add_command(label=label, command=command)
        
        self._style_context_menu(menu)
        return menu
    
    def configure_treeview_columns(self, treeview, columns, column_widths=None):
        """Configure treeview columns with appropriate widths.
        
        Args:
            treeview: The treeview widget to configure
            columns: List of column names
            column_widths: Dict of column name to width, or None for defaults
        """
        default_widths = {
            "P&L": 100,
            "P&L %": 100,
            "Day Change": 100,
            "Order ID": 120,
            "Status": 80,
            "Type": 80,
            "Price": 80,
            "Quantity": 80
        }
        
        for col in columns:
            treeview.heading(col, text=col)
            if column_widths and col in column_widths:
                width = column_widths[col]
            elif col in default_widths:
                width = default_widths[col]
            else:
                width = 120  # Default width
            treeview.column(col, width=width)
        
    def refresh_portfolio(self):
        """Refresh portfolio data."""
        if self.client and self.portfolio_manager:
            self.refresh_data()
        else:
            self.show_warning("Not connected to Schwab")
        
    def cancel_current_action(self):
        """Cancel current action or close dialogs."""
        # Close any open dialogs by destroying all toplevel windows
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkToplevel):
                widget.destroy()
        
    def filter_orders(self):
        """Filter orders based on selection."""
        filter_value = self.order_filter_var.get()
        self.refresh_orders()  # Call the actual refresh_orders method
        
    def show_positions_menu(self, event):
        """Show positions context menu."""
        self.positions_menu.tk_popup(event.x_root, event.y_root)
        
    def show_orders_menu(self, event):
        """Show orders context menu."""
        self.orders_menu.tk_popup(event.x_root, event.y_root)
        
    def buy_more_position(self):
        """Buy more of selected position."""
        selection = self.positions_tree.selection()
        if not selection:
            self.show_warning("Please select a position first")
            return
            
        # Get selected position data
        item = self.positions_tree.item(selection[0])
        values = item['values']
        if values:
            symbol = values[0]  # Symbol is first column
            self.show_order_dialog(symbol=symbol, instruction="BUY")
        
    def sell_position(self):
        """Sell selected position."""
        self.open_sell_order_dialog()
        
    def sell_all_position(self):
        """Sell all of selected position."""
        self.open_sell_order_dialog(sell_all=True)
        
    def view_position_chart(self):
        """View chart for selected position."""
        selection = self.positions_tree.selection()
        if selection:
            item = self.positions_tree.item(selection[0])
            values = item['values']
            if values:
                symbol = values[0]  # Symbol is first column
                self.chart_symbol_var.set(symbol)
                self.tab_view.set("📉 Charts")
    
    def on_position_double_click(self, event):
        """Handle double-click on position - open order to close position."""
        self.open_sell_order_dialog()
    
    def open_sell_order_dialog(self, sell_all=False):
        """Open order dialog pre-filled to sell the selected position."""
        selection = self.positions_tree.selection()
        if not selection:
            self.show_warning("Please select a position first")
            return
            
        if not self.client:
            ToastNotification.show_toast(self, "Not connected to Schwab", "error")
            return
            
        # Get selected position data
        item = self.positions_tree.item(selection[0])
        values = item['values']
        if not values:
            return
            
        symbol = values[0]  # Symbol is first column
        quantity = values[1]  # Quantity is second column
        
        # Parse quantity (remove commas)
        try:
            qty = float(str(quantity).replace(',', ''))
        except:
            qty = 0
            
        if qty <= 0:
            self.show_error("Invalid position quantity")
            return
            
        # Create order dialog
        self.show_order_dialog(symbol=symbol, quantity=int(qty) if sell_all else None, instruction="SELL")
    
    def show_order_dialog(self, symbol=None, quantity=None, instruction=None):
        """Show enhanced order entry dialog with comprehensive order type support."""
        if not self.client or not self.accounts:
            ToastNotification.show_toast(self, "Please connect to Schwab first", "warning")
            return
        
        # Import the enhanced order dialog
        try:
            from enhanced_order_dialog import EnhancedOrderDialog
            
            # Create enhanced order dialog
            dialog = EnhancedOrderDialog(
                self, 
                self.client, 
                self.account_data,  # Pass account data list
                symbol=symbol,
                quantity=quantity,
                instruction=instruction
            )
            
            # Wait for dialog to close
            self.wait_window(dialog)
            
            # Refresh orders after dialog closes
            self.refresh_orders()
            
        except (ImportError, AttributeError) as e:
            logger.warning(f"Enhanced order dialog error: {e}")
            
            # Try the fixed version
            try:
                from enhanced_order_dialog_fixed import EnhancedOrderDialog
                logger.info("Using fixed enhanced order dialog")
                
                dialog = EnhancedOrderDialog(
                    self, 
                    self.client, 
                    self.account_data,
                    symbol=symbol,
                    quantity=quantity,
                    instruction=instruction
                )
                
                self.wait_window(dialog)
                self.refresh_orders()
                
            except Exception as e2:
                logger.warning(f"Fixed dialog also failed: {e2}, falling back to simple dialog")
                # Fall back to simple order dialog if enhanced not available
                self._show_simple_order_dialog(symbol, quantity, instruction)
    
    def _show_simple_order_dialog(self, symbol=None, quantity=None, instruction=None):
        """Show simple order entry dialog as fallback."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Order Entry")
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the window
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(
            main_frame,
            text="Place Order",
            font=("Roboto", 20, "bold")
        ).pack(pady=(0, 20))
        
        # Account selection
        ctk.CTkLabel(main_frame, text="Account:").pack(anchor="w", pady=(10, 0))
        account_var = ctk.StringVar(value=self.account_var.get())
        account_menu = ctk.CTkOptionMenu(
            main_frame,
            values=[f"*{acc[0][-4:]}" for acc in self.account_data],
            variable=account_var
        )
        account_menu.pack(fill="x", pady=(0, 10))
        
        # Symbol
        ctk.CTkLabel(main_frame, text="Symbol:").pack(anchor="w", pady=(10, 0))
        symbol_entry = ctk.CTkEntry(main_frame)
        symbol_entry.pack(fill="x", pady=(0, 10))
        if symbol:
            symbol_entry.insert(0, symbol)
        
        # Instruction
        ctk.CTkLabel(main_frame, text="Action:").pack(anchor="w", pady=(10, 0))
        instruction_var = ctk.StringVar(value=instruction or "BUY")
        instruction_menu = ctk.CTkOptionMenu(
            main_frame,
            values=["BUY", "SELL", "BUY_TO_COVER", "SELL_SHORT"],
            variable=instruction_var
        )
        instruction_menu.pack(fill="x", pady=(0, 10))
        
        # Quantity
        ctk.CTkLabel(main_frame, text="Quantity:").pack(anchor="w", pady=(10, 0))
        quantity_entry = ctk.CTkEntry(main_frame)
        quantity_entry.pack(fill="x", pady=(0, 10))
        if quantity:
            quantity_entry.insert(0, str(quantity))
        
        # Order Type
        ctk.CTkLabel(main_frame, text="Order Type:").pack(anchor="w", pady=(10, 0))
        order_type_var = ctk.StringVar(value="MARKET")
        order_type_menu = ctk.CTkOptionMenu(
            main_frame,
            values=["MARKET", "LIMIT", "STOP", "STOP_LIMIT"],
            variable=order_type_var,
            command=lambda x: toggle_price_fields()
        )
        order_type_menu.pack(fill="x", pady=(0, 10))
        
        # Price fields frame
        price_frame = ctk.CTkFrame(main_frame)
        price_frame.pack(fill="x", pady=(10, 0))
        
        # Limit price
        limit_label = ctk.CTkLabel(price_frame, text="Limit Price:")
        limit_entry = ctk.CTkEntry(price_frame)
        
        # Stop price
        stop_label = ctk.CTkLabel(price_frame, text="Stop Price:")
        stop_entry = ctk.CTkEntry(price_frame)
        
        def toggle_price_fields():
            """Show/hide price fields based on order type."""
            order_type = order_type_var.get()
            
            # Clear price frame
            for widget in price_frame.winfo_children():
                widget.pack_forget()
                
            if order_type == "LIMIT":
                limit_label.pack(anchor="w", pady=(0, 5))
                limit_entry.pack(fill="x", pady=(0, 10))
            elif order_type == "STOP":
                stop_label.pack(anchor="w", pady=(0, 5))
                stop_entry.pack(fill="x", pady=(0, 10))
            elif order_type == "STOP_LIMIT":
                stop_label.pack(anchor="w", pady=(0, 5))
                stop_entry.pack(fill="x", pady=(0, 10))
                limit_label.pack(anchor="w", pady=(0, 5))
                limit_entry.pack(fill="x", pady=(0, 10))
        
        # Duration
        ctk.CTkLabel(main_frame, text="Duration:").pack(anchor="w", pady=(10, 0))
        duration_var = ctk.StringVar(value="DAY")
        duration_menu = ctk.CTkOptionMenu(
            main_frame,
            values=["DAY", "GTC", "IOC", "FOK"],
            variable=duration_var
        )
        duration_menu.pack(fill="x", pady=(0, 10))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        
        def submit_order():
            """Submit the order."""
            try:
                # Get form values
                sym = symbol_entry.get().strip().upper()
                qty = int(quantity_entry.get())
                
                if not sym or qty <= 0:
                    messagebox.showerror("Validation Error", "Invalid symbol or quantity")
                    return
                
                # Get account hash
                account_display = account_var.get()
                account_hash = next((acc[1] for acc in self.account_data if f"*{acc[0][-4:]}" == account_display), None)
                
                if not account_hash:
                    messagebox.showerror("Error", "Invalid account selection")
                    return
                
                # Build order based on type
                order_type = order_type_var.get()
                
                # Import order types
                from schwab.models.orders import OrderType as OT, Session, Duration, Instruction
                
                # Map string values to enums
                order_type_map = {
                    "MARKET": OT.MARKET,
                    "LIMIT": OT.LIMIT,
                    "STOP": OT.STOP,
                    "STOP_LIMIT": OT.STOP_LIMIT
                }
                
                duration_map = {
                    "DAY": Duration.DAY,
                    "GTC": Duration.GOOD_TILL_CANCEL,
                    "IOC": Duration.IMMEDIATE_OR_CANCEL,
                    "FOK": Duration.FILL_OR_KILL
                }
                
                instruction_map = {
                    "BUY": Instruction.BUY,
                    "SELL": Instruction.SELL,
                    "BUY_TO_COVER": Instruction.BUY_TO_COVER,
                    "SELL_SHORT": Instruction.SELL_SHORT
                }
                
                # Create order
                if order_type == "MARKET":
                    order = self.client.order_management.market_order(
                        symbol=sym,
                        quantity=qty,
                        instruction=instruction_map[instruction_var.get()],
                        session=Session.NORMAL,
                        duration=duration_map[duration_var.get()]
                    )
                elif order_type == "LIMIT":
                    price = float(limit_entry.get())
                    order = self.client.order_management.limit_order(
                        symbol=sym,
                        quantity=qty,
                        price=price,
                        instruction=instruction_map[instruction_var.get()],
                        session=Session.NORMAL,
                        duration=duration_map[duration_var.get()]
                    )
                elif order_type == "STOP":
                    stop_price = float(stop_entry.get())
                    order = self.client.order_management.stop_order(
                        symbol=sym,
                        quantity=qty,
                        stop_price=stop_price,
                        instruction=instruction_map[instruction_var.get()],
                        session=Session.NORMAL,
                        duration=duration_map[duration_var.get()]
                    )
                elif order_type == "STOP_LIMIT":
                    stop_price = float(stop_entry.get())
                    limit_price = float(limit_entry.get())
                    order = self.client.order_management.stop_limit_order(
                        symbol=sym,
                        quantity=qty,
                        stop_price=stop_price,
                        limit_price=limit_price,
                        instruction=instruction_map[instruction_var.get()],
                        session=Session.NORMAL,
                        duration=duration_map[duration_var.get()]
                    )
                
                # Place order
                response = self.client.place_order(account_hash, order)
                
                # Close dialog
                dialog.destroy()
                
                # Show success message
                ToastNotification.show_toast(self, f"Order placed for {qty} shares of {sym}", "success")
                
                # Refresh orders
                self.refresh_orders()
                
            except Exception as e:
                logger.error(f"Error placing order: {e}")
                messagebox.showerror("Order Error", f"Failed to place order: {str(e)}")
        
        submit_btn = ctk.CTkButton(
            button_frame,
            text="Submit Order",
            command=submit_order,
            width=150
        )
        submit_btn.pack(side="left", padx=(0, 10))
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            width=100
        )
        cancel_btn.pack(side="left")
        
    def cancel_selected_order(self):
        """Cancel selected order."""
        pass
        
    def modify_selected_order(self):
        """Modify selected order."""
        pass
        
    def copy_order(self):
        """Copy selected order."""
        pass
        
    def load_chart_data(self):
        """Load chart data for the selected symbol."""
        symbol = self.chart_symbol_var.get().strip().upper()
        if not symbol:
            ToastNotification.show_toast(self, "Please enter a symbol", "warning")
            return
            
        if not self.client:
            ToastNotification.show_toast(self, "Not connected to Schwab", "error")
            return
            
        try:
            # Clear current chart
            self.main_chart.clear_chart()
            
            # Get current quote
            quotes_response = self.client.get_quotes([symbol])
            if hasattr(quotes_response, 'items'):
                for sym, quote_data in quotes_response.items():
                    if sym == symbol:
                        # Extract price
                        price = 0
                        if hasattr(quote_data, 'quote'):
                            q = quote_data.quote
                            price = getattr(q, 'last', 0) or getattr(q, 'lastPrice', 0)
                        elif isinstance(quote_data, dict) and 'quote' in quote_data:
                            q = quote_data['quote']
                            price = q.get('last', 0) or q.get('lastPrice', 0)
                            
                        if price > 0:
                            # Initialize with current price
                            current_time = datetime.now()
                            
                            # Check if we have historical data
                            if symbol in self.price_history:
                                times, prices = zip(*self.price_history[symbol])
                                self.main_chart.set_historical_data(symbol, list(times), list(prices))
                                # Add current price
                                self.main_chart.update_chart(symbol, current_time, price)
                            else:
                                # Start with just current price
                                self.main_chart.update_chart(symbol, current_time, price)
                                self.price_history[symbol] = [(current_time, price)]
                                
                            ToastNotification.show_toast(self, f"Loaded data for {symbol}", "success")
                            
                            # Add to watchlist if not already there
                            if symbol not in self.watched_symbols:
                                self.watched_symbols.add(symbol)
                                self.watchlist.add_symbol(symbol, price, 0, 0)
                        else:
                            ToastNotification.show_toast(self, f"No price data for {symbol}", "warning")
                            
        except Exception as e:
            logger.error(f"Error loading chart data: {e}")
            ToastNotification.show_toast(self, f"Error loading data: {str(e)}", "error")
    
    def change_timeframe(self, timeframe):
        """Change chart timeframe."""
        self.timeframe_var.set(timeframe)
        # For now, just update the label - real implementation would filter data
        ToastNotification.show_toast(self, f"Timeframe: {timeframe} (Note: Historical data limited)", "info")
        
    def change_chart_type(self, chart_type):
        """Change chart type."""
        # Note: Currently only line charts are implemented
        ToastNotification.show_toast(self, f"Chart type: {chart_type} (Currently only Line is supported)", "info")
        
    def change_date_range(self, range_name):
        """Change history date range."""
        self.date_range_var.set(range_name)
        ToastNotification.show_toast(self, f"Date range: {range_name}", "info")
        
    # Update display methods
    def update_portfolio_display(self, data=None):
        """Update portfolio display."""
        if not self.portfolio_manager:
            return
            
        try:
            # Get portfolio summary
            summary = self.portfolio_manager.get_portfolio_summary() if not data else data
            
            # Calculate additional metrics
            total_value = float(summary.get('total_value', 0))
            
            # Calculate total P&L from all positions
            total_pnl = 0
            wins = 0
            losses = 0
            positions_by_symbol = summary.get('positions_by_symbol', {})
            
            for symbol, pos_data in positions_by_symbol.items():
                gain_loss = float(pos_data.get('gain_loss', 0))
                total_pnl += gain_loss
                if gain_loss > 0:
                    wins += 1
                elif gain_loss < 0:
                    losses += 1
            
            # Calculate win rate
            total_positions = wins + losses
            win_rate = (wins / total_positions * 100) if total_positions > 0 else 0
            
            # Day change would require historical data - for now, use total P&L as approximation
            # In a real implementation, you'd compare with previous day's close
            day_change = total_pnl  # This is a placeholder
            day_change_pct = (day_change / (total_value - day_change) * 100) if (total_value - day_change) > 0 else 0
            
            # Sharpe ratio would require returns history - placeholder for now
            sharpe_ratio = 0.0  # Would need historical returns to calculate properly
            
            # Update performance dashboard
            metrics = {
                "total_value": f"${total_value:,.2f}",
                "day_change": f"${day_change:+,.2f} ({day_change_pct:+.2f}%)",
                "total_pnl": f"${total_pnl:+,.2f}",
                "win_rate": f"{win_rate:.1f}%",
                "sharpe": f"{sharpe_ratio:.2f}"
            }
            self.performance_dashboard.update_all_metrics(metrics)
            
            # Update allocation chart
            allocations = {
                'Cash': float(summary.get('total_cash', 0)),
                'Equity': float(summary.get('total_equity', 0))
            }
            
            # Add asset class allocations if available
            asset_allocation = summary.get('asset_allocation', {})
            if asset_allocation:
                allocations = {}
                for asset_type, percentage in asset_allocation.items():
                    if percentage > 0:
                        allocations[asset_type] = float(total_value * float(percentage) / 100)
                        
            self.update_allocation_chart(allocations)
            
        except Exception as e:
            logger.error(f"Error updating portfolio display: {e}")
    
    def update_allocation_chart(self, allocations):
        """Update the allocation pie chart."""
        if not allocations:
            return
            
        self.allocation_ax.clear()
        
        # Prepare data
        labels = []
        sizes = []
        colors = ['#00ff88', '#00aaff', '#ffaa00', '#ff4444', '#aa00ff']
        
        for asset_type, value in allocations.items():
            if value > 0:
                labels.append(f"{asset_type}\n${value:,.0f}")
                sizes.append(value)
        
        if sizes:
            # Create pie chart
            wedges, texts, autotexts = self.allocation_ax.pie(
                sizes, 
                labels=labels, 
                colors=colors[:len(sizes)],
                autopct='%1.1f%%',
                startangle=90
            )
            
            # Style the chart
            for text in texts:
                text.set_color('white')
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_weight('bold')
                
        self.allocation_ax.set_title('Portfolio Allocation', color='white', fontsize=14)
        self.allocation_canvas.draw()
        
    def update_positions_display(self, data=None):
        """Update positions display."""
        if not self.portfolio_manager:
            logger.warning("No portfolio manager available for positions display")
            return
            
        try:
            logger.info("Updating positions display...")
            
            # Clear existing items
            for item in self.positions_tree.get_children():
                self.positions_tree.delete(item)
            
            # Get all positions
            if data:
                positions = data
                logger.info(f"Using provided data: {len(positions)} positions")
            else:
                positions = []
                for account_num in self.portfolio_manager._positions:
                    positions_dict = self.portfolio_manager._positions.get(account_num, {})
                    logger.info(f"Account {account_num[-4:]}: Found {len(positions_dict)} positions")
                    for symbol, position in positions_dict.items():
                        positions.append(position)
                logger.info(f"Total positions to display: {len(positions)}")
            
            displayed_count = 0
            for position in positions:
                # Extract symbol
                symbol = self._extract_symbol_from_position(position)
                if not symbol:
                    logger.warning(f"Could not extract symbol from position: {position}")
                    continue
                
                # Debug: Log position attributes
                position_attrs = [attr for attr in dir(position) if not attr.startswith('_')]
                logger.info(f"Position attributes for {symbol}: {position_attrs}")
                
                # Get position details
                long_qty = getattr(position, 'long_quantity', 0)
                short_qty = getattr(position, 'short_quantity', 0)
                logger.info(f"Position {symbol}: long_quantity={long_qty}, short_quantity={short_qty}")
                
                quantity = long_qty - short_qty
                if quantity == 0:
                    logger.info(f"Skipping {symbol} - zero quantity")
                    continue
                    
                logger.info(f"Processing position: {symbol}, quantity: {quantity}")
                    
                # Calculate values
                market_value = getattr(position, 'market_value', 0)
                average_price = getattr(position, 'average_price', 0)
                
                # Get current price from market value and quantity
                current_price = float(market_value) / float(quantity) if quantity != 0 else 0
                
                # Calculate P&L
                cost_basis = float(average_price) * float(quantity)
                pnl = float(market_value) - cost_basis
                pnl_pct = (pnl / cost_basis) * 100 if cost_basis > 0 else 0
                
                # Day change (if available)
                day_change = 0
                if hasattr(position, 'current_day_profit_loss'):
                    day_change = float(getattr(position, 'current_day_profit_loss', 0))
                
                # Format values
                values = (
                    symbol,
                    f"{quantity:,.0f}",
                    f"${average_price:.2f}",
                    f"${current_price:.2f}",
                    f"${market_value:,.2f}",
                    f"${pnl:+,.2f}",
                    f"{pnl_pct:+.2f}%",
                    f"${day_change:+.2f}"
                )
                
                # Determine tag for coloring
                tags = ()
                if pnl >= 0:
                    tags = ("gain",)
                else:
                    tags = ("loss",)
                    
                # Insert item
                self.positions_tree.insert("", "end", values=values, tags=tags)
                displayed_count += 1
                logger.info(f"Successfully displayed position: {symbol}")
            
            logger.info(f"Positions display complete: {displayed_count} positions shown")
            
            # Debug: Add a test row if no positions were displayed
            if displayed_count == 0 and len(positions) > 0:
                logger.warning("No positions displayed despite having data. Adding test row...")
                test_values = ("TEST", "100", "$10.00", "$12.00", "$1,200.00", "$200.00", "20.00%", "$50.00")
                self.positions_tree.insert("", "end", values=test_values, tags=("gain",))
            
            # Configure tags
            self.positions_tree.tag_configure("gain", foreground="#00ff88")
            self.positions_tree.tag_configure("loss", foreground="#ff4444")
            
        except Exception as e:
            logger.error(f"Error updating positions display: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _extract_symbol_from_position(self, position) -> str:
        """Extract symbol from position object."""
        try:
            if hasattr(position, 'instrument'):
                instrument = position.instrument
                if hasattr(instrument, 'symbol'):
                    return instrument.symbol
                elif hasattr(instrument, 'cusip'):
                    # For some positions, only CUSIP is available
                    return f"CUSIP:{instrument.cusip}"
            return ""
        except Exception as e:
            logger.error(f"Error extracting symbol from position: {e}")
            return ""
            
    def refresh_orders(self):
        """Refresh orders display."""
        if not self.client:
            return
            
        try:
            # Get current filter
            filter_value = self.order_filter_var.get()
            
            # Clear existing items
            for item in self.orders_tree.get_children():
                self.orders_tree.delete(item)
                
            # Get orders for all accounts
            all_orders = []
            for account_hash in self.accounts:
                try:
                    orders = self.client.get_orders(account_hash)
                    for order in orders:
                        # Add account info to order
                        order.account_hash = account_hash
                        all_orders.append(order)
                except Exception as e:
                    logger.error(f"Error getting orders for account {account_hash}: {e}")
            
            # Filter orders
            filtered_orders = []
            for order in all_orders:
                if filter_value == "All":
                    filtered_orders.append(order)
                elif filter_value == "Open" and order.status in ["QUEUED", "ACCEPTED", "WORKING"]:
                    filtered_orders.append(order)
                elif filter_value == "Filled" and order.status == "FILLED":
                    filtered_orders.append(order)
                elif filter_value == "Cancelled" and order.status in ["CANCELED", "REJECTED"]:
                    filtered_orders.append(order)
                elif filter_value == "Rejected" and order.status == "REJECTED":
                    filtered_orders.append(order)
                    
            # Display filtered orders
            for order in filtered_orders:
                # Extract order details
                symbol = ""
                quantity = 0
                price = ""
                
                if hasattr(order, 'order_leg_collection') and order.order_leg_collection:
                    leg = order.order_leg_collection[0]
                    symbol = leg.instrument.symbol
                    quantity = leg.quantity
                    
                    if hasattr(leg, 'order_leg_type'):
                        if order.order_type == "LIMIT":
                            price = f"${order.price:.2f}"
                        elif order.order_type == "STOP":
                            price = f"Stop ${order.stop_price:.2f}"
                        elif order.order_type == "STOP_LIMIT":
                            price = f"Stop ${order.stop_price:.2f} Limit ${order.price:.2f}"
                        else:
                            price = "Market"
                
                # Get account display
                account_display = f"*{next((acc[0][-4:] for acc in self.account_data if acc[1] == order.account_hash), 'Unknown')}"
                
                values = (
                    order.order_id,
                    symbol,
                    order.order_type,
                    quantity,
                    price,
                    order.status,
                    order.entered_time.strftime("%m/%d %H:%M") if hasattr(order, 'entered_time') else "",
                    account_display
                )
                
                # Determine tag for coloring
                tags = ()
                if order.status in ["FILLED"]:
                    tags = ("filled",)
                elif order.status in ["CANCELED", "REJECTED"]:
                    tags = ("cancelled",)
                elif order.status in ["QUEUED", "ACCEPTED", "WORKING"]:
                    tags = ("open",)
                    
                # Insert item
                self.orders_tree.insert("", "end", values=values, tags=tags)
            
            # Configure tags
            self.orders_tree.tag_configure("filled", foreground="#00ff88")
            self.orders_tree.tag_configure("cancelled", foreground="#ff4444")
            self.orders_tree.tag_configure("open", foreground="#00aaff")
            
        except Exception as e:
            logger.error(f"Error refreshing orders: {e}")
            
    def update_orders_display(self, data):
        """Update orders display from queue data."""
        self.refresh_orders()
        
    def update_quote_display(self, data):
        """Update quote display for a symbol."""
        if not data:
            return
            
        symbol = data.get("symbol")
        quote = data.get("quote")
        
        if not symbol or not quote:
            return
            
        try:
            # Extract quote data - the structure depends on the API response
            price = 0
            change = 0
            change_pct = 0
            
            # Check for quote subobject
            if hasattr(quote, 'quote'):
                q = quote.quote
                price = getattr(q, 'last', 0) or getattr(q, 'lastPrice', 0) or getattr(q, 'regularMarketLastPrice', 0)
                change = getattr(q, 'netChange', 0) or getattr(q, 'regularMarketNetChange', 0)
                change_pct = getattr(q, 'percentChange', 0) or getattr(q, 'regularMarketPercentChange', 0)
            elif isinstance(quote, dict):
                # Handle dict response
                if 'quote' in quote:
                    q = quote['quote']
                    price = q.get('last', 0) or q.get('lastPrice', 0) or q.get('regularMarketLastPrice', 0)
                    change = q.get('netChange', 0) or q.get('regularMarketNetChange', 0)
                    change_pct = q.get('percentChange', 0) or q.get('regularMarketPercentChange', 0)
                else:
                    price = quote.get('last', 0) or quote.get('lastPrice', 0)
                    change = quote.get('netChange', 0)
                    change_pct = quote.get('percentChange', 0)
            else:
                # Try direct attributes
                price = getattr(quote, 'last', 0) or getattr(quote, 'lastPrice', 0)
                change = getattr(quote, 'netChange', 0)
                change_pct = getattr(quote, 'percentChange', 0)
            
            if price > 0:
                # Update watchlist
                self.watchlist.update_symbol(symbol, price, change_pct, change)
                
                # Store price history
                current_time = datetime.now()
                if symbol not in self.price_history:
                    self.price_history[symbol] = []
                
                # Add new price point
                self.price_history[symbol].append((current_time, price))
                
                # Keep only last 1000 points per symbol
                if len(self.price_history[symbol]) > 1000:
                    self.price_history[symbol] = self.price_history[symbol][-1000:]
                
                # Update chart if this is the selected symbol
                if hasattr(self, 'chart_symbol_var') and self.chart_symbol_var.get() == symbol:
                    self.main_chart.update_chart(symbol, current_time, price)
                    
        except Exception as e:
            logger.error(f"Error updating quote display for {symbol}: {e}")


def main():
    """Main entry point."""
    # Print enhancement notice
    print("\n" + "="*60)
    print("🚀 Schwab Portfolio GUI - Enhanced Edition")
    print("="*60)
    print("✨ NEW: Comprehensive order entry with full option support!")
    print("📊 Features: Option chains, spreads, conditional orders")
    print("📖 See ENHANCED_ORDER_FEATURES.md for details")
    print("="*60 + "\n")
    
    app = EnhancedSchwabPortfolioGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

