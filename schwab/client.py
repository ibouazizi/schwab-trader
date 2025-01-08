from typing import List, Optional, Dict, Any, Union, Callable
from datetime import datetime
import requests
from urllib.parse import urljoin
from decimal import Decimal
from .auth import SchwabAuth

from .models.base import AccountNumber, AccountNumbers, ErrorResponse
from .models.account import Account
from .models.orders import (
    Order, OrderList, OrderType, OrderInstruction, OrderSession,
    OrderDuration, RequestedDestination, TaxLotMethod, SpecialInstruction,
    ComplexOrderStrategyType, OrderStrategyType, OrderLeg, OrderLegType,
    PositionEffect, QuantityType, DividendCapitalGains, StopPriceLinkBasis,
    StopPriceLinkType, StopType
)
from .order_management import OrderManagement
from .order_monitor import OrderMonitor
from .models.execution import ExecutionReport
from .models.quotes import QuoteResponse
from .api.quotes import QuotesMixin

class SchwabClient(QuotesMixin):
    """Client for interacting with the Schwab Trading API."""
    
    TRADING_BASE_URL = "https://api.schwabapi.com/trader/v1"
    MARKET_DATA_BASE_URL = "https://api.schwabapi.com/marketdata/v1"
    
    def __init__(
        self,        
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        auth: Optional['SchwabAuth'] = None
    ):
        """Initialize the client with OAuth credentials.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth callback URL
            auth: Optional pre-configured SchwabAuth instance
        """
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        
        # Initialize authentication
        self.auth = auth or SchwabAuth(client_id, client_secret, redirect_uri)
        
        # Initialize order management and monitoring
        self.order_management = OrderManagement(self)
        self.order_monitor = OrderMonitor(self)
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make a request to the API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Optional query parameters
            json: Optional JSON body
            data: Optional form data
            
        Returns:
            API response as dictionary
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        # Ensure we have a valid token
        self.auth.ensure_valid_token()
        
        # Update authorization header
        self.session.headers.update(self.auth.authorization_header)
        
        # Choose base URL based on endpoint
        if endpoint.startswith("/marketdata/"):
            base_url = "https://api.schwabapi.com"
        elif endpoint.startswith("/trader/"):
            base_url = "https://api.schwabapi.com"
        else:
            # Default to trading base URL for backward compatibility
            base_url = "https://api.schwabapi.com"
            endpoint = f"/trader/v1{endpoint}"
            
        url = urljoin(base_url, endpoint)
        response = self.session.request(
            method,
            url,
            params=params,
            json=json,
            data=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_account_numbers(self) -> AccountNumbers:
        """Get list of account numbers and their encrypted values."""
        data = self._make_request("GET", "/accounts/numbers")
        return AccountNumbers(accounts=[AccountNumber(**account) for account in data])
    
    def get_accounts(self, include_positions: bool = False) -> List[Account]:
        """Get all linked accounts with balances and optionally positions.
        
        Args:
            include_positions: Whether to include position information
            
        Returns:
            List of account information
        """
        params = {"fields": "positions"} if include_positions else None
        data = self._make_request(
            "GET",
            "/accounts/positions" if include_positions else "/accounts",
            params=params
        )
        return [Account(**account) for account in data]
    
    def get_account(self, account_number: str, include_positions: bool = False) -> Account:
        """Get specific account information.
        
        Args:
            account_number: The encrypted account number
            include_positions: Whether to include position information
            
        Returns:
            Account information
        """
        params = {"fields": "positions"} if include_positions else None
        endpoint = (
            f"/accounts/{account_number}/positions"
            if include_positions
            else f"/accounts/{account_number}"
        )
        data = self._make_request("GET", endpoint, params=params)
        return Account(**data)
    
    def get_orders(
        self,
        account_number: str,
        from_entered_time: datetime,
        to_entered_time: datetime,
        max_results: Optional[int] = None,
        status: Optional[str] = None
    ) -> OrderList:
        """Get orders for a specific account.
        
        Args:
            account_number: The encrypted account number
            from_entered_time: Start time for order history
            to_entered_time: End time for order history
            max_results: Maximum number of orders to return
            status: Filter orders by status
            
        Returns:
            List of orders
        """
        params = {
            "fromDate": from_entered_time.strftime("%Y-%m-%d"),
            "toDate": to_entered_time.strftime("%Y-%m-%d"),
        }
        if max_results is not None:
            params["maxResults"] = max_results
        if status is not None:
            params["status"] = status
            
        data = self._make_request("GET", f"/accounts/{account_number}/orders/history", params=params)
        return OrderList(**data)
        
    def place_order(self, account_number: str, order: Order) -> None:
        """Place an order for a specific account.
        
        Args:
            account_number: The encrypted account number
            order: The order to place
            
        Returns:
            None if successful
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        self._make_request("POST", f"/accounts/{account_number}/orders/place", json=order.model_dump(by_alias=True))
        
    def replace_order(self, account_number: str, order_id: int, new_order: Order) -> None:
        """Replace an existing order with a new order.
        
        The existing order will be canceled and a new order will be created.
        
        Args:
            account_number: The encrypted account number
            order_id: The ID of the order to replace
            new_order: The new order to place
            
        Returns:
            None if successful
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        self._make_request(
            "PUT",
            f"/accounts/{account_number}/orders/{order_id}/replace",
            json=new_order.model_dump(by_alias=True)
        )
        
    def cancel_order(self, account_number: str, order_id: int) -> None:
        """Cancel a specific order.
        
        Args:
            account_number: The encrypted account number
            order_id: The ID of the order to cancel
            
        Returns:
            None if successful
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        self._make_request("DELETE", f"/accounts/{account_number}/orders/{order_id}/cancel")
        
    def get_order(self, account_number: str, order_id: int) -> Order:
        """Get a specific order by its ID.
        
        Args:
            account_number: The encrypted account number
            order_id: The ID of the order to retrieve
            
        Returns:
            The order details
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        data = self._make_request("GET", f"/accounts/{account_number}/orders/{order_id}/details")
        return Order(**data)

    # Order Management Methods
    def modify_order_price(self, account_number: str, order_id: int, new_price: float) -> Order:
        """Modify the price of an existing order.
        
        Args:
            account_number: The encrypted account number
            order_id: The ID of the order to modify
            new_price: The new price for the order
            
        Returns:
            Modified order object
            
        Raises:
            OrderValidationError: If the order cannot be modified
        """
        return self.order_management.modify_price(account_number, order_id, new_price)

    def modify_order_quantity(self, account_number: str, order_id: int, new_quantity: int) -> Order:
        """Modify the quantity of an existing order.
        
        Args:
            account_number: The encrypted account number
            order_id: The ID of the order to modify
            new_quantity: The new quantity for the order
            
        Returns:
            Modified order object
            
        Raises:
            OrderValidationError: If the order cannot be modified
        """
        return self.order_management.modify_quantity(account_number, order_id, new_quantity)

    def batch_cancel_orders(self, account_number: str, order_ids: List[int]) -> Dict[int, bool]:
        """Cancel multiple orders in batch.
        
        Args:
            account_number: The encrypted account number
            order_ids: List of order IDs to cancel
            
        Returns:
            Dictionary mapping order IDs to cancellation success status
        """
        return self.order_management.batch_cancel_orders(account_number, order_ids)

    def batch_modify_orders(
        self,
        account_number: str,
        modifications: List[Dict]
    ) -> Dict[int, Union[Order, Exception]]:
        """Modify multiple orders in batch.
        
        Args:
            account_number: The encrypted account number
            modifications: List of dictionaries containing order_id and modifications
                Each dict should have 'order_id' and optionally 'price' and/or 'quantity'
            
        Returns:
            Dictionary mapping order IDs to modified Order objects or Exceptions
        """
        return self.order_management.batch_modify_orders(account_number, modifications)

    # Order Monitoring Methods
    def monitor_orders(
        self,
        account_number: str,
        order_ids: List[int],
        status_callback: Optional[Callable[[Order, str], None]] = None,
        execution_callback: Optional[Callable[[ExecutionReport], None]] = None,
        interval: float = 1.0
    ) -> None:
        """Start monitoring orders for status changes and executions.
        
        Args:
            account_number: The encrypted account number
            order_ids: List of order IDs to monitor
            status_callback: Optional callback for status changes
            execution_callback: Optional callback for execution reports
            interval: Polling interval in seconds (default: 1.0)
        """
        for order_id in order_ids:
            if status_callback:
                self.order_monitor.add_status_callback(order_id, status_callback)
            if execution_callback:
                self.order_monitor.add_execution_callback(order_id, execution_callback)
        
        return self.order_monitor.start_monitoring(account_number, order_ids, interval)

    def stop_monitoring(self) -> None:
        """Stop monitoring all orders."""
        self.order_monitor.stop_monitoring()
        
    def create_market_order(
        self,
        symbol: str,
        quantity: Union[int, Decimal],
        instruction: OrderInstruction,
        description: Optional[str] = None,
        instrument_id: Optional[int] = None,
        session: OrderSession = OrderSession.NORMAL,
        duration: OrderDuration = OrderDuration.DAY,
        requested_destination: Optional[RequestedDestination] = None,
        tax_lot_method: Optional[TaxLotMethod] = None,
        special_instruction: Optional[SpecialInstruction] = None
    ) -> Order:
        """Create a market order.
        
        Args:
            symbol: The symbol to trade
            quantity: The quantity to trade
            instruction: BUY or SELL
            description: Optional description of the instrument
            instrument_id: Optional instrument ID
            session: Order session (default: NORMAL)
            duration: Order duration (default: DAY)
            requested_destination: Optional trading destination
            tax_lot_method: Optional tax lot method
            special_instruction: Optional special instruction
            
        Returns:
            Order object ready to be placed
        """
        quantity = Decimal(str(quantity))
        return Order(
            session=session,
            duration=duration,
            order_type=OrderType.MARKET,
            complex_order_strategy_type=ComplexOrderStrategyType.NONE,
            quantity=quantity,
            filled_quantity=Decimal("0"),
            remaining_quantity=quantity,
            requested_destination=requested_destination,
            tax_lot_method=tax_lot_method,
            special_instruction=special_instruction,
            order_strategy_type=OrderStrategyType.SINGLE,
            order_leg_collection=[
                OrderLeg(
                    order_leg_type=OrderLegType.EQUITY,
                    leg_id=1,
                    instrument={
                        "symbol": symbol,
                        "description": description or symbol,
                        "instrument_id": instrument_id or 0,
                        "net_change": Decimal("0"),
                        "type": "EQUITY"
                    },
                    instruction=instruction,
                    position_effect=PositionEffect.OPENING,
                    quantity=quantity,
                    quantity_type=QuantityType.ALL_SHARES,
                    div_cap_gains=DividendCapitalGains.REINVEST
                )
            ]
        )
        
    def create_limit_order(
        self,
        symbol: str,
        quantity: Union[int, Decimal],
        limit_price: Union[float, Decimal],
        instruction: OrderInstruction,
        description: Optional[str] = None,
        instrument_id: Optional[int] = None,
        session: OrderSession = OrderSession.NORMAL,
        duration: OrderDuration = OrderDuration.DAY,
        requested_destination: Optional[RequestedDestination] = None,
        tax_lot_method: Optional[TaxLotMethod] = None,
        special_instruction: Optional[SpecialInstruction] = None
    ) -> Order:
        """Create a limit order.
        
        Args:
            symbol: The symbol to trade
            quantity: The quantity to trade
            limit_price: The limit price
            instruction: BUY or SELL
            description: Optional description of the instrument
            instrument_id: Optional instrument ID
            session: Order session (default: NORMAL)
            duration: Order duration (default: DAY)
            requested_destination: Optional trading destination
            tax_lot_method: Optional tax lot method
            special_instruction: Optional special instruction
            
        Returns:
            Order object ready to be placed
        """
        quantity = Decimal(str(quantity))
        limit_price = Decimal(str(limit_price))
        return Order(
            session=session,
            duration=duration,
            order_type=OrderType.LIMIT,
            complex_order_strategy_type=ComplexOrderStrategyType.NONE,
            quantity=quantity,
            filled_quantity=Decimal("0"),
            remaining_quantity=quantity,
            requested_destination=requested_destination,
            price=limit_price,
            tax_lot_method=tax_lot_method,
            special_instruction=special_instruction,
            order_strategy_type=OrderStrategyType.SINGLE,
            order_leg_collection=[
                OrderLeg(
                    order_leg_type=OrderLegType.EQUITY,
                    leg_id=1,
                    instrument={
                        "symbol": symbol,
                        "description": description or symbol,
                        "instrument_id": instrument_id or 0,
                        "net_change": Decimal("0"),
                        "type": "EQUITY"
                    },
                    instruction=instruction,
                    position_effect=PositionEffect.OPENING,
                    quantity=quantity,
                    quantity_type=QuantityType.ALL_SHARES,
                    div_cap_gains=DividendCapitalGains.REINVEST
                )
            ]
        )
        
    def create_stop_order(
        self,
        symbol: str,
        quantity: Union[int, Decimal],
        stop_price: Union[float, Decimal],
        instruction: OrderInstruction,
        description: Optional[str] = None,
        instrument_id: Optional[int] = None,
        session: OrderSession = OrderSession.NORMAL,
        duration: OrderDuration = OrderDuration.DAY,
        requested_destination: Optional[RequestedDestination] = None,
        tax_lot_method: Optional[TaxLotMethod] = None,
        special_instruction: Optional[SpecialInstruction] = None
    ) -> Order:
        """Create a stop order.
        
        Args:
            symbol: The symbol to trade
            quantity: The quantity to trade
            stop_price: The stop price
            instruction: BUY or SELL
            description: Optional description of the instrument
            instrument_id: Optional instrument ID
            session: Order session (default: NORMAL)
            duration: Order duration (default: DAY)
            requested_destination: Optional trading destination
            tax_lot_method: Optional tax lot method
            special_instruction: Optional special instruction
            
        Returns:
            Order object ready to be placed
        """
        quantity = Decimal(str(quantity))
        stop_price = Decimal(str(stop_price))
        return Order(
            session=session,
            duration=duration,
            order_type=OrderType.STOP,
            complex_order_strategy_type=ComplexOrderStrategyType.NONE,
            quantity=quantity,
            filled_quantity=Decimal("0"),
            remaining_quantity=quantity,
            requested_destination=requested_destination,
            stop_price=stop_price,
            stop_price_link_basis=StopPriceLinkBasis.MANUAL,
            stop_price_link_type=StopPriceLinkType.VALUE,
            stop_type=StopType.STANDARD,
            tax_lot_method=tax_lot_method,
            special_instruction=special_instruction,
            order_strategy_type=OrderStrategyType.SINGLE,
            order_leg_collection=[
                OrderLeg(
                    order_leg_type=OrderLegType.EQUITY,
                    leg_id=1,
                    instrument={
                        "symbol": symbol,
                        "description": description or symbol,
                        "instrument_id": instrument_id or 0,
                        "net_change": Decimal("0"),
                        "type": "EQUITY"
                    },
                    instruction=instruction,
                    position_effect=PositionEffect.OPENING,
                    quantity=quantity,
                    quantity_type=QuantityType.ALL_SHARES,
                    div_cap_gains=DividendCapitalGains.REINVEST
                )
            ]
        )
def create_stop_limit_order(
    self,
    symbol: str,
    quantity: Union[int, Decimal],
    stop_price: Union[float, Decimal],
    limit_price: Union[float, Decimal],
    instruction: OrderInstruction,
    description: Optional[str] = None,
    instrument_id: Optional[int] = None,
    session: OrderSession = OrderSession.NORMAL,
    duration: OrderDuration = OrderDuration.DAY,
    requested_destination: Optional[RequestedDestination] = None,
    tax_lot_method: Optional[TaxLotMethod] = None,
    special_instruction: Optional[SpecialInstruction] = None
) -> Order:
    """Create a stop-limit order.
    
    Args:
        symbol: The symbol to trade
        quantity: The quantity to trade
        stop_price: The stop price
        limit_price: The limit price
        instruction: BUY or SELL
        description: Optional description of the instrument
        instrument_id: Optional instrument ID
        session: Order session (default: NORMAL)
        duration: Order duration (default: DAY)
        requested_destination: Optional trading destination
        tax_lot_method: Optional tax lot method
        special_instruction: Optional special instruction
        
    Returns:
        Order object ready to be placed
    """
    quantity = Decimal(str(quantity))
    stop_price = Decimal(str(stop_price))
    limit_price = Decimal(str(limit_price))
    return Order(
        session=session,
        duration=duration,
        order_type=OrderType.STOP_LIMIT,
        complex_order_strategy_type=ComplexOrderStrategyType.NONE,
        quantity=quantity,
        filled_quantity=Decimal("0"),
        remaining_quantity=quantity,
        requested_destination=requested_destination,
        stop_price=stop_price,
        stop_price_link_basis=StopPriceLinkBasis.MANUAL,
        stop_price_link_type=StopPriceLinkType.VALUE,
        stop_type=StopType.STANDARD,
        price=limit_price,
        tax_lot_method=tax_lot_method,
        special_instruction=special_instruction,
        order_strategy_type=OrderStrategyType.SINGLE,
        order_leg_collection=[
            OrderLeg(
                order_leg_type=OrderLegType.EQUITY,
                leg_id=1,
                instrument={
                    "symbol": symbol,
                    "description": description or symbol,
                    "instrument_id": instrument_id or 0,
                    "net_change": Decimal("0"),
                    "type": "EQUITY"
                },
                instruction=instruction,
                position_effect=PositionEffect.OPENING,
                quantity=quantity,
                quantity_type=QuantityType.ALL_SHARES,
                div_cap_gains=DividendCapitalGains.REINVEST
            )
        ]
    )

def create_trailing_stop_order(
    self,
    symbol: str,
    quantity: Union[int, Decimal],
    stop_price_offset: Union[float, Decimal],
    instruction: OrderInstruction,
    description: Optional[str] = None,
    instrument_id: Optional[int] = None,
    session: OrderSession = OrderSession.NORMAL,
    duration: OrderDuration = OrderDuration.DAY,
    requested_destination: Optional[RequestedDestination] = None,
    tax_lot_method: Optional[TaxLotMethod] = None,
    special_instruction: Optional[SpecialInstruction] = None
) -> Order:
    """Create a trailing stop order.
    
    Args:
        symbol: The symbol to trade
        quantity: The quantity to trade
        stop_price_offset: The trailing amount
        instruction: BUY or SELL
        description: Optional description of the instrument
        instrument_id: Optional instrument ID
        session: Order session (default: NORMAL)
        duration: Order duration (default: DAY)
        requested_destination: Optional trading destination
        tax_lot_method: Optional tax lot method
        special_instruction: Optional special instruction
        
    Returns:
        Order object ready to be placed
    """
    quantity = Decimal(str(quantity))
    stop_price_offset = Decimal(str(stop_price_offset))
    return Order(
        session=session,
        duration=duration,
        order_type=OrderType.TRAILING_STOP,
        complex_order_strategy_type=ComplexOrderStrategyType.NONE,
        quantity=quantity,
        filled_quantity=Decimal("0"),
        remaining_quantity=quantity,
        requested_destination=requested_destination,
        stop_price_offset=stop_price_offset,
        stop_price_link_basis=StopPriceLinkBasis.MANUAL,
        stop_price_link_type=StopPriceLinkType.VALUE,
        stop_type=StopType.STANDARD,
        tax_lot_method=tax_lot_method,
        special_instruction=special_instruction,
        order_strategy_type=OrderStrategyType.SINGLE,
        order_leg_collection=[
            OrderLeg(
                order_leg_type=OrderLegType.EQUITY,
                leg_id=1,
                instrument={
                    "symbol": symbol,
                    "description": description or symbol,
                    "instrument_id": instrument_id or 0,
                    "net_change": Decimal("0"),
                    "type": "EQUITY"
                },
                instruction=instruction,
                position_effect=PositionEffect.OPENING,
                quantity=quantity,
                quantity_type=QuantityType.ALL_SHARES,
                div_cap_gains=DividendCapitalGains.REINVEST
            )
        ]
    )

def create_market_on_close_order(
    self,
    symbol: str,
    quantity: Union[int, Decimal],
    instruction: OrderInstruction,
    description: Optional[str] = None,
    instrument_id: Optional[int] = None,
    session: OrderSession = OrderSession.NORMAL,
    requested_destination: Optional[RequestedDestination] = None,
    tax_lot_method: Optional[TaxLotMethod] = None,
    special_instruction: Optional[SpecialInstruction] = None
) -> Order:
    """Create a market-on-close order.
    
    Args:
        symbol: The symbol to trade
        quantity: The quantity to trade
        instruction: BUY or SELL
        description: Optional description of the instrument
        instrument_id: Optional instrument ID
        session: Order session (default: NORMAL)
        requested_destination: Optional trading destination
        tax_lot_method: Optional tax lot method
        special_instruction: Optional special instruction
        
    Returns:
        Order object ready to be placed
    """
    quantity = Decimal(str(quantity))
    return Order(
        session=session,
        duration=OrderDuration.DAY,  # MOC orders must be DAY orders
        order_type=OrderType.MARKET_ON_CLOSE,
        complex_order_strategy_type=ComplexOrderStrategyType.NONE,
        quantity=quantity,
        filled_quantity=Decimal("0"),
        remaining_quantity=quantity,
        requested_destination=requested_destination,
        tax_lot_method=tax_lot_method,
        special_instruction=special_instruction,
        order_strategy_type=OrderStrategyType.SINGLE,
        order_leg_collection=[
            OrderLeg(
                order_leg_type=OrderLegType.EQUITY,
                leg_id=1,
                instrument={
                    "symbol": symbol,
                    "description": description or symbol,
                    "instrument_id": instrument_id or 0,
                    "net_change": Decimal("0"),
                    "type": "EQUITY"
                },
                instruction=instruction,
                position_effect=PositionEffect.OPENING,
                quantity=quantity,
                quantity_type=QuantityType.ALL_SHARES,
                div_cap_gains=DividendCapitalGains.REINVEST
            )
        ]
    )

def create_limit_on_close_order(
    self,
    symbol: str,
    quantity: Union[int, Decimal],
    limit_price: Union[float, Decimal],
    instruction: OrderInstruction,
    description: Optional[str] = None,
    instrument_id: Optional[int] = None,
    session: OrderSession = OrderSession.NORMAL,
    requested_destination: Optional[RequestedDestination] = None,
    tax_lot_method: Optional[TaxLotMethod] = None,
    special_instruction: Optional[SpecialInstruction] = None
) -> Order:
    """Create a limit-on-close order.
    
    Args:
        symbol: The symbol to trade
        quantity: The quantity to trade
        limit_price: The limit price
        instruction: BUY or SELL
        description: Optional description of the instrument
        instrument_id: Optional instrument ID
        session: Order session (default: NORMAL)
        requested_destination: Optional trading destination
        tax_lot_method: Optional tax lot method
        special_instruction: Optional special instruction
        
    Returns:
        Order object ready to be placed
    """
    quantity = Decimal(str(quantity))
    limit_price = Decimal(str(limit_price))
    return Order(
        session=session,
        duration=OrderDuration.DAY,  # LOC orders must be DAY orders
        order_type=OrderType.LIMIT_ON_CLOSE,
        complex_order_strategy_type=ComplexOrderStrategyType.NONE,
        quantity=quantity,
        filled_quantity=Decimal("0"),
        remaining_quantity=quantity,
        requested_destination=requested_destination,
        price=limit_price,
        tax_lot_method=tax_lot_method,
        special_instruction=special_instruction,
        order_strategy_type=OrderStrategyType.SINGLE,
        order_leg_collection=[
            OrderLeg(
                order_leg_type=OrderLegType.EQUITY,
                leg_id=1,
                instrument={
                    "symbol": symbol,
                    "description": description or symbol,
                    "instrument_id": instrument_id or 0,
                    "net_change": Decimal("0"),
                    "type": "EQUITY"
                },
                instruction=instruction,
                position_effect=PositionEffect.OPENING,
                quantity=quantity,
                quantity_type=QuantityType.ALL_SHARES,
                div_cap_gains=DividendCapitalGains.REINVEST
            )
        ]
    )
