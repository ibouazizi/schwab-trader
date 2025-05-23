"""
Portfolio Management for Schwab Trader

This module provides a PortfolioManager class that builds on the existing
client, order management, and real-time data mixins to provide a unified
view of all account assets, orders, and execution history.
"""

from typing import Dict, List, Set, Optional, Union, Callable, Any
from decimal import Decimal
from datetime import datetime, timedelta
import asyncio
import json
import os
import time
from pathlib import Path
import logging
from threading import Lock

from .client import SchwabClient
from .async_client import AsyncSchwabClient
from .paper_trading.client import PaperTradingClient, AsyncPaperTradingClient
from .models.generated.trading_models import Account, Position, Order, Status as OrderStatus, OrderActivity, ExecutionLeg
from .models.execution import ExecutionReport

# Set up logging
logger = logging.getLogger(__name__)

# Debug mode flag - only for enhanced logging, not for mock data
DEBUG_MODE = True

class PortfolioManager:
    """
    Manages a portfolio of positions across one or more Schwab accounts.
    
    The PortfolioManager maintains an in-memory ledger of positions, orders,
    and executions, with real-time updates based on order status changes and
    execution reports.
    
    Key features:
    - Track positions across multiple accounts
    - Record order placements and executions
    - Calculate performance metrics
    - Support persistence of portfolio state
    - Integration with paper trading accounts
    """
    
    def __init__(
        self, 
        client: Union[SchwabClient, AsyncSchwabClient, PaperTradingClient, AsyncPaperTradingClient],
        persistence_path: Optional[str] = None
    ):
        """
        Initialize the portfolio manager.
        
        Args:
            client: Authenticated SchwabClient, AsyncSchwabClient, PaperTradingClient, 
                   or AsyncPaperTradingClient instance
            persistence_path: Optional path to save portfolio state
        """
        self.client = client
        self.persistence_path = persistence_path
        
        # Check if using paper trading client
        self._is_paper_trading_client = isinstance(client, (PaperTradingClient, AsyncPaperTradingClient))
        if self._is_paper_trading_client:
            logger.info("Portfolio manager initialized with paper trading client")
            if hasattr(client, 'enable_paper_trading'):
                # Make sure paper trading mode is enabled
                client.enable_paper_trading()
        
        # Lock for thread safety when updating portfolio state
        self._lock = Lock()
        
        # Portfolio state
        self._accounts: Dict[str, Account] = {}  # account_number -> Account
        self._positions: Dict[str, Dict[str, Position]] = {}  # account_number -> {symbol -> Position}
        self._orders: Dict[int, Order] = {}  # order_id -> Order
        self._executions: Dict[str, ExecutionReport] = {}  # execution_id -> ExecutionReport
        self._order_callbacks: Dict[int, List[Callable]] = {}  # order_id -> callbacks
        
        # Monitoring state
        self._monitoring = False
        self._monitored_orders: Set[int] = set()
        self._monitored_accounts: Set[str] = set()
        
        # Load persisted state if available
        if persistence_path:
            self._load_state()
    
    def add_account(self, account_number: str) -> None:
        """
        Add an account to the portfolio.
        
        Args:
            account_number: The encrypted account number
        """
        if account_number in self._accounts:
            logger.info(f"Account {account_number} already in portfolio")
            return
        
        # Get account details with positions
        account = self.client.get_account(account_number, include_positions=True)
        
        # Log account structure for debugging
        logger.info(f"Account data received for {account_number}")
        if hasattr(account, 'model_dump'):
            try:
                account_data = account.model_dump()
                if 'securities_account' in account_data and isinstance(account_data['securities_account'], dict):
                    sec_data = account_data['securities_account']
                    logger.info(f"Securities account type: {sec_data.get('type', 'Unknown')}")
                    if 'current_balances' in sec_data:
                        logger.info(f"Current balances: {sec_data['current_balances']}")
            except Exception as e:
                logger.error(f"Error dumping account data: {e}")
        
        with self._lock:
            # Store account data
            self._accounts[account_number] = account
            
            # Store position data
            self._positions[account_number] = {}
            
            # Extract positions from securities_account
            sec_acct = getattr(account, 'securities_account', None)
            if sec_acct is not None and hasattr(sec_acct, 'positions'):
                positions_list = getattr(sec_acct, 'positions', [])
                
                for position in positions_list:
                    symbol = self._extract_symbol_from_position(position)
                    if symbol:
                        self._positions[account_number][symbol] = position
                        logger.debug(f"Added position for {symbol}")
                    else:
                        logger.warning(f"Position without extractable symbol found in account {account_number}")
            
            # Add to monitored accounts
            self._monitored_accounts.add(account_number)
            
        logger.info(f"Added account {account_number} to portfolio with {len(self._positions[account_number])} positions")
    
    async def add_account_async(self, account_number: str) -> None:
        """
        Add an account to the portfolio asynchronously.
        
        Args:
            account_number: The encrypted account number
        """
        if account_number in self._accounts:
            logger.info(f"Account {account_number} already in portfolio")
            return
        
        # Get account details with positions
        account = await self.client.get_account(account_number, include_positions=True)
        
        with self._lock:
            # Store account data
            self._accounts[account_number] = account
            
            # Store position data
            self._positions[account_number] = {}
            
            # Extract positions from securities_account
            sec_acct = getattr(account, 'securities_account', None)
            if sec_acct is not None and hasattr(sec_acct, 'positions'):
                positions_list = getattr(sec_acct, 'positions', [])
                
                for position in positions_list:
                    symbol = self._extract_symbol_from_position(position)
                    if symbol:
                        self._positions[account_number][symbol] = position
                        logger.debug(f"Added position for {symbol}")
                    else:
                        logger.warning(f"Position without extractable symbol found in account {account_number}")
            
            # Add to monitored accounts
            self._monitored_accounts.add(account_number)
            
        logger.info(f"Added account {account_number} to portfolio with {len(self._positions[account_number])} positions")
    
    def refresh_positions(self) -> None:
        """Refresh all positions for all accounts in the portfolio."""
        for account_number in self._accounts:
            logger.info(f"Refreshing positions for account {account_number}")
            
            try:
                # Get fresh account data with positions
                account = self.client.get_account(account_number, include_positions=True)
                
                with self._lock:
                    # Update account data
                    self._accounts[account_number] = account
                    
                    # Initialize position data
                    self._positions[account_number] = {}
                    
                    # Extract positions from securities_account
                    sec_acct = getattr(account, 'securities_account', None)
                    if sec_acct is not None:
                        positions_list = getattr(sec_acct, 'positions', [])
                        
                        if positions_list:
                            logger.info(f"Found {len(positions_list)} positions in securities_account")
                            
                            for position in positions_list:
                                symbol = self._extract_symbol_from_position(position)
                                if symbol:
                                    self._positions[account_number][symbol] = position
                                    logger.debug(f"Stored position for {symbol}")
                            
                            logger.info(f"Successfully stored {len(self._positions[account_number])} positions for account {account_number}")
                            continue
                    
                    # If no positions found through the primary method, log warning
                    logger.warning(f"No positions found for account {account_number}")
            
            except Exception as e:
                logger.exception(f"Error refreshing positions for account {account_number}: {str(e)}")
        
        logger.info(f"Completed position refresh for {len(self._accounts)} accounts")
    
    def _debug_account_structure(self, account, account_number: str) -> None:
        """Debug method to log account structure when positions aren't found."""
        try:
            logger.debug(f"Account type: {type(account).__name__}")
            
            if hasattr(account, 'model_dump'):
                try:
                    data = account.model_dump()
                    logger.debug(f"Account keys: {list(data.keys())}")
                    if 'securities_account' in data:
                        sec_data = data['securities_account']
                        if isinstance(sec_data, dict):
                            logger.debug(f"Securities account keys: {list(sec_data.keys())}")
                except Exception as e:
                    logger.debug(f"Could not dump account model: {e}")
            
            if hasattr(account, 'securities_account') and account.securities_account:
                sec_acct = account.securities_account
                logger.debug(f"Securities account type: {type(sec_acct).__name__}")
                logger.debug(f"Securities account attributes: {[attr for attr in dir(sec_acct) if not attr.startswith('_')]}")
        except Exception as e:
            logger.debug(f"Error in debug account structure: {e}")
    
    
    def _extract_symbol_from_position(self, position) -> str:
        """Extract symbol from a position object."""
        symbol = None
        
        try:
            # First try through instrument.symbol (most common case)
            if hasattr(position, 'instrument'):
                if hasattr(position.instrument, 'symbol'):
                    symbol = position.instrument.symbol
                
                # Check for symbol in root (for options)
                elif hasattr(position.instrument, 'root') and hasattr(position.instrument.root, 'symbol'):
                    symbol = position.instrument.root.symbol
                
                # If it's a RootModel, try to access .root directly
                elif hasattr(position.instrument, 'root') and hasattr(position.instrument.root, 'symbol'):
                    symbol = position.instrument.root.symbol
                
                # Last resort - if we have description but no symbol (sometimes happens)
                elif hasattr(position.instrument, 'description') and position.instrument.description:
                    # Use first word of description as a fallback "symbol"
                    desc = position.instrument.description
                    symbol = desc.split()[0]  # First word as symbol
                
                # Try CUSIP if available as last fallback
                elif hasattr(position.instrument, 'cusip') and position.instrument.cusip:
                    symbol = f"CUSIP:{position.instrument.cusip}"
        except Exception as e:
            logger.error(f"Error extracting symbol from position object: {str(e)}")
        
        return symbol
    
    def _log_position_details(self, position) -> None:
        """Log details of a position object to help with debugging."""
        try:
            # Get position attributes excluding private and callable ones
            position_attrs = [attr for attr in dir(position) 
                             if not attr.startswith('_') and not callable(getattr(position, attr))]
            logger.info(f"Position model attributes: {', '.join(position_attrs)}")
            
            # Log key position properties that we care about
            for key_attr in ['market_value', 'long_quantity', 'short_quantity', 'average_price']:
                if hasattr(position, key_attr):
                    logger.info(f"Position {key_attr}: {getattr(position, key_attr)}")
            
            # Log instrument details
            if hasattr(position, 'instrument'):
                instrument = position.instrument
                instrument_type = type(instrument).__name__
                logger.info(f"Position instrument type: {instrument_type}")
                
                # If instrument is a RootModel, also log its .root type
                if hasattr(instrument, 'root'):
                    root_type = type(instrument.root).__name__
                    logger.info(f"Position instrument root type: {root_type}")
                    
                    # Log some important attributes if available
                    if hasattr(instrument.root, 'asset_type'):
                        logger.info(f"Position asset type: {instrument.root.asset_type}")
        except Exception as e:
            logger.error(f"Error logging position details: {str(e)}")
    
    async def refresh_positions_async(self) -> None:
        """Refresh all positions for all accounts asynchronously."""
        for account_number in self._accounts:
            logger.info(f"Async refreshing positions for account {account_number}")
            
            try:
                # Get fresh account data with positions
                account = await self.client.get_account(account_number, include_positions=True)
                
                with self._lock:
                    # Update account data
                    self._accounts[account_number] = account
                    
                    # Initialize position data
                    self._positions[account_number] = {}
                    
                    # Log account model type for debugging
                    account_model_name = type(account).__name__
                    logger.info(f"Account model type: {account_model_name}")
                    
                    # Check for positions directly on the account (Pydantic model variant 1)
                    positions_count = 0
                    if hasattr(account, 'positions') and account.positions:
                        positions_count = len(account.positions)
                        logger.info(f"Found {positions_count} positions directly on the account")
                        for position in account.positions:
                            if hasattr(position, 'instrument') and hasattr(position.instrument, 'symbol'):
                                symbol = position.instrument.symbol
                                self._positions[account_number][symbol] = position
                                logger.info(f"Refreshed position for {symbol} from account.positions")
                            else:
                                logger.warning(f"Position without instrument or symbol found in account {account_number}")
                    
                    # Check for positions in securities_account (Pydantic model variant 2)
                    elif (hasattr(account, 'securities_account') and
                          account.securities_account and
                          hasattr(account.securities_account, 'positions') and
                          account.securities_account.positions):
                        
                        positions_count = len(account.securities_account.positions)
                        logger.info(f"Found {positions_count} positions in securities_account")
                        
                        for position in account.securities_account.positions:
                            # Extract symbol based on position model structure
                            symbol = None
                            
                            if hasattr(position, 'instrument'):
                                if hasattr(position.instrument, 'symbol'):
                                    symbol = position.instrument.symbol
                                elif hasattr(position.instrument, 'root') and hasattr(position.instrument.root, 'symbol'):
                                    symbol = position.instrument.root.symbol
                            
                            if symbol:
                                self._positions[account_number][symbol] = position
                                logger.info(f"Refreshed position for {symbol} from securities_account.positions")
                            else:
                                logger.warning(f"Could not determine symbol for position in account {account_number}")
                    
                    if positions_count == 0:
                        logger.warning(f"No positions found in account {account_number}")
                    
                    # Log the position structure for more debugging insights
                    if self._positions[account_number]:
                        # Take the first position as an example to log its structure
                        first_symbol = next(iter(self._positions[account_number]))
                        position_example = self._positions[account_number][first_symbol]
                        position_attrs = [attr for attr in dir(position_example) 
                                         if not attr.startswith('_') and not callable(getattr(position_example, attr))]
                        logger.info(f"Position model attributes: {', '.join(position_attrs)}")
                        
                        # Log basic position information
                        if hasattr(position_example, 'market_value'):
                            logger.info(f"Example position market value: {position_example.market_value}")
                        if hasattr(position_example, 'long_quantity'):
                            logger.info(f"Example position long quantity: {position_example.long_quantity}")
            
            except Exception as e:
                logger.exception(f"Error refreshing positions for account {account_number}: {str(e)}")
        
        logger.info(f"Completed async position refresh for {len(self._accounts)} accounts")
    
    def place_order(self, account_number: str, order: Order) -> int:
        """
        Place an order and track it in the portfolio.
        
        Args:
            account_number: The encrypted account number
            order: The order to place
            
        Returns:
            The order ID
        """
        # Ensure account is in the portfolio
        if account_number not in self._accounts:
            raise ValueError(f"Account {account_number} not in portfolio")
            
        # If using paper trading client, ensure we're in paper trading mode
        if self._is_paper_trading_client and hasattr(self.client, 'is_paper_trading_enabled'):
            if not self.client.is_paper_trading_enabled:
                # Enable paper trading mode
                self.client.enable_paper_trading()
                logger.info("Enabled paper trading mode for order placement")
            
            # If using paper trading client, ensure account is a paper trading account
            if hasattr(self.client, 'is_paper_account'):
                is_paper = self.client.is_paper_account(account_number)
                if not is_paper:
                    logger.warning(f"Account {account_number} is not a paper trading account")
                    raise ValueError(f"Cannot use non-paper account {account_number} with paper trading client")
        
        # Place the order
        self.client.place_order(account_number, order)
        
        # Get the order details with ID
        from_date = datetime.now() - timedelta(minutes=5)
        to_date = datetime.now()
        recent_orders = self.client.get_orders(
            account_number,
            from_entered_time=from_date,
            to_entered_time=to_date
        )
        
        # Find the order we just placed (should be the most recent one)
        placed_order = None
        for order_item in recent_orders.orders:
            if (order_item.order_type == order.order_type and
                order_item.quantity == order.quantity):
                placed_order = order_item
                break
        
        if not placed_order:
            logger.warning("Could not find placed order in recent orders")
            return 0
            
        order_id = placed_order.order_id
        
        with self._lock:
            # Store the order
            self._orders[order_id] = placed_order
            # Add to monitoring
            self._monitored_orders.add(order_id)
            
        # Start monitoring if not already
        if not self._monitoring:
            self._start_monitoring()
            
        logger.info(f"Placed order {order_id} for {account_number}")
        return order_id
    
    async def place_order_async(self, account_number: str, order: Order) -> int:
        """
        Place an order and track it in the portfolio asynchronously.
        
        Args:
            account_number: The encrypted account number
            order: The order to place
            
        Returns:
            The order ID
        """
        # Ensure account is in the portfolio
        if account_number not in self._accounts:
            raise ValueError(f"Account {account_number} not in portfolio")
            
        # If using paper trading client, ensure we're in paper trading mode
        if self._is_paper_trading_client and hasattr(self.client, 'is_paper_trading_enabled'):
            if not self.client.is_paper_trading_enabled:
                # Enable paper trading mode
                self.client.enable_paper_trading()
                logger.info("Enabled paper trading mode for async order placement")
            
            # If using paper trading client, ensure account is a paper trading account
            if hasattr(self.client, 'is_paper_account'):
                is_paper = await self.client.is_paper_account(account_number)
                if not is_paper:
                    logger.warning(f"Account {account_number} is not a paper trading account")
                    raise ValueError(f"Cannot use non-paper account {account_number} with paper trading client")
        
        # Place the order
        await self.client.place_order(account_number, order)
        
        # Get the order details with ID
        from_date = datetime.now() - timedelta(minutes=5)
        to_date = datetime.now()
        recent_orders = await self.client.get_orders(
            account_number,
            from_entered_time=from_date,
            to_entered_time=to_date
        )
        
        # Find the order we just placed (should be the most recent one)
        placed_order = None
        for order_item in recent_orders.orders:
            if (order_item.order_type == order.order_type and
                order_item.quantity == order.quantity):
                placed_order = order_item
                break
        
        if not placed_order:
            logger.warning("Could not find placed order in recent orders")
            return 0
            
        order_id = placed_order.order_id
        
        with self._lock:
            # Store the order
            self._orders[order_id] = placed_order
            # Add to monitoring
            self._monitored_orders.add(order_id)
            
        # Start monitoring if not already
        if not self._monitoring:
            await self._start_monitoring_async()
            
        logger.info(f"Placed order {order_id} for {account_number}")
        return order_id
    
    def cancel_order(self, account_number: str, order_id: int) -> None:
        """
        Cancel an order and update its status in the portfolio.
        
        Args:
            account_number: The encrypted account number
            order_id: The order ID to cancel
        """
        # Ensure order is in the portfolio
        if order_id not in self._orders:
            raise ValueError(f"Order {order_id} not in portfolio")
        
        # Cancel the order
        self.client.cancel_order(account_number, order_id)
        
        # Update order status
        self._update_order(account_number, order_id)
        
        logger.info(f"Canceled order {order_id} for {account_number}")
    
    async def cancel_order_async(self, account_number: str, order_id: int) -> None:
        """
        Cancel an order and update its status in the portfolio asynchronously.
        
        Args:
            account_number: The encrypted account number
            order_id: The order ID to cancel
        """
        # Ensure order is in the portfolio
        if order_id not in self._orders:
            raise ValueError(f"Order {order_id} not in portfolio")
        
        # Cancel the order
        await self.client.cancel_order(account_number, order_id)
        
        # Update order status
        await self._update_order_async(account_number, order_id)
        
        logger.info(f"Canceled order {order_id} for {account_number}")
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get a consolidated snapshot of the portfolio.
        
        Returns:
            A dictionary containing portfolio summary information
        """
        total_equity = Decimal('0')
        total_cash = Decimal('0')
        positions_by_symbol = {}
        positions_by_asset_class = {
            'EQUITY': Decimal('0'),
            'OPTION': Decimal('0'),
            'MUTUAL_FUND': Decimal('0'),
            'FIXED_INCOME': Decimal('0'),
            'FOREX': Decimal('0'),
            'INDEX': Decimal('0')
        }
        
        # Refresh positions before summary if monitoring active (skip manual/test setups)
        if self._monitored_accounts:
            try:
                logger.info("Refreshing positions before generating portfolio summary")
                self.refresh_positions()
            except Exception as e:
                logger.exception(f"Error during pre-summary position refresh: {str(e)}")
        
        # Calculate totals
        for account_number, account in self._accounts.items():
            logger.info(f"Processing account {account_number} for portfolio summary")
            account_cash = Decimal('0')  # Track cash for this account
            
            # First, log the entire account structure for debugging
            try:
                # For Pydantic model accounts
                account_data = {}
                if hasattr(account, 'model_dump') and not str(type(account)).find('SimpleNamespace') >= 0:
                    try:
                        account_data = account.model_dump()
                        logger.info(f"Account data keys: {list(account_data.keys())}")
                    except Exception as model_err:
                        logger.warning(f"Error in model_dump() for account structure: {str(model_err)}")

                    # If securities_account exists, log its structure
                    if account_data and 'securities_account' in account_data:
                        sec_account = account_data['securities_account']
                        if isinstance(sec_account, dict):
                            logger.info(f"Securities account keys: {list(sec_account.keys())}")

                            # Log balances structure if it exists
                            if 'current_balances' in sec_account:
                                balances = sec_account['current_balances']
                                if isinstance(balances, dict):
                                    logger.info(f"Current balances keys: {list(balances.keys())}")
                                    logger.info(f"Current balances values: {balances}")
                # For SimpleNamespace accounts
                else:
                    logger.info("Account is a SimpleNamespace object")
                    if hasattr(account, 'securities_account'):
                        logger.info("Found securities_account in SimpleNamespace")
                        sec_account = account.securities_account
                        
                        if hasattr(sec_account, 'current_balances'):
                            logger.info("Found current_balances in securities_account")
                            current_balances = sec_account.current_balances
                            
                            # Log available attributes on current_balances if it's not None
                            if current_balances:
                                balance_attrs = [attr for attr in dir(current_balances) 
                                               if not attr.startswith('_') and not callable(getattr(current_balances, attr))]
                                logger.info(f"Current balances attributes: {balance_attrs}")
                                # Log values of buying_power if available
                                if hasattr(current_balances, 'buying_power'):
                                    logger.info(f"Buying power: {current_balances.buying_power}")
            except Exception as e:
                logger.warning(f"Error logging account structure: {str(e)}")
            
            # Extract cash balance using simplified approach
            account_cash = self._extract_account_cash_balance(account, account_number)
            
            # Add account cash to total
            total_cash += account_cash
            logger.info(f"Total cash balance after processing account {account_number}: {total_cash}")
            
            # Process the positions for this account
            account_equity = Decimal('0')  # Track equity for this account
            logger.info(f"Processing {len(self._positions.get(account_number, {}))} positions for account {account_number}")
            
            # Skip if no positions for this account
            if account_number not in self._positions or not self._positions[account_number]:
                logger.warning(f"No positions for account {account_number}")
                continue
            
            # Process positions for this account
            account_positions = self._positions.get(account_number, {})
            for symbol, position in account_positions.items():
                try:
                    logger.info(f"Processing position for symbol: {symbol}")
                    position_data = None
                    market_value = Decimal('0')
                    
                    # Try to dump position to dict for debugging
                    try:
                        if hasattr(position, 'model_dump'):
                            position_data = position.model_dump()
                            logger.info(f"Position data keys: {list(position_data.keys())}")
                            if 'market_value' in position_data:
                                logger.info(f"Raw market_value in position data: {position_data['market_value']}")
                    except Exception as dump_err:
                        logger.warning(f"Error dumping position data: {str(dump_err)}")
                    
                    # Extract market value, handling different position structures
                    try:
                        market_value = self._extract_decimal_field(position, 'market_value', Decimal('0'))
                        logger.info(f"Position {symbol} market value: {market_value}")
                    except Exception as mv_err:
                        logger.warning(f"Error extracting market value for {symbol}: {str(mv_err)}")
                    
                    # If market value is zero but we have a quantity, try calculating it from quantity * current price
                    if market_value <= 0:
                        long_qty = Decimal('0')
                        short_qty = Decimal('0')
                        
                        try:
                            long_qty = self._extract_decimal_field(position, 'long_quantity', Decimal('0'))
                            short_qty = self._extract_decimal_field(position, 'short_quantity', Decimal('0'))
                        except Exception as qty_err:
                            logger.warning(f"Error extracting quantity for {symbol}: {str(qty_err)}")
                            
                        net_qty = long_qty - short_qty
                        
                        if net_qty != 0:
                            # Try to get last price from instrument if available
                            last_price = Decimal('0')
                            try:
                                if hasattr(position, 'instrument') and hasattr(position.instrument, 'last_price'):
                                    last_price = Decimal(str(position.instrument.last_price))
                                elif position_data and 'instrument' in position_data:
                                    inst_data = position_data['instrument']
                                    if isinstance(inst_data, dict) and 'last_price' in inst_data:
                                        last_price = Decimal(str(inst_data['last_price']))
                            except Exception as price_err:
                                logger.warning(f"Error extracting last_price for {symbol}: {str(price_err)}")
                                
                            # If we found a last price, calculate market value
                            if last_price > 0:
                                market_value = net_qty * last_price
                                logger.info(f"Calculated market value for {symbol}: {market_value} (qty: {net_qty} * price: {last_price})")
                            
                            # If we still couldn't determine market value
                            elif market_value <= 0:
                                logger.warning(f"Could not determine market value for {symbol} with quantity {net_qty}")
                    
                    # Skip positions with missing or zero market value
                    if market_value <= 0:
                        logger.warning(f"Skipping position with zero or negative market value: {symbol}")
                        continue
                    
                    # Add to account equity total
                    account_equity += market_value
                    
                    # Aggregate positions by symbol
                    if symbol not in positions_by_symbol:
                        positions_by_symbol[symbol] = {
                            'quantity': Decimal('0'),
                            'market_value': Decimal('0'),
                            'cost_basis': Decimal('0'),
                            'gain_loss': Decimal('0'),
                            'gain_loss_pct': Decimal('0'),
                            'average_price': Decimal('0')
                        }
                    
                    # Extract position quantities
                    long_qty = self._extract_decimal_field(position, 'long_quantity', Decimal('0'))
                    short_qty = self._extract_decimal_field(position, 'short_quantity', Decimal('0'))
                    
                    net_qty = long_qty - short_qty
                    positions_by_symbol[symbol]['quantity'] += net_qty
                    positions_by_symbol[symbol]['market_value'] += market_value
                    
                    # Extract average price
                    avg_price = self._extract_decimal_field(position, 'average_price', Decimal('0'))
                    positions_by_symbol[symbol]['average_price'] = avg_price
                    
                    # Calculate cost basis
                    cost_basis = avg_price * long_qty
                    positions_by_symbol[symbol]['cost_basis'] += cost_basis
                    
                    # Calculate gain/loss
                    if cost_basis > 0:
                        gain_loss = market_value - cost_basis
                        gain_loss_pct = (gain_loss / cost_basis) * Decimal('100')
                        positions_by_symbol[symbol]['gain_loss'] = gain_loss
                        positions_by_symbol[symbol]['gain_loss_pct'] = gain_loss_pct
                    
                    # Determine asset class
                    asset_type_str = self._determine_asset_type(position)
                    
                    # Add to asset class totals
                    if asset_type_str not in positions_by_asset_class:
                        positions_by_asset_class[asset_type_str] = Decimal('0')
                    positions_by_asset_class[asset_type_str] += market_value
                    
                    logger.info(f"Processed position {symbol}: qty={net_qty}, market_value={market_value}, avg_price={avg_price}, asset_type={asset_type_str}")
                
                except Exception as e:
                    logger.exception(f"Error processing position {symbol}: {str(e)}")
            
            # Add account equity to total
            total_equity += account_equity
            logger.info(f"Total equity after processing account {account_number}: {total_equity} (account equity: {account_equity})")
        
        # Log portfolio summary information for debugging
        if DEBUG_MODE:
            # Log calculated values
            logger.info("Portfolio summary from extracted data:")
            logger.info(f"  - Total cash: {total_cash}")
            logger.info(f"  - Total equity: {total_equity}")
            logger.info(f"  - Position count: {len(positions_by_symbol)}")
            
            # Log warning if no equity found
            if total_equity == 0:
                logger.warning("No equity found in any account. Check position data extraction.")
                
            # Log warning if no cash found
            if total_cash == 0:
                logger.warning("No cash balance found in any account. Check cash balance extraction.")
        
        # Calculate account allocation percentages
        total_value = total_equity + total_cash
        logger.info(f"Final portfolio summary values: total_equity={total_equity}, total_cash={total_cash}, total_value={total_value}")
        
        # Calculate allocation percentages, rounded to 2 decimal places for better display
        quant = Decimal('0.01')  # 2 decimal places for display
        
        if total_value > 0:
            raw_cash_pct = total_cash / total_value * Decimal('100')
            raw_equity_pct = total_equity / total_value * Decimal('100')
            cash_allocation = raw_cash_pct.quantize(quant)
            equity_allocation = raw_equity_pct.quantize(quant)
        else:
            cash_allocation = Decimal('0')
            equity_allocation = Decimal('0')
        
        # Calculate asset class allocation percentages
        asset_allocation = {}
        for asset_class, value in positions_by_asset_class.items():
            if total_value > 0 and value > 0:
                raw_pct = value / total_value * Decimal('100')
                asset_allocation[asset_class] = raw_pct.quantize(quant)
        
        # Log the positions found in the summary
        if positions_by_symbol:
            logger.info(f"Found {len(positions_by_symbol)} positions in portfolio summary:")
            for symbol, data in positions_by_symbol.items():
                logger.info(f"  - {symbol}: quantity={data['quantity']}, market_value={data['market_value']}")
        else:
            logger.warning("No positions found for portfolio summary")
        
        return {
            'total_value': total_value,
            'total_equity': total_equity,
            'total_cash': total_cash,
            'cash_allocation': cash_allocation,
            'equity_allocation': equity_allocation,
            'positions_by_symbol': positions_by_symbol,
            'asset_allocation': asset_allocation,
            'accounts': list(self._accounts.keys()),
            'open_orders': len([o for o in self._orders.values() if o.status == OrderStatus.WORKING]),
            'filled_orders': len([o for o in self._orders.values() if o.status == OrderStatus.FILLED]),
            'total_orders': len(self._orders),
            'total_executions': len(self._executions)
        }
    
    def _extract_decimal_field(self, obj, field_name, default=Decimal('0')) -> Decimal:
        """Safely extract a Decimal field from an object."""
        try:
            if hasattr(obj, field_name):
                value = getattr(obj, field_name)
                if value is not None:
                    return Decimal(str(value))
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning(f"Error extracting {field_name}: {str(e)}")
        
        # Try extracting from model_dump if attribute access fails
        try:
            if hasattr(obj, 'model_dump'):
                data = obj.model_dump()
                if field_name in data and data[field_name] is not None:
                    return Decimal(str(data[field_name]))
        except Exception:
            pass
            
        return default
    
    def _determine_asset_type(self, position) -> str:
        """Determine the asset type of a position."""
        # Default to EQUITY if we can't determine asset type
        asset_type = 'EQUITY'
        
        try:
            # First try through regular attribute access
            if hasattr(position, 'instrument'):
                instrument = position.instrument
                
                # Direct asset type attribute
                if hasattr(instrument, 'asset_type'):
                    asset_type = str(instrument.asset_type)
                # Type instead of asset_type 
                elif hasattr(instrument, 'type'):
                    asset_type = str(instrument.type)
                # Asset type in root object
                elif hasattr(instrument, 'root'):
                    root = instrument.root
                    if hasattr(root, 'asset_type'):
                        asset_type = str(root.asset_type)
            
            # If still not found, try via model_dump
            if asset_type == 'EQUITY' and hasattr(position, 'model_dump'):
                data = position.model_dump()
                if 'instrument' in data and isinstance(data['instrument'], dict):
                    instrument = data['instrument']
                    
                    if 'asset_type' in instrument:
                        asset_type = str(instrument['asset_type'])
                    elif 'type' in instrument:
                        asset_type = str(instrument['type'])
                    elif 'root' in instrument and isinstance(instrument['root'], dict):
                        root = instrument['root']
                        if 'asset_type' in root:
                            asset_type = str(root['asset_type'])
            
            # Normalize asset type string
            asset_type = asset_type.upper()
            
            # Map common types to standard categories
            type_mapping = {
                'COMMON_STOCK': 'EQUITY',
                'PREFERRED_STOCK': 'EQUITY',
                'ETF': 'EQUITY',
                'BOND': 'FIXED_INCOME',
                'GOVERNMENT_BOND': 'FIXED_INCOME',
                'CORPORATE_BOND': 'FIXED_INCOME',
                'FUND': 'MUTUAL_FUND'
            }
            
            if asset_type in type_mapping:
                asset_type = type_mapping[asset_type]
                
        except Exception as e:
            logger.warning(f"Error determining asset type: {str(e)}")
        
        return asset_type
    
    def _extract_account_cash_balance(self, account, account_number: str) -> Decimal:
        """Extract cash balance from account using Pydantic models."""
        account_cash = Decimal('0')
        
        try:
            if hasattr(account, 'securities_account') and account.securities_account:
                sec_acct = account.securities_account
                
                # Check account type and use appropriate model fields
                if hasattr(sec_acct, 'type'):
                    account_type = sec_acct.type
                    
                    if account_type == 'MARGIN' and hasattr(sec_acct, 'current_balances') and sec_acct.current_balances:
                        # MarginBalance model
                        balances = sec_acct.current_balances
                        if hasattr(balances, 'available_funds') and balances.available_funds is not None:
                            account_cash = Decimal(str(balances.available_funds))
                            logger.info(f"Found margin account cash balance of {account_cash} for account {account_number}")
                    
                    elif account_type == 'CASH' and hasattr(sec_acct, 'current_balances') and sec_acct.current_balances:
                        # CashBalance model
                        balances = sec_acct.current_balances
                        if hasattr(balances, 'cash_available_for_trading') and balances.cash_available_for_trading is not None:
                            account_cash = Decimal(str(balances.cash_available_for_trading))
                            logger.info(f"Found cash account balance of {account_cash} for account {account_number}")
                        elif hasattr(balances, 'total_cash') and balances.total_cash is not None:
                            account_cash = Decimal(str(balances.total_cash))
                            logger.info(f"Found cash account total_cash of {account_cash} for account {account_number}")
                
                if account_cash == 0:
                    logger.debug(f"No positive cash balance found for account {account_number}")
                        
        except Exception as e:
            logger.warning(f"Error extracting cash balance for account {account_number}: {e}")
            
        return account_cash
    
    def get_position(self, symbol: str) -> Dict[str, Any]:
        """
        Get consolidated position information for a symbol across all accounts.
        
        Args:
            symbol: The symbol to look up
            
        Returns:
            Position information
        """
        total_quantity = Decimal('0')
        total_market_value = Decimal('0')
        total_cost_basis = Decimal('0')
        
        for account_number, positions in self._positions.items():
            if symbol in positions:
                position = positions[symbol]
                total_quantity += position.long_quantity - position.short_quantity
                total_market_value += position.market_value
                total_cost_basis += position.average_price * position.long_quantity
        
        average_price = (total_cost_basis / total_quantity) if total_quantity > 0 else Decimal('0')
        gain_loss = total_market_value - total_cost_basis
        # Calculate percentage gain/loss, rounded to 14 decimal places
        if total_cost_basis > 0:
            raw_pct = gain_loss / total_cost_basis * Decimal('100')
            quant = Decimal('0.00000000000001')  # 14 decimal places
            gain_loss_pct = raw_pct.quantize(quant)
        else:
            gain_loss_pct = Decimal('0')
        
        return {
            'symbol': symbol,
            'quantity': total_quantity,
            'market_value': total_market_value,
            'cost_basis': total_cost_basis,
            'average_price': average_price,
            'gain_loss': gain_loss,
            'gain_loss_pct': gain_loss_pct
        }
    
    def get_order_history(
        self, 
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        status: Optional[OrderStatus] = None
    ) -> List[Order]:
        """
        Get filtered order history.
        
        Args:
            from_date: Optional start date filter
            to_date: Optional end date filter
            status: Optional status filter
            
        Returns:
            List of orders matching the criteria
        """
        orders = list(self._orders.values())
        
        # Apply filters
        if from_date:
            orders = [o for o in orders if o.entered_time and o.entered_time >= from_date]
        if to_date:
            orders = [o for o in orders if o.entered_time and o.entered_time <= to_date]
        if status:
            orders = [o for o in orders if o.status == status]
            
        # Sort by entered time descending
        orders.sort(key=lambda o: o.entered_time if o.entered_time else datetime.min, reverse=True)
        
        return orders
    
    def get_execution_history(self, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> List[ExecutionReport]:
        """
        Get filtered execution history.
        
        Args:
            from_date: Optional start date filter
            to_date: Optional end date filter
            
        Returns:
            List of executions matching the criteria
        """
        executions = list(self._executions.values())
        
        # Apply filters
        if from_date:
            executions = [e for e in executions if e.timestamp >= from_date]
        if to_date:
            executions = [e for e in executions if e.timestamp <= to_date]
            
        # Sort by timestamp descending
        executions.sort(key=lambda e: e.timestamp, reverse=True)
        
        return executions
    
    def monitor_orders(
        self, 
        callback: Callable[[Order, OrderStatus], None]
    ) -> None:
        """
        Register a callback for order status changes.
        
        Args:
            callback: Function to call when order status changes
        """
        # Add callback for all current orders
        for order_id in self._orders:
            if order_id not in self._order_callbacks:
                self._order_callbacks[order_id] = []
            self._order_callbacks[order_id].append(callback)
        
        # Start monitoring if not already
        if not self._monitoring:
            self._start_monitoring()
    
    def _update_order(self, account_number: str, order_id: int) -> None:
        """Update order information."""
        try:
            order = self.client.get_order(account_number, order_id)
            
            with self._lock:
                prev_status = self._orders[order_id].status if order_id in self._orders else None
                self._orders[order_id] = order
                
                # Check for status change
                if prev_status and order.status != prev_status:
                    self._handle_status_change(order, prev_status)
                    
                # Check for executions
                if order.order_activity_collection:
                    for activity in order.order_activity_collection:
                        if activity.activity_type == "EXECUTION":
                            self._handle_execution(order, activity)
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {str(e)}")
    
    async def _update_order_async(self, account_number: str, order_id: int) -> None:
        """Update order information asynchronously."""
        try:
            order = await self.client.get_order(account_number, order_id)
            
            with self._lock:
                prev_status = self._orders[order_id].status if order_id in self._orders else None
                self._orders[order_id] = order
                
                # Check for status change
                if prev_status and order.status != prev_status:
                    self._handle_status_change(order, prev_status)
                    
                # Check for executions
                if order.order_activity_collection:
                    for activity in order.order_activity_collection:
                        if activity.activity_type == "EXECUTION":
                            self._handle_execution(order, activity)
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {str(e)}")
    
    def _handle_status_change(self, order: Order, prev_status: OrderStatus) -> None:
        """Handle order status change."""
        logger.info(f"Order {order.order_id} status changed: {prev_status} -> {order.status}")
        
        # Notify callbacks
        if order.order_id in self._order_callbacks:
            for callback in self._order_callbacks[order.order_id]:
                try:
                    callback(order, order.status)
                except Exception as e:
                    logger.error(f"Error in order status callback: {str(e)}")
    
    def _handle_execution(self, order: Order, activity: Any) -> None:
        """Handle order execution."""
        # Create execution report
        for leg in activity.execution_legs:
            execution = ExecutionReport.from_activity(
                order_id=order.order_id,
                activity=activity,
                leg=leg
            )
            
            # Store execution
            self._executions[execution.execution_id] = execution
            
            logger.info(f"Execution received: {execution.execution_id} for order {order.order_id}")
    
    def _start_monitoring(self) -> None:
        """Start monitoring orders and positions."""
        import threading
        
        self._monitoring = True
        
        def monitor_loop():
            while self._monitoring:
                try:
                    # Update all monitored orders
                    for account_number in self._monitored_accounts:
                        for order_id in list(self._monitored_orders):
                            self._update_order(account_number, order_id)
                    
                    # Refresh positions periodically (every 60 seconds)
                    if int(time.time()) % 60 == 0:
                        self.refresh_positions()
                        
                    # Persist state if configured
                    if self.persistence_path:
                        self._save_state()
                        
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {str(e)}")
                
                # Sleep to prevent hammering the API
                time.sleep(1)
        
        # Start monitoring thread
        threading.Thread(target=monitor_loop, daemon=True).start()
        logger.info("Started order and position monitoring")
        
    
    async def _start_monitoring_async(self) -> None:
        """Start monitoring orders and positions asynchronously."""
        self._monitoring = True
        
        async def monitor_loop():
            while self._monitoring:
                try:
                    # Update all monitored orders
                    for account_number in self._monitored_accounts:
                        for order_id in list(self._monitored_orders):
                            await self._update_order_async(account_number, order_id)
                    
                    # Refresh positions periodically (every 60 seconds)
                    if int(time.time()) % 60 == 0:
                        await self.refresh_positions_async()
                        
                    # Persist state if configured
                    if self.persistence_path:
                        self._save_state()
                        
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {str(e)}")
                
                # Sleep to prevent hammering the API
                await asyncio.sleep(1)
        
        # Start monitoring task
        asyncio.create_task(monitor_loop())
        logger.info("Started order and position monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring orders and positions."""
        self._monitoring = False
        logger.info("Stopped order and position monitoring")
    
    def _save_state(self) -> None:
        """Save portfolio state to disk."""
        if not self.persistence_path:
            return
            
        try:
            # Prepare data for serialization
            state = {
                'timestamp': datetime.now().isoformat(),
                'accounts': {k: v.model_dump() for k, v in self._accounts.items()},
                'orders': {str(k): v.model_dump() for k, v in self._orders.items()},
                'executions': {k: v.model_dump() for k, v in self._executions.items()}
            }
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
            
            # Write to file
            with open(self.persistence_path, 'w') as f:
                json.dump(state, f)
                
            logger.debug(f"Saved portfolio state to {self.persistence_path}")
        except Exception as e:
            logger.error(f"Error saving portfolio state: {str(e)}")
    
    def _load_state(self) -> None:
        """Load portfolio state from disk."""
        if not self.persistence_path or not os.path.exists(self.persistence_path):
            return
            
        try:
            with open(self.persistence_path, 'r') as f:
                state = json.load(f)
                
            # Deserialize accounts
            if 'accounts' in state:
                for account_number, account_data in state['accounts'].items():
                    try:
                        self._accounts[account_number] = Account.model_validate(account_data)
                        # Initialize positions dict
                        self._positions[account_number] = {}
                        # Extract positions from account
                        if (self._accounts[account_number].securities_account and 
                            self._accounts[account_number].securities_account.positions):
                            for position in self._accounts[account_number].securities_account.positions:
                                symbol = position.instrument.symbol
                                self._positions[account_number][symbol] = position
                        # Add to monitored accounts
                        self._monitored_accounts.add(account_number)
                    except Exception as e:
                        logger.error(f"Error deserializing account {account_number}: {str(e)}")
            
            # Deserialize orders
            if 'orders' in state:
                for order_id_str, order_data in state['orders'].items():
                    try:
                        order_id = int(order_id_str)
                        self._orders[order_id] = Order.model_validate(order_data)
                        # Add to monitored orders if still active
                        if self._orders[order_id].status == OrderStatus.WORKING:
                            self._monitored_orders.add(order_id)
                    except Exception as e:
                        logger.error(f"Error deserializing order {order_id_str}: {str(e)}")
            
            # Deserialize executions
            if 'executions' in state:
                for execution_id, execution_data in state['executions'].items():
                    try:
                        self._executions[execution_id] = ExecutionReport.model_validate(execution_data)
                    except Exception as e:
                        logger.error(f"Error deserializing execution {execution_id}: {str(e)}")
            
            logger.info(f"Loaded portfolio state from {self.persistence_path}: " +
                       f"{len(self._accounts)} accounts, {len(self._orders)} orders, " +
                       f"{len(self._executions)} executions")
                       
            # Start monitoring if there are active orders
            if self._monitored_orders and not self._monitoring:
                self._start_monitoring()
                
        except Exception as e:
            logger.error(f"Error loading portfolio state: {str(e)}")
    
    @property
    def accounts(self) -> Dict[str, Account]:
        """Get all accounts in the portfolio."""
        return self._accounts
    
    def update(self) -> None:
        """Update all account and position data."""
        with self._lock:
            for account_number in list(self._accounts.keys()):
                try:
                    # Get fresh account data with positions
                    account = self.client.get_account(account_number, include_positions=True)
                    self._accounts[account_number] = account
                    
                    # Update positions
                    self._positions[account_number] = {}
                    sec_acct = getattr(account, 'securities_account', None)
                    if sec_acct is not None and hasattr(sec_acct, 'positions'):
                        positions_list = getattr(sec_acct, 'positions', [])
                        for position in positions_list:
                            symbol = self._extract_symbol_from_position(position)
                            if symbol:
                                self._positions[account_number][symbol] = position
                except Exception as e:
                    logger.error(f"Error updating account {account_number}: {str(e)}")
    
    def get_total_value(self) -> Decimal:
        """Get total portfolio value across all accounts."""
        total = Decimal('0')
        for account_number, account in self._accounts.items():
            try:
                if hasattr(account, 'securities_account') and account.securities_account:
                    sec_acct = account.securities_account
                    
                    # Check if it's a MarginAccount or CashAccount (proper Pydantic models)
                    if hasattr(sec_acct, 'initial_balances') and sec_acct.initial_balances:
                        # Use initial_balances.account_value which exists in both account types
                        if hasattr(sec_acct.initial_balances, 'account_value') and sec_acct.initial_balances.account_value is not None:
                            value = Decimal(str(sec_acct.initial_balances.account_value))
                            logger.info(f"Account {account_number}: found account value {value} in initial_balances")
                            total += value
                        else:
                            logger.warning(f"Account {account_number}: no account_value in initial_balances")
                    else:
                        logger.warning(f"Account {account_number}: no initial_balances found")
                else:
                    logger.warning(f"Account {account_number}: no securities_account found")
            except Exception as e:
                logger.error(f"Error getting value for account {account_number}: {str(e)}")
        
        logger.info(f"Total portfolio value: {total}")
        return total
    
    def get_total_cash(self) -> Decimal:
        """Get total cash balance across all accounts."""
        total = Decimal('0')
        for account_number, account in self._accounts.items():
            try:
                cash = self._extract_account_cash_balance(account, account_number)
                total += cash
            except Exception as e:
                logger.error(f"Error getting cash for account {account_number}: {str(e)}")
        return total
    
    def get_total_unrealized_gain_loss(self) -> Decimal:
        """Get total unrealized gain/loss across all positions."""
        total = Decimal('0')
        for account_positions in self._positions.values():
            for position in account_positions.values():
                try:
                    gain_loss = self._extract_decimal_field(position, 'long_open_profit_loss', Decimal('0'))
                    total += gain_loss
                except Exception as e:
                    logger.error(f"Error calculating gain/loss: {str(e)}")
        return total
    
    def get_total_unrealized_gain_loss_percent(self) -> Decimal:
        """Get total unrealized gain/loss percentage."""
        total_cost = Decimal('0')
        total_gain_loss = Decimal('0')
        
        for account_positions in self._positions.values():
            for position in account_positions.values():
                try:
                    # Get cost basis
                    long_qty = self._extract_decimal_field(position, 'long_quantity', Decimal('0'))
                    avg_price = self._extract_decimal_field(position, 'average_long_price', Decimal('0'))
                    cost = long_qty * avg_price
                    total_cost += cost
                    
                    # Get gain/loss
                    gain_loss = self._extract_decimal_field(position, 'long_open_profit_loss', Decimal('0'))
                    total_gain_loss += gain_loss
                except Exception as e:
                    logger.error(f"Error calculating gain/loss percentage: {str(e)}")
        
        if total_cost > 0:
            return (total_gain_loss / total_cost) * 100
        return Decimal('0')
    
    def _update_position_quote(self, symbol: str, quote: Any) -> None:
        """Update position with latest quote data."""
        # This is called by the GUI when streaming quotes come in
        # For now, we'll just log it
        logger.debug(f"Quote update for {symbol}: {quote}")
            
