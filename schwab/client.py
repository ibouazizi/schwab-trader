from typing import List, Optional, Dict, Any, Union, Callable
from datetime import datetime
import requests
from urllib.parse import urljoin
from decimal import Decimal
from .auth import SchwabAuth
from .dual_auth import DualSchwabAuth

# Import all models from generated packages
from .models.generated.market_data_models import ErrorResponse, QuoteResponse
from .models.generated.trading_models import (
    AccountNumberHash as AccountNumber, Account,
    Order, OrderType, Session as OrderSession,
    Duration as OrderDuration, RequestedDestination, 
    ComplexOrderStrategyType, OrderStrategyType, OrderLeg, OrderLegType,
    PositionEffect, StopPriceLinkBasis,
    StopPriceLinkType, StopType, Instruction as OrderInstruction,
    TaxLotMethod, SpecialInstruction,
    QuantityType, DivCapGains as DividendCapitalGains,
    Transaction, TransactionType, UserPreference
)
from .models.base import AccountNumbers  # Keep for now - custom aggregation model
from .order_management import OrderManagement
from .order_monitor import OrderMonitor
from .models.execution import ExecutionReport  # Keep - custom model without generated equivalent
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
        auth: Optional['SchwabAuth'] = None,
        market_data_client_id: Optional[str] = None,
        market_data_client_secret: Optional[str] = None
    ):
        """Initialize the client with OAuth credentials.
        
        Args:
            client_id: OAuth client ID for Trading API
            client_secret: OAuth client secret for Trading API
            redirect_uri: OAuth callback URL
            auth: Optional pre-configured SchwabAuth instance
            market_data_client_id: OAuth client ID for Market Data API (optional)
            market_data_client_secret: OAuth client secret for Market Data API (optional)
        """
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        
        # Initialize authentication
        if market_data_client_id and market_data_client_secret:
            # Use dual auth if market data credentials are provided
            self.dual_auth = DualSchwabAuth(
                client_id, client_secret, redirect_uri,
                market_data_client_id, market_data_client_secret
            )
            # If auth is provided, set it on the trading auth
            if auth:
                self.dual_auth.trading_auth = auth
            self.auth = self.dual_auth.trading_auth
        else:
            # Single auth mode
            self.dual_auth = None
            self.auth = auth or SchwabAuth(client_id, client_secret, redirect_uri)
        
        # Initialize order management and monitoring
        self.order_management = OrderManagement(self)
        self.order_monitor = OrderMonitor(self)
    
    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request to the API.
        
        Args:
            endpoint: API endpoint
            params: Optional query parameters
            
        Returns:
            API response as dictionary
        """
        return self._make_request("GET", endpoint, params=params)
    
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
                pass
        """
        # Get appropriate auth for the endpoint
        if self.dual_auth and "/marketdata/" in endpoint:
            # Use market data auth
            auth = self.dual_auth.get_auth_for_endpoint(endpoint)
            self.dual_auth.ensure_market_data_token()
            self.session.headers.update(auth.authorization_header)
        else:
            # Use trading auth
            self.auth.ensure_valid_token()
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
        
        # Check for errors before parsing
        if response.status_code >= 400:
            try:
                error_data = response.json()
                
                # If it's a validation error with datetime, extract the message
                if isinstance(error_data, dict):
                    error_msg = str(error_data.get('message', '') or error_data.get('error', '') or error_data)
                    if "datetime" in error_msg and "pattern" in error_msg:
                        # This is a datetime validation error from the API
                        raise ValueError(f"API datetime validation error: {error_msg}")
            except ValueError:
                raise
            except Exception as e:
                pass
        
        response.raise_for_status()
        
        # Parse the JSON response
        try:
            response_text = response.text
            
            # Check if the response contains the datetime validation error
            if "Unable to apply constraint" in response_text and "datetime" in response_text:
                # Extract the error message if possible
                try:
                    import json
                    error_data = json.loads(response_text)
                    if isinstance(error_data, dict) and 'message' in error_data:
                        raise ValueError(f"Schwab API validation error: {error_data['message']}")
                except:
                    pass
                    
                raise TypeError(f"Unable to apply constraint 'pattern' to supplied value 2025-02-26 00:00:00 for schema of type 'datetime'")
            
            data = response.json()
            
            # Clean up datetime values that don't match expected patterns
            data = self._fix_datetime_formats(data)
            
            return data
        except Exception as e:
            # If JSON parsing fails, re-raise the exception
            raise
    
    def _fix_datetime_formats(self, data):
        """Fix datetime formats in API responses.
        
        Converts datetime objects and strings to ISO format expected by models.
        """
        from datetime import datetime as dt
        
        if isinstance(data, dict):
            fixed = {}
            for key, value in data.items():
                # Check for datetime fields that need fixing
                if any(date_key in key.lower() for date_key in ['date', 'datetime']):
                    if isinstance(value, dt):
                        # Convert datetime object to ISO string
                        iso_string = value.isoformat() + 'Z' if value.tzinfo is None else value.isoformat()
                        fixed[key] = iso_string
                    elif isinstance(value, str):
                        # Check if it's in the problematic format
                        if ' ' in value and len(value) >= 19:  # "YYYY-MM-DD HH:MM:SS" format
                            # Convert to ISO format
                            fixed[key] = value.replace(' ', 'T') + 'Z'
                        else:
                            fixed[key] = value
                    else:
                        fixed[key] = value
                else:
                    fixed[key] = self._fix_datetime_formats(value)
            return fixed
        elif isinstance(data, list):
            return [self._fix_datetime_formats(item) for item in data]
        elif isinstance(data, dt):
            # Handle datetime objects at any level
            return data.isoformat() + 'Z' if data.tzinfo is None else data.isoformat()
        else:
            return data
    
    def get_account_numbers(self) -> AccountNumbers:
        """Get list of account numbers and their encrypted values."""
        data = self._make_request("GET", "/accounts/accountNumbers")
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
            "/accounts",
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
        data = self._make_request("GET", f"/accounts/{account_number}", params=params)
        return Account(**data)
    
    def get_orders(
        self,
        account_number: str,
        from_entered_time: datetime,
        to_entered_time: datetime,
        max_results: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Order]:
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
            "fromEnteredTime": from_entered_time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "toEnteredTime": to_entered_time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        }
        if max_results is not None:
            params["maxResults"] = max_results
        if status is not None:
            params["status"] = status
            
        data = self._make_request("GET", f"/accounts/{account_number}/orders", params=params)
        return [Order(**order) for order in data]
        
    def place_order(self, account_number: str, order: Order) -> None:
        """Place an order for a specific account.
        
        Args:
            account_number: The encrypted account number
            order: The order to place
            
        Returns:
            None if successful
            
        Raises:
            requests.exceptions.RequestException: If the request fails
                pass
        """
        self._make_request("POST", f"/accounts/{account_number}/orders", json=order.model_dump(by_alias=True))
        
    def preview_order(self, account_number: str, order: Order) -> Dict[str, Any]:
        """Preview an order before placing it.
        
        Get estimated commission, fees, and other order details before placement.
        
        Args:
            account_number: The encrypted account number
            order: The order to preview
            
        Returns:
            Dictionary containing order preview information including:
            - estimatedCommission: Estimated commission for the order
            - estimatedFees: Estimated fees
            - estimatedTotal: Estimated total cost/proceeds
            - orderValidation: Validation messages if any
            
        Raises:
            requests.exceptions.RequestException: If the request fails
                pass
        """
        data = self._make_request(
            "POST", 
            f"/accounts/{account_number}/previewOrder", 
            json=order.model_dump(by_alias=True)
        )
        return data
        
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
                pass
        """
        self._make_request(
            "PUT",
            f"/accounts/{account_number}/orders/{order_id}",
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
                pass
        """
        self._make_request("DELETE", f"/accounts/{account_number}/orders/{order_id}")
        
    def get_order(self, account_number: str, order_id: int) -> Order:
        """Get a specific order by its ID.
        
        Args:
            account_number: The encrypted account number
            order_id: The ID of the order to retrieve
            
        Returns:
            The order details
            
        Raises:
            requests.exceptions.RequestException: If the request fails
                pass
        """
        data = self._make_request("GET", f"/accounts/{account_number}/orders/{order_id}")
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
        
    # Transaction Methods
    def get_transactions(
        self,
        account_number: str,
        start_date: datetime,
        end_date: datetime,
        transaction_type: Optional[TransactionType] = None,
        symbol: Optional[str] = None
    ) -> List[Transaction]:
        """Get transaction history for an account.
        
        Args:
            account_number: The encrypted account number
            start_date: Start date for transaction history
            end_date: End date for transaction history
            transaction_type: Optional filter by transaction type
            symbol: Optional filter by symbol
            
        Returns:
            List of transactions
            
        Raises:
            requests.exceptions.RequestException: If the request fails
                pass
        """
        params = {
            "startDate": start_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "endDate": end_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
        
        if transaction_type:
            params["types"] = transaction_type.value
            
        if symbol:
            params["symbol"] = symbol
            
        data = self._make_request("GET", f"/accounts/{account_number}/transactions", params=params)
        return [Transaction(**txn) for txn in data]
        
    def get_transaction(self, account_number: str, transaction_id: int) -> Transaction:
        """Get details of a specific transaction.
        
        Args:
            account_number: The encrypted account number
            transaction_id: The transaction ID
            
        Returns:
            Transaction details
            
        Raises:
            requests.exceptions.RequestException: If the request fails
                pass
        """
        data = self._make_request("GET", f"/accounts/{account_number}/transactions/{transaction_id}")
        return Transaction(**data)
        
    # User Preferences Methods
    def get_user_preferences(self) -> UserPreference:
        """Get user trading preferences.
        
        Returns:
            UserPreference object containing:
            - accounts: List of user preference accounts
            - streamer_info: List of streaming service information
            - offers: List of available offers
            
        Raises:
            requests.exceptions.RequestException: If the request fails
                pass
        """
        response = self._make_request("GET", "/userPreference")
        return UserPreference(**response)
        
    def update_user_preferences(self, preferences: Dict[str, Any]) -> None:
        """Update user trading preferences.
        
        Args:
            preferences: Dictionary of preferences to update
            
        Returns:
            None if successful
            
        Raises:
            requests.exceptions.RequestException: If the request fails
                pass
        """
        self._make_request("PUT", "/userPreference", json=preferences)
        
    # All Orders Methods
    def get_all_orders(
        self,
        from_entered_time: datetime,
        to_entered_time: datetime,
        max_results: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Order]:
        """Get orders for all linked accounts.
        
        Args:
            from_entered_time: Start time for orders
            to_entered_time: End time for orders
            max_results: Maximum number of orders to return
            status: Optional filter by order status
            
        Returns:
            List of orders across all accounts
            
        Raises:
            requests.exceptions.RequestException: If the request fails
                pass
        """
        params = {
            "fromEnteredTime": from_entered_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "toEnteredTime": to_entered_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }
        
        if max_results:
            params["maxResults"] = max_results
            
        if status:
            params["status"] = status
            
        data = self._make_request("GET", "/orders", params=params)
        return [Order(**order) for order in data]
        
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
    def get_option_chain(self, symbol: str, contract_type: str = None, strike_count: int = None,
                        include_underlying_quote: bool = None, strategy: str = None,
                        strike_from_date: str = None, strike_to_date: str = None,
                        strike_from: float = None, strike_to: float = None,
                        expiration_month: str = None, option_type: str = None,
                        days_to_expiration: int = None, exp_month: str = None,
                        option_detail_flag: bool = None, 
                        entitlement: str = "np") -> Dict[str, Any]:
        """
        Get option chain for a symbol.
        
        Args:
            symbol: The underlying symbol for the option chain
            contract_type: Type of contracts (CALL, PUT, ALL)
            strike_count: Number of strikes to return
            include_underlying_quote: Include quote for underlying symbol
            strategy: Option strategy (SINGLE, ANALYTICAL, COVERED, VERTICAL, etc.)
            strike_from_date: From date for strike range (yyyy-MM-dd)
            strike_to_date: To date for strike range (yyyy-MM-dd)
            strike_from: From strike price
            strike_to: To strike price
            expiration_month: Expiration month (ALL, JAN, FEB, etc.)
            option_type: Option type (S for Standard, NS for Non-Standard, ALL)
            days_to_expiration: Days to expiration
            exp_month: Expiration month (ALL, JAN, FEB, etc.)
            option_detail_flag: Include additional option details
            entitlement: Entitlement level (np, npbo, retail)
            
        Returns:
            Dictionary containing option chain data
        """
        params = {
            "symbol": symbol,
            "entitlement": entitlement
        }
        
        # Add optional parameters
        if contract_type:
            params["contractType"] = contract_type
        if strike_count is not None:
            params["strikeCount"] = strike_count
        if include_underlying_quote is not None:
            params["includeUnderlyingQuote"] = include_underlying_quote
        if strategy:
            params["strategy"] = strategy
        if strike_from_date:
            params["strikeFromDate"] = strike_from_date
        if strike_to_date:
            params["strikeToDate"] = strike_to_date
        if strike_from is not None:
            params["strikeFrom"] = strike_from
        if strike_to is not None:
            params["strikeTo"] = strike_to
        if expiration_month:
            params["expirationMonth"] = expiration_month
        if option_type:
            params["optionType"] = option_type
        if days_to_expiration is not None:
            params["daysToExpiration"] = days_to_expiration
        if exp_month:
            params["expMonth"] = exp_month
        if option_detail_flag is not None:
            params["optionDetailFlag"] = option_detail_flag
            
        return self._make_request("GET", "/marketdata/v1/chains", params=params)
    
    def get_option_expiration_chain(self, symbol: str, 
                                   entitlement: str = "np") -> Dict[str, Any]:
        """
        Get option expiration dates for a symbol.
        
        Args:
            symbol: The underlying symbol
            entitlement: Entitlement level (np, npbo, retail)
            
        Returns:
            Dictionary containing expiration dates
        """
        params = {
            "symbol": symbol,
            "entitlement": entitlement
        }
        
        return self._make_request("GET", "/marketdata/v1/expirationchain", params=params)
    
    def get_price_history(self, symbol: str, 
                         period_type: str = "day",
                         period: Optional[int] = None,
                         frequency_type: Optional[str] = None,
                         frequency: Optional[int] = None,
                         start_date: Optional[int] = None,
                         end_date: Optional[int] = None,
                         need_extended_hours_data: bool = False,
                         need_previous_close: bool = False) -> Dict[str, Any]:
        """
        Get price history for a symbol.
        
        Args:
            symbol: The symbol to get price history for
            period_type: The chart period type (day, month, year, ytd)
            period: The number of periods
                - day: 1, 2, 3, 4, 5, 10
                - month: 1, 2, 3, 6
                - year: 1, 2, 3, 5, 10, 15, 20
                - ytd: 1
            frequency_type: The time frequency type
                - day: minute
                - month: daily, weekly
                - year: daily, weekly, monthly
                - ytd: daily, weekly
            frequency: The time frequency (1, 5, 10, 15, 30 for minute)
            start_date: Start date in milliseconds since epoch
            end_date: End date in milliseconds since epoch
            need_extended_hours_data: Include extended hours data
            need_previous_close: Include previous close data
            
        Returns:
            Dictionary containing candles with OHLC data
        """
        params = {
            "symbol": symbol,
            "periodType": period_type,
            "needExtendedHoursData": need_extended_hours_data,
            "needPreviousClose": need_previous_close
        }
        
        if period is not None:
            params["period"] = period
        if frequency_type is not None:
            params["frequencyType"] = frequency_type
        if frequency is not None:
            params["frequency"] = frequency
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date
            
        return self._make_request("GET", "/marketdata/v1/pricehistory", params=params)
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



# Import and bind advanced methods
from . import client_advanced_methods

# Bind advanced methods to SchwabClient
SchwabClient.create_multi_leg_option_order = client_advanced_methods.create_multi_leg_option_order
SchwabClient.create_one_cancels_other_order = client_advanced_methods.create_one_cancels_other_order
SchwabClient.create_one_triggers_other_order = client_advanced_methods.create_one_triggers_other_order
SchwabClient.create_bracket_order = client_advanced_methods.create_bracket_order
SchwabClient.get_portfolio_analysis = client_advanced_methods.get_portfolio_analysis
SchwabClient.get_tax_lots = client_advanced_methods.get_tax_lots
SchwabClient.place_order_with_tax_lot = client_advanced_methods.place_order_with_tax_lot
SchwabClient.get_dividend_history = client_advanced_methods.get_dividend_history
SchwabClient.get_cost_basis_summary = client_advanced_methods.get_cost_basis_summary
SchwabClient.calculate_account_performance = client_advanced_methods.calculate_account_performance
