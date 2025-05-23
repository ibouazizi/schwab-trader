# Schwab Trader API Reference

## Table of Contents
1. [Client Classes](#client-classes)
   - [SchwabClient](#schwabclient)
   - [AsyncSchwabClient](#asyncschwabclient)
   - [PaperTradingClient](#papertradingclient)
   - [AsyncPaperTradingClient](#asyncpapertradingclient)
2. [Authentication](#authentication)
   - [SchwabAuth](#schwabauth)
3. [Account Management](#account-management)
   - [Account Models](#account-models)
   - [Account Methods](#account-methods)
4. [Order Management](#order-management)
   - [Order Models](#order-models)
   - [Order Methods](#order-methods)
   - [Order Creation Methods](#order-creation-methods)
   - [Order Modification Methods](#order-modification-methods)
5. [Market Data](#market-data)
   - [Quote Models](#quote-models)
   - [Quote Methods](#quote-methods)
6. [Portfolio Management](#portfolio-management)
   - [PortfolioManager](#portfoliomanager)
7. [Streaming Data](#streaming-data)
   - [SchwabStreamer](#schwabstreamer)
   - [StreamerClient](#streamerclient)
8. [Order Monitoring](#order-monitoring)
   - [OrderMonitor](#ordermonitor)
9. [Paper Trading](#paper-trading)
   - [Paper Trading Components](#paper-trading-components)
10. [Error Handling](#error-handling)
    - [Exception Classes](#exception-classes)
    - [Error Handling Patterns](#error-handling-patterns)

## Client Classes

### SchwabClient

The main synchronous client for interacting with Schwab's Trading API.

```python
from schwab import SchwabClient

client = SchwabClient(
    auth: Optional[SchwabAuth] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    redirect_uri: Optional[str] = None,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None
)
```

#### Constructor Parameters
- `auth` (Optional[SchwabAuth]): Pre-configured auth instance
- `client_id` (Optional[str]): OAuth client ID from Schwab
- `client_secret` (Optional[str]): OAuth client secret from Schwab
- `redirect_uri` (Optional[str]): OAuth callback URL
- `access_token` (Optional[str]): Existing access token
- `refresh_token` (Optional[str]): Existing refresh token

#### Inherits From
- `QuotesMixin`: Provides market data functionality

### AsyncSchwabClient

Asynchronous version of the client for non-blocking operations.

```python
from schwab import AsyncSchwabClient

async with AsyncSchwabClient(auth=auth) as client:
    # Perform async operations
    accounts = await client.get_account_numbers()
```

All methods from SchwabClient are available with async/await syntax.

### PaperTradingClient

Extension of SchwabClient with paper trading safety features.

```python
from schwab.paper_trading import PaperTradingClient

paper_client = PaperTradingClient(auth=auth)
# Visual indicators show when in paper trading mode
```

#### Additional Features
- Automatic paper account detection
- Visual indicators for paper trading operations
- Safety checks to prevent accidental real trades
- Method decoration for paper trading validation

### AsyncPaperTradingClient

Asynchronous version of PaperTradingClient.

```python
from schwab.paper_trading import AsyncPaperTradingClient

async with AsyncPaperTradingClient(auth=auth) as client:
    # Async paper trading operations
    await client.place_order(account_number, order)
```

## Authentication

### SchwabAuth

Handles OAuth 2.0 authentication flow with automatic token management.

```python
from schwab.auth import SchwabAuth

auth = SchwabAuth(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
    token_expires_at: Optional[datetime] = None
)
```

#### Methods

```python
def get_authorization_url(self) -> str:
    """Get the URL for the OAuth authorization step."""

def exchange_code_for_tokens(self, authorization_code: str) -> Dict[str, Any]:
    """Exchange authorization code for access and refresh tokens."""

def refresh_access_token(self) -> Dict[str, Any]:
    """Refresh the access token using the refresh token."""

def ensure_valid_token(self) -> None:
    """Ensure we have a valid access token, refreshing if necessary."""

def get_auth_header(self) -> Dict[str, str]:
    """Get the authorization header for API requests."""

def save_tokens(self, filepath: str) -> None:
    """Save tokens to a file for persistence."""

def load_tokens(self, filepath: str) -> None:
    """Load tokens from a file."""
```

## Account Management

### Account Models

#### Account
```python
from schwab.models.account import Account

class Account(BaseModel):
    securitiesAccount: SecuritiesAccount
    aggregatedBalance: Optional[AggregatedBalance]
```

#### SecuritiesAccount
```python
class SecuritiesAccount(BaseModel):
    type: str
    accountNumber: str
    roundTrips: int
    isDayTrader: bool
    isClosingOnlyRestricted: bool
    pfcbFlag: bool
    positions: Optional[List[Position]]
    initialBalances: Optional[InitialBalances]
    currentBalances: Optional[CurrentBalances]
    projectedBalances: Optional[ProjectedBalances]
```

#### Position
```python
class Position(BaseModel):
    shortQuantity: float
    averagePrice: float
    currentDayProfitLoss: float
    currentDayProfitLossPercentage: float
    longQuantity: float
    settledLongQuantity: float
    settledShortQuantity: float
    instrument: Instrument
    marketValue: float
    maintenanceRequirement: float
    averageLongPrice: float
    averageShortPrice: float
    taxLotAverageLongPrice: float
    taxLotAverageShortPrice: float
    longOpenProfitLoss: float
    shortOpenProfitLoss: float
    previousSessionLongQuantity: float
    previousSessionShortQuantity: float
    currentDayCost: float
```

#### Balances
```python
class CurrentBalances(BaseModel):
    liquidationValue: float
    cashBalance: float
    cashAvailableForTrading: float
    cashAvailableForWithdrawal: float
    cashCall: float
    longMarketValue: float
    shortMarketValue: float
    pendingDeposits: float
    cashDebitCallValue: float
    unsettledCash: float
    totalCash: float
    accountValue: float
    availableFunds: float
    availableFundsNonMarginableTrade: float
    buyingPower: float
    buyingPowerNonMarginableTrade: float
    dayTradingBuyingPower: float
    dayTradingBuyingPowerCall: float
    equity: float
    equityPercentage: float
    maintenanceCall: float
    maintenanceRequirement: float
    marginBalance: float
    regTCall: float
    shortBalance: float
    sma: float
```

### Account Methods

```python
def get_account_numbers(self) -> List[AccountNumberHash]:
    """Get all account numbers associated with the authenticated user."""

def get_accounts(self, include_positions: bool = False) -> List[Account]:
    """Get all accounts with optional position information."""

def get_account(
    self, 
    account_number: str, 
    include_positions: bool = False
) -> Account:
    """Get detailed account information for a specific account."""

def get_transactions(
    self,
    account_number: str,
    start_date: datetime,
    end_date: datetime,
    types: Optional[str] = None,
    symbol: Optional[str] = None
) -> List[Transaction]:
    """Get transaction history for an account."""

def get_user_preferences(self) -> UserPreference:
    """Get user preferences and settings."""
```

## Order Management

### Order Models

#### Order
```python
from schwab.models.orders import Order

class Order(BaseModel):
    session: Optional[str]
    duration: Optional[str]
    orderType: Optional[str]
    cancelTime: Optional[str]
    complexOrderStrategyType: Optional[str]
    quantity: Optional[float]
    filledQuantity: Optional[float]
    remainingQuantity: Optional[float]
    requestedDestination: Optional[str]
    destinationLinkName: Optional[str]
    releaseTime: Optional[str]
    stopPrice: Optional[float]
    stopPriceLinkBasis: Optional[str]
    stopPriceLinkType: Optional[str]
    stopPriceOffset: Optional[float]
    stopType: Optional[str]
    priceLinkBasis: Optional[str]
    priceLinkType: Optional[str]
    price: Optional[float]
    taxLotMethod: Optional[str]
    orderLegCollection: Optional[List[OrderLeg]]
    activationPrice: Optional[float]
    specialInstruction: Optional[str]
    orderStrategyType: Optional[str]
    orderId: Optional[int]
    cancelable: Optional[bool]
    editable: Optional[bool]
    status: Optional[str]
    enteredTime: Optional[str]
    closeTime: Optional[str]
    tag: Optional[str]
    accountNumber: Optional[int]
    orderActivityCollection: Optional[List[OrderActivity]]
    replacingOrderCollection: Optional[List[Order]]
    childOrderStrategies: Optional[List[Order]]
    statusDescription: Optional[str]
```

#### OrderLeg
```python
class OrderLeg(BaseModel):
    orderLegType: Optional[str]
    legId: Optional[int]
    instrument: Optional[Instrument]
    instruction: Optional[str]
    positionEffect: Optional[str]
    quantity: Optional[float]
    quantityType: Optional[str]
    divCapGains: Optional[str]
    toSymbol: Optional[str]
```

#### Enums
```python
class OrderInstruction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    BUY_TO_COVER = "BUY_TO_COVER"
    SELL_SHORT = "SELL_SHORT"
    BUY_TO_OPEN = "BUY_TO_OPEN"
    BUY_TO_CLOSE = "BUY_TO_CLOSE"
    SELL_TO_OPEN = "SELL_TO_OPEN"
    SELL_TO_CLOSE = "SELL_TO_CLOSE"
    EXCHANGE = "EXCHANGE"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"
    MARKET_ON_CLOSE = "MARKET_ON_CLOSE"
    LIMIT_ON_CLOSE = "LIMIT_ON_CLOSE"
    CABINET = "CABINET"
    NON_MARKETABLE = "NON_MARKETABLE"
    NET_DEBIT = "NET_DEBIT"
    NET_CREDIT = "NET_CREDIT"
    NET_ZERO = "NET_ZERO"

class OrderStatus(str, Enum):
    AWAITING_PARENT_ORDER = "AWAITING_PARENT_ORDER"
    AWAITING_CONDITION = "AWAITING_CONDITION"
    AWAITING_STOP_CONDITION = "AWAITING_STOP_CONDITION"
    AWAITING_MANUAL_REVIEW = "AWAITING_MANUAL_REVIEW"
    ACCEPTED = "ACCEPTED"
    AWAITING_UR_OUT = "AWAITING_UR_OUT"
    PENDING_ACTIVATION = "PENDING_ACTIVATION"
    QUEUED = "QUEUED"
    WORKING = "WORKING"
    REJECTED = "REJECTED"
    PENDING_CANCEL = "PENDING_CANCEL"
    CANCELED = "CANCELED"
    PENDING_REPLACE = "PENDING_REPLACE"
    REPLACED = "REPLACED"
    FILLED = "FILLED"
    EXPIRED = "EXPIRED"
    NEW = "NEW"
    AWAITING_RELEASE_TIME = "AWAITING_RELEASE_TIME"
    PENDING_ACKNOWLEDGEMENT = "PENDING_ACKNOWLEDGEMENT"
    PENDING_RECALL = "PENDING_RECALL"
    UNKNOWN = "UNKNOWN"

class OrderDuration(str, Enum):
    DAY = "DAY"
    GOOD_TILL_CANCEL = "GOOD_TILL_CANCEL"
    FILL_OR_KILL = "FILL_OR_KILL"
    IMMEDIATE_OR_CANCEL = "IMMEDIATE_OR_CANCEL"
    WEEK = "WEEK"
    MONTH = "MONTH"
    END_OF_WEEK = "END_OF_WEEK"
    END_OF_MONTH = "END_OF_MONTH"
    NEXT_END_OF_MONTH = "NEXT_END_OF_MONTH"
    UNKNOWN = "UNKNOWN"

class ComplexOrderStrategyType(str, Enum):
    NONE = "NONE"
    COVERED = "COVERED"
    VERTICAL = "VERTICAL"
    BACK_RATIO = "BACK_RATIO"
    CALENDAR = "CALENDAR"
    DIAGONAL = "DIAGONAL"
    STRADDLE = "STRADDLE"
    STRANGLE = "STRANGLE"
    COLLAR_SYNTHETIC = "COLLAR_SYNTHETIC"
    BUTTERFLY = "BUTTERFLY"
    CONDOR = "CONDOR"
    IRON_CONDOR = "IRON_CONDOR"
    VERTICAL_ROLL = "VERTICAL_ROLL"
    COLLAR_WITH_STOCK = "COLLAR_WITH_STOCK"
    DOUBLE_DIAGONAL = "DOUBLE_DIAGONAL"
    UNBALANCED_BUTTERFLY = "UNBALANCED_BUTTERFLY"
    UNBALANCED_CONDOR = "UNBALANCED_CONDOR"
    UNBALANCED_IRON_CONDOR = "UNBALANCED_IRON_CONDOR"
    UNBALANCED_VERTICAL_ROLL = "UNBALANCED_VERTICAL_ROLL"
    MUTUAL_FUND_SWAP = "MUTUAL_FUND_SWAP"
    CUSTOM = "CUSTOM"
```

### Order Methods

```python
def place_order(self, account_number: str, order: Order) -> Dict[str, Any]:
    """Place an order for the specified account."""

def get_order(self, account_number: str, order_id: int) -> Order:
    """Get order details by ID."""

def get_orders(
    self,
    account_number: str,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    status: Optional[str] = None,
    max_results: Optional[int] = None
) -> List[Order]:
    """Get orders matching the specified criteria."""

def replace_order(
    self,
    account_number: str,
    order_id: int,
    new_order: Order
) -> Dict[str, Any]:
    """Replace an existing order with a new order."""

def cancel_order(self, account_number: str, order_id: int) -> None:
    """Cancel an existing order."""
```

### Order Creation Methods

```python
def create_market_order(
    self,
    symbol: str,
    quantity: int,
    instruction: str,
    account_type: str = "CASH",
    duration: str = "DAY",
    session: str = "NORMAL",
    position_effect: str = "OPENING"
) -> Order:
    """Create a market order."""

def create_limit_order(
    self,
    symbol: str,
    quantity: int,
    limit_price: float,
    instruction: str,
    account_type: str = "CASH",
    duration: str = "DAY",
    session: str = "NORMAL",
    position_effect: str = "OPENING"
) -> Order:
    """Create a limit order."""

def create_stop_order(
    self,
    symbol: str,
    quantity: int,
    stop_price: float,
    instruction: str,
    account_type: str = "CASH",
    duration: str = "DAY",
    session: str = "NORMAL",
    position_effect: str = "OPENING"
) -> Order:
    """Create a stop order."""

def create_stop_limit_order(
    self,
    symbol: str,
    quantity: int,
    stop_price: float,
    limit_price: float,
    instruction: str,
    account_type: str = "CASH",
    duration: str = "DAY",
    session: str = "NORMAL",
    position_effect: str = "OPENING"
) -> Order:
    """Create a stop-limit order."""

def create_trailing_stop_order(
    self,
    symbol: str,
    quantity: int,
    stop_price_offset: float,
    instruction: str,
    stop_price_link_type: str = "VALUE",
    account_type: str = "CASH",
    duration: str = "DAY",
    session: str = "NORMAL",
    position_effect: str = "OPENING"
) -> Order:
    """Create a trailing stop order."""

def create_market_on_close_order(
    self,
    symbol: str,
    quantity: int,
    instruction: str,
    account_type: str = "CASH",
    position_effect: str = "OPENING"
) -> Order:
    """Create a market-on-close order."""

def create_limit_on_close_order(
    self,
    symbol: str,
    quantity: int,
    limit_price: float,
    instruction: str,
    account_type: str = "CASH",
    position_effect: str = "OPENING"
) -> Order:
    """Create a limit-on-close order."""
```

### Order Modification Methods

```python
def modify_order_price(
    self,
    account_number: str,
    order_id: int,
    new_price: float
) -> Order:
    """Modify the price of an existing order."""

def modify_order_quantity(
    self,
    account_number: str,
    order_id: int,
    new_quantity: int
) -> Order:
    """Modify the quantity of an existing order."""

def batch_cancel_orders(
    self,
    account_number: str,
    order_ids: List[int]
) -> Dict[int, bool]:
    """Cancel multiple orders in batch."""

def batch_modify_orders(
    self,
    account_number: str,
    modifications: List[Dict[str, Any]]
) -> Dict[int, Union[Order, Exception]]:
    """Modify multiple orders in batch."""
```

## Market Data

### Quote Models

#### Quote
```python
from schwab.models.quotes import Quote

class Quote(BaseModel):
    _52WeekHigh: Optional[float]
    _52WeekLow: Optional[float]
    askMICId: Optional[str]
    askPrice: Optional[float]
    askSize: Optional[int]
    askTime: Optional[int]
    bidMICId: Optional[str]
    bidPrice: Optional[float]
    bidSize: Optional[int]
    bidTime: Optional[int]
    closePrice: Optional[float]
    highPrice: Optional[float]
    lastMICId: Optional[str]
    lastPrice: Optional[float]
    lastSize: Optional[int]
    lowPrice: Optional[float]
    mark: Optional[float]
    markChange: Optional[float]
    markChangePercentage: Optional[float]
    netChange: Optional[float]
    netPercentChange: Optional[float]
    openPrice: Optional[float]
    postMarketChange: Optional[float]
    postMarketPercentChange: Optional[float]
    quoteTime: Optional[int]
    securityStatus: Optional[str]
    totalVolume: Optional[int]
    tradeTime: Optional[int]
```

#### Reference
```python
class Reference(BaseModel):
    contractType: Optional[str]
    cusip: Optional[str]
    daysToExpiration: Optional[int]
    deliverables: Optional[str]
    description: Optional[str]
    exchange: Optional[str]
    exchangeName: Optional[str]
    exerciseType: Optional[str]
    expirationDate: Optional[int]
    expirationType: Optional[str]
    htbQuantity: Optional[float]
    htbRate: Optional[float]
    inTheMoney: Optional[bool]
    isIndex: Optional[bool]
    isPennyPilot: Optional[bool]
    lastTradingDay: Optional[int]
    multiplier: Optional[float]
    optionType: Optional[str]
    settlementType: Optional[str]
    strikePrice: Optional[float]
    symbol: Optional[str]
    type: Optional[str]
    underlyingSymbol: Optional[str]
    uvExpirationType: Optional[str]
```

### Quote Methods

```python
def get_quotes(self, symbols: Union[str, List[str]]) -> Dict[str, QuoteResponse]:
    """Get real-time quotes for specified symbols."""

def get_quote(self, symbol: str) -> QuoteResponse:
    """Get real-time quote for a single symbol."""

def get_options_chain(
    self,
    symbol: str,
    contract_type: Optional[str] = None,
    strike_count: Optional[int] = None,
    include_quotes: Optional[bool] = None,
    strategy: Optional[str] = None,
    interval: Optional[float] = None,
    strike: Optional[float] = None,
    range: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    volatility: Optional[float] = None,
    underlying_price: Optional[float] = None,
    interest_rate: Optional[float] = None,
    days_to_expiration: Optional[int] = None,
    exp_month: Optional[str] = None,
    option_type: Optional[str] = None,
    entitlement: Optional[str] = None
) -> OptionChain:
    """Get options chain for a symbol."""

def get_price_history(
    self,
    symbol: str,
    period_type: Optional[str] = None,
    period: Optional[int] = None,
    frequency_type: Optional[str] = None,
    frequency: Optional[int] = None,
    start_date: Optional[int] = None,
    end_date: Optional[int] = None,
    need_extended_hours_data: Optional[bool] = None,
    need_previous_close: Optional[bool] = None
) -> PriceHistory:
    """Get historical price data."""
```

## Portfolio Management

### PortfolioManager

Comprehensive portfolio management and tracking system.

```python
from schwab.portfolio import PortfolioManager

portfolio = PortfolioManager(
    client: Union[SchwabClient, AsyncSchwabClient],
    refresh_interval: int = 300  # 5 minutes
)
```

#### Methods

```python
def add_account(self, account_number: str) -> None:
    """Add an account to the portfolio."""

def remove_account(self, account_number: str) -> None:
    """Remove an account from the portfolio."""

def refresh_positions(self) -> None:
    """Refresh all positions across accounts."""

async def async_refresh_positions(self) -> None:
    """Async version of refresh_positions."""

def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
    """Get aggregated position for a symbol across all accounts."""

def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
    """Get all positions aggregated by symbol."""

def get_portfolio_summary(self) -> Dict[str, Any]:
    """Get comprehensive portfolio summary including P&L and allocations."""

def place_order(
    self,
    account_number: str,
    order: Order,
    track: bool = True
) -> Dict[str, Any]:
    """Place an order and optionally track it."""

def monitor_orders(
    self,
    callback: Callable[[str, Any], None],
    interval: float = 1.0
) -> None:
    """Monitor orders with callback notifications."""

def stop_monitoring(self) -> None:
    """Stop order monitoring."""

def get_order_history(self) -> List[Dict[str, Any]]:
    """Get history of all tracked orders."""

def get_executions(self) -> List[Dict[str, Any]]:
    """Get all executions."""

def save_state(self, filepath: str) -> None:
    """Save portfolio state to file."""

def load_state(self, filepath: str) -> None:
    """Load portfolio state from file."""
```

## Streaming Data

### SchwabStreamer

WebSocket streaming client for real-time market data.

```python
from schwab.streaming import SchwabStreamer

streamer = SchwabStreamer(
    client: Union[SchwabClient, AsyncSchwabClient],
    account_number: Optional[str] = None
)
```

#### Methods

```python
def subscribe_quotes(
    self,
    symbols: List[str],
    callback: Callable[[Dict[str, Any]], None]
) -> None:
    """Subscribe to real-time quotes."""

def subscribe_level_one_equity(
    self,
    symbols: List[str],
    fields: Optional[List[str]] = None
) -> None:
    """Subscribe to level 1 equity data."""

def subscribe_level_one_option(
    self,
    symbols: List[str],
    fields: Optional[List[str]] = None
) -> None:
    """Subscribe to level 1 option data."""

def unsubscribe(self, service: str, symbols: List[str]) -> None:
    """Unsubscribe from a service."""

def set_quality_of_service(self, qos: str) -> None:
    """Set quality of service level."""

def start(self) -> None:
    """Start the streaming connection."""

def stop(self) -> None:
    """Stop the streaming connection."""
```

### StreamerClient

Alternative streaming client with automatic reconnection.

```python
from schwab.streaming import StreamerClient

async with StreamerClient(
    auth: SchwabAuth,
    account_number: str,
    on_message: Callable[[Dict[str, Any]], None],
    on_error: Optional[Callable[[Exception], None]] = None,
    on_close: Optional[Callable[[], None]] = None
) as client:
    await client.subscribe_quotes(["AAPL", "MSFT"])
```

## Order Monitoring

### OrderMonitor

Real-time order status and execution monitoring.

```python
from schwab.order_monitor import OrderMonitor

monitor = OrderMonitor(
    client: Union[SchwabClient, AsyncSchwabClient]
)
```

#### Methods

```python
def start_monitoring(
    self,
    account_number: str,
    order_ids: List[int],
    on_status_change: Optional[Callable[[Order, str, str], None]] = None,
    on_execution: Optional[Callable[[Order, OrderActivity], None]] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
    interval: float = 1.0
) -> None:
    """Start monitoring specified orders."""

def stop_monitoring(self) -> None:
    """Stop all monitoring threads."""

def is_monitoring(self) -> bool:
    """Check if monitor is currently active."""

def get_monitored_orders(self) -> List[int]:
    """Get list of currently monitored order IDs."""
```

## Paper Trading

### Paper Trading Components

#### PaperTradingIndicator
```python
from schwab.paper_trading import PaperTradingIndicator

class PaperTradingIndicator:
    """Visual indicator for paper trading mode."""
    
    @staticmethod
    def show() -> None:
        """Display paper trading indicator."""
    
    @staticmethod
    def format_message(message: str) -> str:
        """Format message with paper trading prefix."""
```

#### PaperAccountManager
```python
from schwab.paper_trading import PaperAccountManager

manager = PaperAccountManager(client)

def is_paper_account(self, account_number: str) -> bool:
    """Check if account is a paper trading account."""

def detect_account_type(self, account_number: str) -> str:
    """Detect account type (paper or real)."""
```

#### Paper Trading Decorators
```python
@paper_trading_check
def place_order(self, account_number: str, order: Order) -> Dict[str, Any]:
    """Decorator ensures paper trading validation."""
```

### Technical Indicators

```python
from schwab.paper_trading.indicators import RSI, MovingAverage, MACD, BollingerBands

# RSI
rsi = RSI(period=14)
rsi_values = rsi.calculate(price_data)

# Moving Average
ma = MovingAverage(period=20, ma_type="EMA")  # SMA, EMA, WMA
ma_values = ma.calculate(price_data)

# MACD
macd = MACD(fast_period=12, slow_period=26, signal_period=9)
macd_line, signal_line, histogram = macd.calculate(price_data)

# Bollinger Bands
bb = BollingerBands(period=20, std_dev=2)
upper_band, middle_band, lower_band = bb.calculate(price_data)
```

## Error Handling

### Exception Classes

```python
# Authentication errors
class AuthenticationError(Exception):
    """Raised when authentication fails."""

class TokenExpiredError(AuthenticationError):
    """Raised when access token is expired."""

# Order validation errors
class OrderValidationError(Exception):
    """Raised when order validation fails."""
    
    def __init__(self, message: str, validation_errors: Optional[Dict] = None):
        self.validation_errors = validation_errors

# API errors
class SchwabAPIError(Exception):
    """Base class for API errors."""
    
    def __init__(self, status_code: int, message: str, response: Optional[Dict] = None):
        self.status_code = status_code
        self.response = response

class RateLimitError(SchwabAPIError):
    """Raised when rate limit is exceeded."""

class InsufficientFundsError(SchwabAPIError):
    """Raised when account has insufficient funds."""
```

### Error Handling Patterns

```python
from schwab.models.order_validation import OrderValidationError
from schwab.auth import AuthenticationError, TokenExpiredError
import requests

try:
    # Place order
    order = client.create_market_order(
        symbol="AAPL",
        quantity=100,
        instruction="BUY"
    )
    result = client.place_order(account_number, order)
    
except OrderValidationError as e:
    print(f"Order validation failed: {str(e)}")
    if e.validation_errors:
        for field, error in e.validation_errors.items():
            print(f"  {field}: {error}")
            
except TokenExpiredError:
    # Token expired, refresh and retry
    client.auth.refresh_access_token()
    # Retry operation
    
except AuthenticationError as e:
    print(f"Authentication failed: {str(e)}")
    # Re-authenticate user
    
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 429:
        print("Rate limit exceeded, please wait")
    elif e.response.status_code == 400:
        print(f"Bad request: {e.response.text}")
    else:
        print(f"HTTP Error: {e.response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"Network error: {str(e)}")
    
except Exception as e:
    print(f"Unexpected error: {str(e)}")
```

## Best Practices

### 1. Authentication Management
```python
# Save tokens for persistence
auth.save_tokens("tokens.json")

# Load tokens on startup
auth = SchwabAuth(client_id, client_secret, redirect_uri)
auth.load_tokens("tokens.json")

# Tokens are automatically refreshed
client = SchwabClient(auth=auth)
```

### 2. Async Context Management
```python
async def main():
    async with AsyncSchwabClient(auth=auth) as client:
        # All operations within context
        accounts = await client.get_accounts()
        # Connection automatically closed
```

### 3. Order Validation
```python
# Always validate orders before placing
order = client.create_limit_order(
    symbol="AAPL",
    quantity=100,
    limit_price=150.00,
    instruction="BUY"
)

# Client validates automatically, but you can add checks
if order.quantity <= 0:
    raise ValueError("Invalid quantity")
```

### 4. Error Recovery
```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def place_order_with_retry(client, account_number, order):
    try:
        return await client.place_order(account_number, order)
    except RateLimitError:
        await asyncio.sleep(60)  # Wait 1 minute
        raise
```

### 5. Portfolio Monitoring
```python
# Set up comprehensive monitoring
portfolio = PortfolioManager(client)
portfolio.add_account("account1")
portfolio.add_account("account2")

# Monitor with callbacks
def on_portfolio_event(event_type, data):
    if event_type == "order_filled":
        print(f"Order filled: {data}")
    elif event_type == "position_changed":
        print(f"Position update: {data}")

portfolio.monitor_orders(callback=on_portfolio_event)

# Save state periodically
import schedule

schedule.every(5).minutes.do(
    lambda: portfolio.save_state("portfolio_backup.json")
)
```

## Additional Resources

- [Schwab API Documentation](https://developer.schwab.com)
- [OAuth 2.0 Documentation](https://oauth.net/2/)
- [Example Scripts](../examples/)
- [API Guide](API.md)
- [Order Types Tutorial](ORDER_TYPES_TUTORIAL.md)
- [Paper Trading Guide](PAPER_TRADING.md)