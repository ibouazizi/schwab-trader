# Schwab API Python Library Reference

## Table of Contents
1. [Client Classes](#client-classes)
   - [SchwabClient](#schwabclient)
   - [AsyncSchwabClient](#asyncschwabclient)
2. [Authentication](#authentication)
   - [SchwabAuth](#schwabauth)
3. [Account Management](#account-management)
   - [Account Models](#account-models)
   - [Account Methods](#account-methods)
4. [Order Management](#order-management)
   - [Order Models](#order-models)
   - [Order Methods](#order-methods)
5. [Market Data](#market-data)
   - [Quote Models](#quote-models)
   - [Quote Methods](#quote-methods)
6. [Error Handling](#error-handling)
   - [Exception Classes](#exception-classes)
   - [Error Handling Patterns](#error-handling-patterns)

## Client Classes

### SchwabClient

The main client class for synchronous API operations.

```python
from schwab import SchwabClient

client = SchwabClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    redirect_uri="your_redirect_uri"
)
```

#### Constructor Parameters
- `client_id` (str): OAuth client ID from Schwab
- `client_secret` (str): OAuth client secret from Schwab
- `redirect_uri` (str): OAuth callback URL
- `auth` (Optional[SchwabAuth]): Pre-configured auth instance

#### Methods

##### Account Management
```python
def get_account_numbers(self) -> List[Account]:
    """Get all account numbers associated with the authenticated user."""

def get_account(self, account_number: str, include_positions: bool = False) -> AccountDetails:
    """Get detailed account information."""

def get_account_positions(self, account_number: str) -> List[Position]:
    """Get all positions for an account."""
```

##### Order Management
```python
def create_market_order(
    self,
    symbol: str,
    quantity: int,
    instruction: OrderInstruction,
    description: str = None
) -> Order:
    """Create a market order."""

def create_limit_order(
    self,
    symbol: str,
    quantity: int,
    limit_price: float,
    instruction: OrderInstruction,
    description: str = None
) -> Order:
    """Create a limit order."""

def create_stop_order(
    self,
    symbol: str,
    quantity: int,
    stop_price: float,
    instruction: OrderInstruction,
    description: str = None
) -> Order:
    """Create a stop order."""

def create_stop_limit_order(
    self,
    symbol: str,
    quantity: int,
    stop_price: float,
    limit_price: float,
    instruction: OrderInstruction,
    description: str = None
) -> Order:
    """Create a stop-limit order."""

def place_order(self, account_number: str, order: Order) -> OrderResponse:
    """Place an order for the specified account."""

def get_order(self, account_number: str, order_id: int) -> Order:
    """Get order details by ID."""

def get_orders(
    self,
    account_number: str,
    from_entered_time: datetime = None,
    to_entered_time: datetime = None,
    status: str = None
) -> List[Order]:
    """Get orders matching the specified criteria."""

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

def cancel_order(self, account_number: str, order_id: int) -> None:
    """Cancel an existing order."""
```

##### Market Data
```python
def get_quotes(self, symbols: List[str]) -> QuoteResponse:
    """Get real-time quotes for specified symbols."""

def get_quote_history(
    self,
    symbol: str,
    interval: str,
    start_time: datetime,
    end_time: datetime
) -> List[HistoricalQuote]:
    """Get historical quote data."""
```

### AsyncSchwabClient

Asynchronous version of the client for non-blocking operations.

```python
from schwab import AsyncSchwabClient

async with AsyncSchwabClient(api_key="your_api_key") as client:
    # Perform async operations
    accounts = await client.get_account_numbers()
```

All methods from SchwabClient are available with async/await syntax.

## Authentication

### SchwabAuth

Handles OAuth 2.0 authentication flow.

```python
from schwab import SchwabAuth

auth = SchwabAuth(
    client_id="your_client_id",
    client_secret="your_client_secret",
    redirect_uri="your_redirect_uri"
)
```

#### Methods
```python
def get_authorization_url(self) -> str:
    """Get the URL for the authorization step."""

def exchange_code_for_tokens(self, authorization_code: str) -> Dict:
    """Exchange authorization code for access and refresh tokens."""

def refresh_access_token(self) -> Dict:
    """Refresh the access token using the refresh token."""

def ensure_valid_token(self) -> None:
    """Ensure we have a valid access token, refreshing if necessary."""
```

## Account Management

### Account Models

#### Account
```python
class Account(BaseModel):
    account_id: str
    account_type: str
    encrypted_account_number: str
```

#### AccountDetails
```python
class AccountDetails(Account):
    cash_balance: Decimal
    buying_power: Decimal
    total_value: Decimal
    positions: List[Position]
```

#### Position
```python
class Position(BaseModel):
    symbol: str
    quantity: Decimal
    asset_type: str
    average_price: Decimal
    current_price: Decimal
    market_value: Decimal
    cost_basis: Decimal
```

## Order Management

### Order Models

#### OrderInstruction
```python
class OrderInstruction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    BUY_TO_COVER = "BUY_TO_COVER"
    SELL_SHORT = "SELL_SHORT"
```

#### OrderType
```python
class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"
    MARKET_ON_CLOSE = "MARKET_ON_CLOSE"
    LIMIT_ON_CLOSE = "LIMIT_ON_CLOSE"
```

#### OrderStatus
```python
class OrderStatus(str, Enum):
    WORKING = "WORKING"
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    FILLED = "FILLED"
    EXPIRED = "EXPIRED"
    REPLACED = "REPLACED"
```

#### Order
```python
class Order(BaseModel):
    order_id: Optional[int]
    symbol: str
    quantity: int
    order_type: OrderType
    instruction: OrderInstruction
    status: Optional[OrderStatus]
    price: Optional[float]
    stop_price: Optional[float]
    entered_time: Optional[datetime]
    description: Optional[str]
```

## Market Data

### Quote Models

#### QuoteData
```python
class QuoteData(BaseModel):
    symbol: str
    lastPrice: Optional[float]
    bidPrice: Optional[float]
    askPrice: Optional[float]
    bidSize: Optional[int]
    askSize: Optional[int]
    totalVolume: Optional[int]
    lastSize: Optional[int]
    tradeTime: Optional[datetime]
    quoteTime: Optional[datetime]
    closePrice: Optional[float]
```

#### QuoteResponse
```python
class QuoteResponse(BaseModel):
    root: Dict[str, QuoteData]
```

## Error Handling

### Exception Classes

#### OrderValidationError
```python
class OrderValidationError(Exception):
    """Raised when order validation fails."""
```

#### AuthenticationError
```python
class AuthenticationError(Exception):
    """Raised when authentication fails."""
```

### Error Handling Patterns

```python
from schwab.models.order_validation import OrderValidationError

try:
    order = client.create_market_order(
        symbol="AAPL",
        quantity=100,
        instruction=OrderInstruction.BUY
    )
    response = client.place_order(account_number, order)
except OrderValidationError as e:
    print(f"Order validation failed: {str(e)}")
except AuthenticationError as e:
    print(f"Authentication failed: {str(e)}")
except Exception as e:
    print(f"An error occurred: {str(e)}")
```

## Rate Limiting

The library implements smart rate limiting to comply with Schwab's API restrictions:

- Maximum requests per minute: 3000
- Minimum request interval: 20ms
- Automatic retry with exponential backoff
- Request tracking with rolling window

```python
# Rate limiting is handled automatically by the client
# but can be configured if needed
client = SchwabClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    redirect_uri="your_redirect_uri",
    max_retries=3,
    retry_delay=0.1
)
```

## Best Practices

1. Always use the context manager with AsyncSchwabClient:
```python
async with AsyncSchwabClient(api_key=token) as client:
    # Your async code here
```

2. Handle token refresh automatically:
```python
auth = SchwabAuth(client_id, client_secret, redirect_uri)
auth.ensure_valid_token()  # Called automatically by the client
```

3. Use appropriate error handling:
```python
try:
    result = await client.get_quotes(symbols)
except Exception as e:
    logger.error(f"Error fetching quotes: {e}")
    # Implement appropriate error handling
```

4. Implement proper rate limiting in your application:
```python
# The library handles basic rate limiting, but for intensive operations:
await asyncio.sleep(1)  # Add appropriate delays
```

## Usage Examples

### 1. Portfolio Management System
```python
from schwab import SchwabClient
from schwab.models.orders import OrderInstruction, OrderType
from decimal import Decimal
from datetime import datetime, timedelta
import pandas as pd

class PortfolioManager:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client = SchwabClient(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri
        )
        
    def get_portfolio_summary(self, account_number: str) -> dict:
        """Get a comprehensive portfolio summary."""
        # Get account details with positions
        account = self.client.get_account(
            account_number=account_number,
            include_positions=True
        )
        
        # Calculate portfolio metrics
        total_equity = sum(
            position.market_value
            for position in account.positions
            if position.asset_type == "EQUITY"
        )
        
        # Calculate total P&L
        total_pnl = sum(
            position.market_value - position.cost_basis
            for position in account.positions
        )
        
        # Calculate position-level metrics
        positions = []
        for pos in account.positions:
            pnl = pos.market_value - pos.cost_basis
            pnl_pct = (pnl / pos.cost_basis * 100) if pos.cost_basis != 0 else Decimal('0')
            
            positions.append({
                'symbol': pos.symbol,
                'quantity': pos.quantity,
                'avg_price': pos.average_price,
                'current_price': pos.current_price,
                'market_value': pos.market_value,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })
        
        return {
            'account_value': account.total_value,
            'cash_balance': account.cash_balance,
            'buying_power': account.buying_power,
            'total_equity': total_equity,
            'total_pnl': total_pnl,
            'positions': positions
        }
    
    def rebalance_portfolio(self, account_number: str, target_allocations: dict):
        """Rebalance portfolio according to target allocations."""
        # Get current positions
        account = self.client.get_account(account_number, include_positions=True)
        
        # Calculate current allocations
        total_value = account.total_value
        current_allocations = {
            pos.symbol: (pos.market_value / total_value * 100)
            for pos in account.positions
        }
        
        # Calculate required trades
        trades = []
        for symbol, target_pct in target_allocations.items():
            current_pct = current_allocations.get(symbol, Decimal('0'))
            if abs(current_pct - target_pct) > Decimal('1.0'):  # 1% threshold
                # Get current quote
                quote = self.client.get_quotes([symbol])[symbol]
                
                # Calculate required position size
                target_value = total_value * (target_pct / 100)
                current_value = total_value * (current_pct / 100)
                value_difference = target_value - current_value
                
                # Calculate shares to trade
                shares = abs(int(value_difference / quote.lastPrice))
                if shares > 0:
                    instruction = (
                        OrderInstruction.BUY 
                        if value_difference > 0 
                        else OrderInstruction.SELL
                    )
                    trades.append((symbol, shares, instruction))
        
        # Execute trades
        for symbol, shares, instruction in trades:
            order = self.client.create_market_order(
                symbol=symbol,
                quantity=shares,
                instruction=instruction
            )
            self.client.place_order(account_number, order)
```

### 2. Real-time Trading Monitor
```python
import asyncio
from schwab import AsyncSchwabClient
from schwab.models.orders import OrderStatus
from datetime import datetime, timedelta

class TradingMonitor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.running = True
        self.positions = {}
        self.orders = {}
        
    async def monitor_positions(self, account_number: str):
        """Monitor positions and P&L in real-time."""
        async with AsyncSchwabClient(api_key=self.api_key) as client:
            while self.running:
                try:
                    # Get current positions
                    account = await client.get_account(
                        account_number=account_number,
                        include_positions=True
                    )
                    
                    # Update position tracking
                    for position in account.positions:
                        if position.symbol not in self.positions:
                            print(f"New position: {position.symbol}")
                        
                        prev_value = self.positions.get(
                            position.symbol, 
                            {'market_value': 0}
                        )['market_value']
                        
                        value_change = position.market_value - prev_value
                        if abs(value_change) > 0:
                            print(
                                f"{position.symbol} value changed by "
                                f"${value_change:,.2f}"
                            )
                        
                        self.positions[position.symbol] = {
                            'quantity': position.quantity,
                            'market_value': position.market_value,
                            'current_price': position.current_price
                        }
                    
                    await asyncio.sleep(5)  # Update every 5 seconds
                    
                except Exception as e:
                    print(f"Error monitoring positions: {e}")
                    await asyncio.sleep(5)
    
    async def monitor_orders(self, account_number: str):
        """Monitor order status changes."""
        async with AsyncSchwabClient(api_key=self.api_key) as client:
            while self.running:
                try:
                    # Get recent orders
                    orders = await client.get_orders(
                        account_number=account_number,
                        from_entered_time=datetime.now() - timedelta(days=1),
                        status="WORKING"
                    )
                    
                    # Check for status changes
                    for order in orders:
                        prev_status = self.orders.get(
                            order.order_id, 
                            {'status': None}
                        )['status']
                        
                        if order.status != prev_status:
                            print(
                                f"Order {order.order_id} status changed: "
                                f"{prev_status} -> {order.status}"
                            )
                            
                            if order.status == OrderStatus.FILLED:
                                print(
                                    f"Order filled: {order.symbol} "
                                    f"{order.instruction} {order.quantity} "
                                    f"@ {order.price}"
                                )
                        
                        self.orders[order.order_id] = {
                            'status': order.status,
                            'symbol': order.symbol,
                            'quantity': order.quantity,
                            'price': order.price
                        }
                    
                    await asyncio.sleep(2)  # Check every 2 seconds
                    
                except Exception as e:
                    print(f"Error monitoring orders: {e}")
                    await asyncio.sleep(2)
    
    async def run(self, account_number: str):
        """Run all monitoring tasks."""
        tasks = [
            self.monitor_positions(account_number),
            self.monitor_orders(account_number)
        ]
        await asyncio.gather(*tasks)
    
    def stop(self):
        """Stop all monitoring tasks."""
        self.running = False
```

### 3. Automated Trading Strategy
```python
from schwab import SchwabClient
from schwab.models.orders import OrderInstruction, OrderType
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class MovingAverageCrossStrategy:
    def __init__(
        self, 
        client_id: str, 
        client_secret: str, 
        redirect_uri: str,
        symbols: list,
        fast_ma: int = 20,
        slow_ma: int = 50
    ):
        self.client = SchwabClient(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri
        )
        self.symbols = symbols
        self.fast_ma = fast_ma
        self.slow_ma = slow_ma
        self.positions = {}
        
    def calculate_signals(self, symbol: str) -> dict:
        """Calculate trading signals based on moving average crossover."""
        # Get historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=100)
        
        quotes = self.client.get_quote_history(
            symbol=symbol,
            interval='1day',
            start_time=start_date,
            end_time=end_date
        )
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'date': q.date,
                'close': q.close,
                'volume': q.volume
            }
            for q in quotes
        ])
        
        # Calculate moving averages
        df['fast_ma'] = df['close'].rolling(window=self.fast_ma).mean()
        df['slow_ma'] = df['close'].rolling(window=self.slow_ma).mean()
        
        # Calculate crossover signals
        df['signal'] = np.where(
            df['fast_ma'] > df['slow_ma'],
            1,  # Buy signal
            -1  # Sell signal
        )
        
        # Get current signal
        current_signal = df['signal'].iloc[-1]
        prev_signal = df['signal'].iloc[-2]
        
        return {
            'symbol': symbol,
            'current_price': df['close'].iloc[-1],
            'signal_changed': current_signal != prev_signal,
            'signal': current_signal,
            'fast_ma': df['fast_ma'].iloc[-1],
            'slow_ma': df['slow_ma'].iloc[-1]
        }
    
    def execute_trades(self, account_number: str, max_position_size: float = 10000):
        """Execute trades based on signals."""
        for symbol in self.symbols:
            try:
                # Calculate signals
                signal_data = self.calculate_signals(symbol)
                
                if signal_data['signal_changed']:
                    # Get current position
                    current_position = 0
                    account = self.client.get_account(
                        account_number, 
                        include_positions=True
                    )
                    for position in account.positions:
                        if position.symbol == symbol:
                            current_position = position.quantity
                    
                    # Calculate trade size
                    price = signal_data['current_price']
                    shares = int(max_position_size / price)
                    
                    if signal_data['signal'] == 1 and current_position <= 0:
                        # Buy signal
                        order = self.client.create_market_order(
                            symbol=symbol,
                            quantity=shares,
                            instruction=OrderInstruction.BUY
                        )
                        self.client.place_order(account_number, order)
                        print(f"Placed buy order for {shares} shares of {symbol}")
                        
                    elif signal_data['signal'] == -1 and current_position > 0:
                        # Sell signal
                        order = self.client.create_market_order(
                            symbol=symbol,
                            quantity=current_position,
                            instruction=OrderInstruction.SELL
                        )
                        self.client.place_order(account_number, order)
                        print(f"Placed sell order for {current_position} shares of {symbol}")
                
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
```

### 4. Risk Management System
```python
from schwab import SchwabClient
from schwab.models.orders import OrderInstruction
from decimal import Decimal
import numpy as np

class RiskManager:
    def __init__(
        self, 
        client_id: str, 
        client_secret: str, 
        redirect_uri: str,
        max_position_pct: float = 0.05,
        max_loss_pct: float = 0.02
    ):
        self.client = SchwabClient(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri
        )
        self.max_position_pct = max_position_pct
        self.max_loss_pct = max_loss_pct
    
    def check_position_limits(self, account_number: str) -> list:
        """Check for positions exceeding size limits."""
        violations = []
        account = self.client.get_account(account_number, include_positions=True)
        
        for position in account.positions:
            position_pct = position.market_value / account.total_value
            if position_pct > self.max_position_pct:
                violations.append({
                    'symbol': position.symbol,
                    'current_pct': position_pct,
                    'max_pct': self.max_position_pct,
                    'excess_value': position.market_value - (
                        account.total_value * self.max_position_pct
                    )
                })
        
        return violations
    
    def place_stop_loss_orders(self, account_number: str):
        """Place stop-loss orders for positions."""
        account = self.client.get_account(account_number, include_positions=True)
        
        for position in account.positions:
            # Calculate stop price
            stop_price = position.average_price * (1 - self.max_loss_pct)
            
            # Create stop order
            order = self.client.create_stop_order(
                symbol=position.symbol,
                quantity=position.quantity,
                stop_price=stop_price,
                instruction=OrderInstruction.SELL
            )
            
            # Place the order
            self.client.place_order(account_number, order)
            print(
                f"Placed stop-loss order for {position.symbol} "
                f"at ${stop_price:.2f}"
            )
    
    def calculate_portfolio_risk(self, account_number: str) -> dict:
        """Calculate portfolio risk metrics."""
        account = self.client.get_account(account_number, include_positions=True)
        
        # Calculate position values and weights
        total_value = account.total_value
        position_weights = [
            position.market_value / total_value
            for position in account.positions
        ]
        
        # Calculate position correlations and volatility
        returns_data = []
        for position in account.positions:
            quotes = self.client.get_quote_history(
                symbol=position.symbol,
                interval='1day',
                start_time=datetime.now() - timedelta(days=252),
                end_time=datetime.now()
            )
            
            prices = [q.close for q in quotes]
            returns = np.diff(np.log(prices))
            returns_data.append(returns)
        
        # Calculate portfolio metrics
        if returns_data:
            returns_matrix = np.array(returns_data)
            correlation_matrix = np.corrcoef(returns_matrix)
            volatilities = np.std(returns_matrix, axis=1) * np.sqrt(252)
            
            # Portfolio volatility
            portfolio_vol = np.sqrt(
                np.dot(
                    np.dot(
                        np.array(position_weights),
                        correlation_matrix * np.outer(volatilities, volatilities)
                    ),
                    np.array(position_weights)
                )
            )
            
            # Value at Risk (95% confidence)
            var_95 = portfolio_vol * 1.645 * total_value
            
            return {
                'portfolio_volatility': portfolio_vol,
                'value_at_risk_95': var_95,
                'position_volatilities': dict(
                    zip(
                        [p.symbol for p in account.positions],
                        volatilities
                    )
                ),
                'correlation_matrix': correlation_matrix.tolist()
            }
        
        return None
```

## Additional Resources

- [Schwab API Documentation](https://www.schwab.com/public/schwab/nn/api/documentation)
- [OAuth 2.0 Documentation](https://oauth.net/2/)
- [Example Scripts](../examples/)