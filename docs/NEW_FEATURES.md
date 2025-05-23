# New Features in Schwab Trader

This document highlights the major features and capabilities of the Schwab Trader library, including recent additions and enhancements.

## Table of Contents
1. [Portfolio Management](#portfolio-management)
2. [Paper Trading](#paper-trading)
3. [Streaming Market Data](#streaming-market-data)
4. [Order Management](#order-management)
5. [Async Support](#async-support)
6. [Technical Indicators](#technical-indicators)
7. [Advanced Order Types](#advanced-order-types)
8. [Error Handling](#error-handling)

## Portfolio Management

The library includes a comprehensive `PortfolioManager` class for managing multiple accounts and tracking performance.

### Key Features
- Multi-account aggregation
- Real-time position tracking
- P&L calculations
- Order monitoring
- State persistence

### Example Usage
```python
from schwab.portfolio import PortfolioManager

# Initialize portfolio manager
portfolio = PortfolioManager(client)

# Add multiple accounts
portfolio.add_account("account1")
portfolio.add_account("account2")

# Get aggregated summary
summary = portfolio.get_portfolio_summary()
print(f"Total Value: ${summary['total_value']:,.2f}")
print(f"Total P&L: ${summary['total_pnl']:,.2f}")
print(f"Total P&L %: {summary['total_pnl_percentage']:.2f}%")

# Get position across all accounts
aapl_position = portfolio.get_position("AAPL")
if aapl_position:
    print(f"Total AAPL shares: {aapl_position['total_quantity']}")
    print(f"Average cost: ${aapl_position['average_cost']:.2f}")
    print(f"Current value: ${aapl_position['total_value']:.2f}")

# Monitor portfolio events
def on_portfolio_event(event_type, data):
    if event_type == "order_filled":
        print(f"Order filled: {data['symbol']} {data['quantity']} @ ${data['price']}")
    elif event_type == "position_changed":
        print(f"Position updated: {data['symbol']} new quantity: {data['quantity']}")

portfolio.monitor_orders(callback=on_portfolio_event)

# Save portfolio state
portfolio.save_state("portfolio_backup.json")

# Load portfolio state
portfolio.load_state("portfolio_backup.json")
```

## Paper Trading

Built-in paper trading support with visual indicators and safety features.

### Key Features
- Automatic paper account detection
- Visual indicators for paper trading mode
- Safety checks to prevent accidental real trades
- Support for both sync and async clients

### Example Usage
```python
from schwab.paper_trading import PaperTradingClient, AsyncPaperTradingClient

# Initialize paper trading client
paper_client = PaperTradingClient(auth=auth)

# All operations show paper trading indicators
order = paper_client.create_market_order(
    symbol="AAPL",
    quantity=100,
    instruction="BUY"
)

# Visual indicator in output
result = paper_client.place_order(paper_account_number, order)
# Output: [PAPER TRADING] Order placed successfully for 100 shares of AAPL

# Account type detection
from schwab.paper_trading.account import PaperAccountManager

manager = PaperAccountManager(client)
if manager.is_paper_account(account_number):
    print("This is a paper trading account")

# Async paper trading
async with AsyncPaperTradingClient(auth=auth) as client:
    await client.place_order(paper_account_number, order)
```

### Technical Indicators for Paper Trading

```python
from schwab.paper_trading.indicators import RSI, MovingAverage, MACD, BollingerBands

# Calculate RSI
rsi = RSI(period=14)
rsi_values = rsi.calculate(price_data)

# Moving Averages
ma = MovingAverage(period=20, ma_type="EMA")  # SMA, EMA, WMA
ma_values = ma.calculate(price_data)

# MACD
macd = MACD(fast_period=12, slow_period=26, signal_period=9)
macd_line, signal_line, histogram = macd.calculate(price_data)

# Bollinger Bands
bb = BollingerBands(period=20, std_dev=2)
upper_band, middle_band, lower_band = bb.calculate(price_data)
```

## Streaming Market Data

Real-time WebSocket streaming for market data and quotes.

### Key Features
- WebSocket connection management
- Real-time quote streaming
- Level 1 equity and options data
- Automatic reconnection
- Quality of Service options

### Example Usage
```python
from schwab.streaming import SchwabStreamer, StreamerClient

# Basic streaming
streamer = SchwabStreamer(client)

def on_quote_update(data):
    print(f"Quote: {data['symbol']} - ${data['lastPrice']}")

# Subscribe to quotes
streamer.subscribe_quotes(
    symbols=["AAPL", "MSFT", "GOOGL"],
    callback=on_quote_update
)

# Start streaming
streamer.start()

# Advanced streaming with auto-reconnect
async with StreamerClient(
    auth=auth,
    account_number=account_number,
    on_message=on_quote_update,
    on_error=lambda e: print(f"Error: {e}"),
    on_close=lambda: print("Connection closed")
) as client:
    # Subscribe to level 1 data
    await client.subscribe_level_one_equity(
        symbols=["AAPL", "MSFT"],
        fields=["BID_PRICE", "ASK_PRICE", "LAST_PRICE", "TOTAL_VOLUME"]
    )
    
    # Set quality of service
    await client.set_quality_of_service("EXPRESS")  # REAL_TIME, FAST, MODERATE, EXPRESS
```

## Order Management

Enhanced order management with validation, modification, and monitoring capabilities.

### Order Creation Helpers
```python
# Market order
order = client.create_market_order(
    symbol="AAPL",
    quantity=100,
    instruction="BUY"
)

# Limit order
order = client.create_limit_order(
    symbol="MSFT",
    quantity=50,
    limit_price=350.00,
    instruction="SELL",
    duration="GOOD_TILL_CANCEL"
)

# Stop-limit order
order = client.create_stop_limit_order(
    symbol="TSLA",
    quantity=25,
    stop_price=800.00,
    limit_price=795.00,
    instruction="SELL"
)

# Trailing stop order
order = client.create_trailing_stop_order(
    symbol="NVDA",
    quantity=10,
    stop_price_offset=5.00,  # $5 trailing stop
    instruction="SELL"
)

# Market on close
order = client.create_market_on_close_order(
    symbol="SPY",
    quantity=100,
    instruction="BUY"
)
```

### Order Monitoring
```python
from schwab.order_monitor import OrderMonitor

monitor = OrderMonitor(client)

def on_status_change(order, old_status, new_status):
    print(f"Order {order.orderId}: {old_status} -> {new_status}")
    
    if new_status == "FILLED":
        print(f"Order filled! {order.filledQuantity} shares @ ${order.price}")

def on_execution(order, activity):
    for leg in activity.executionLegs:
        print(f"Executed: {leg.quantity} @ ${leg.price} on {leg.time}")

# Start monitoring
monitor.start_monitoring(
    account_number=account_number,
    order_ids=[12345, 12346, 12347],
    on_status_change=on_status_change,
    on_execution=on_execution,
    interval=1.0  # Check every second
)

# Stop monitoring
monitor.stop_monitoring()
```

### Order Modification
```python
# Modify order price
modified = client.modify_order_price(
    account_number=account_number,
    order_id=12345,
    new_price=155.00
)

# Modify order quantity
modified = client.modify_order_quantity(
    account_number=account_number,
    order_id=12345,
    new_quantity=200
)

# Batch operations
results = client.batch_cancel_orders(
    account_number=account_number,
    order_ids=[12345, 12346, 12347]
)

modifications = [
    {"order_id": 12345, "price": 155.00},
    {"order_id": 12346, "quantity": 200},
    {"order_id": 12347, "price": 160.00, "quantity": 150}
]

results = client.batch_modify_orders(
    account_number=account_number,
    modifications=modifications
)
```

## Async Support

Full asynchronous support for non-blocking operations.

### Key Features
- Async versions of all client methods
- Context manager support
- Concurrent operations
- Proper session management

### Example Usage
```python
import asyncio
from schwab import AsyncSchwabClient

async def main():
    async with AsyncSchwabClient(auth=auth) as client:
        # Concurrent operations
        accounts, quotes, orders = await asyncio.gather(
            client.get_accounts(include_positions=True),
            client.get_quotes(["AAPL", "MSFT", "GOOGL"]),
            client.get_orders(
                account_number=account_number,
                from_date=datetime.now() - timedelta(days=7)
            )
        )
        
        # Process results
        print(f"Found {len(accounts)} accounts")
        print(f"AAPL price: ${quotes['AAPL'].quote.lastPrice}")
        print(f"Active orders: {len([o for o in orders if o.status == 'WORKING'])}")
        
        # Place order asynchronously
        order = client.create_limit_order(
            symbol="AAPL",
            quantity=100,
            limit_price=150.00,
            instruction="BUY"
        )
        
        result = await client.place_order(
            accounts[0].securitiesAccount.accountNumber,
            order
        )

asyncio.run(main())
```

### Async Portfolio Management
```python
from schwab.portfolio import PortfolioManager

async def monitor_portfolio():
    async with AsyncSchwabClient(auth=auth) as client:
        portfolio = PortfolioManager(client)
        portfolio.add_account("account1")
        portfolio.add_account("account2")
        
        # Async refresh
        await portfolio.async_refresh_positions()
        
        # Get summary
        summary = portfolio.get_portfolio_summary()
        print(f"Portfolio value: ${summary['total_value']:,.2f}")
```

## Technical Indicators

Built-in technical indicators for trading strategies.

### Available Indicators
- **RSI** - Relative Strength Index
- **Moving Averages** - SMA, EMA, WMA
- **MACD** - Moving Average Convergence Divergence
- **Bollinger Bands** - With customizable standard deviations

### Example Strategy
```python
from schwab.paper_trading.indicators import RSI, MovingAverage

# Get price history
history = client.get_price_history(
    symbol="AAPL",
    period_type="day",
    period=30,
    frequency_type="minute",
    frequency=30
)

prices = [candle.close for candle in history.candles]

# Calculate indicators
rsi = RSI(period=14)
rsi_values = rsi.calculate(prices)

ma_fast = MovingAverage(period=10, ma_type="EMA")
ma_slow = MovingAverage(period=20, ma_type="EMA")

fast_ma = ma_fast.calculate(prices)
slow_ma = ma_slow.calculate(prices)

# Trading signals
if rsi_values[-1] < 30 and fast_ma[-1] > slow_ma[-1]:
    print("Bullish signal: RSI oversold with positive MA crossover")
```

## Advanced Order Types

Support for complex order strategies and multi-leg orders.

### Options Strategies
```python
# Vertical spread
order = Order(
    orderType="NET_DEBIT",
    session="NORMAL",
    price=2.50,
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="VERTICAL",
    orderLegCollection=[
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="AAPL_012025C150",
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="AAPL_012025C160",
                assetType="OPTION"
            )
        )
    ]
)

# Iron condor
order = Order(
    orderType="NET_CREDIT",
    session="NORMAL",
    price=3.00,
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="IRON_CONDOR",
    orderLegCollection=[
        # Put spread
        OrderLeg(instruction="SELL_TO_OPEN", quantity=1,
                instrument=Instrument(symbol="SPY_012025P440", assetType="OPTION")),
        OrderLeg(instruction="BUY_TO_OPEN", quantity=1,
                instrument=Instrument(symbol="SPY_012025P430", assetType="OPTION")),
        # Call spread
        OrderLeg(instruction="SELL_TO_OPEN", quantity=1,
                instrument=Instrument(symbol="SPY_012025C460", assetType="OPTION")),
        OrderLeg(instruction="BUY_TO_OPEN", quantity=1,
                instrument=Instrument(symbol="SPY_012025C470", assetType="OPTION"))
    ]
)
```

### Conditional Orders
```python
# One-Cancels-Other (OCO)
order = Order(
    orderType="LIMIT",
    session="NORMAL",
    price=155.00,
    duration="GOOD_TILL_CANCEL",
    orderStrategyType="OCO",
    childOrderStrategies=[
        Order(
            orderType="STOP",
            session="NORMAL",
            stopPrice=145.00,
            duration="GOOD_TILL_CANCEL",
            orderLegCollection=[
                OrderLeg(
                    instruction="SELL",
                    quantity=100,
                    instrument=Instrument(symbol="AAPL", assetType="EQUITY")
                )
            ]
        )
    ],
    orderLegCollection=[
        OrderLeg(
            instruction="SELL",
            quantity=100,
            instrument=Instrument(symbol="AAPL", assetType="EQUITY")
        )
    ]
)
```

## Error Handling

Comprehensive error handling with specific exception types.

### Exception Types
```python
from schwab.auth import AuthenticationError, TokenExpiredError
from schwab.models.order_validation import OrderValidationError

# Authentication errors
try:
    tokens = auth.exchange_code_for_tokens(auth_code)
except AuthenticationError as e:
    print(f"Authentication failed: {e}")

# Token expiration
try:
    accounts = client.get_accounts()
except TokenExpiredError:
    # Automatic refresh happens, but you can handle if needed
    auth.refresh_access_token()

# Order validation
try:
    order = client.modify_order_price(account_number, order_id, -10.00)
except OrderValidationError as e:
    print(f"Invalid order modification: {e}")
    if e.validation_errors:
        for field, error in e.validation_errors.items():
            print(f"  {field}: {error}")

# API errors
try:
    order = client.get_order(account_number, 99999999)
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        print("Order not found")
    elif e.response.status_code == 429:
        print("Rate limit exceeded")
```

### Error Recovery
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def place_order_with_retry(client, account_number, order):
    try:
        return await client.place_order(account_number, order)
    except Exception as e:
        print(f"Retry attempt failed: {e}")
        raise

# Automatic retry with exponential backoff
result = await place_order_with_retry(client, account_number, order)
```

## Additional Features

### Transaction History
```python
# Get transactions
transactions = client.get_transactions(
    account_number=account_number,
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    types="TRADE",  # TRADE, DIVIDEND, INTEREST, etc.
    symbol="AAPL"
)

for txn in transactions:
    print(f"{txn.transactionDate}: {txn.description} - ${txn.netAmount}")
```

### User Preferences
```python
# Get user preferences
prefs = client.get_user_preferences()
print(f"Express trading: {prefs.expressTrading}")
print(f"Default order duration: {prefs.defaultOrderDuration}")
```

### Options Chain Analysis
```python
# Get options chain with Greeks
chain = client.get_options_chain(
    symbol="AAPL",
    contract_type="ALL",
    include_quotes=True,
    volatility=25.0,
    underlying_price=150.00,
    interest_rate=5.0,
    days_to_expiration=30
)

# Analyze options
for expiration, strikes in chain.callExpDateMap.items():
    for strike, options in strikes.items():
        option = options[0]
        print(f"Strike: ${strike}")
        print(f"  Delta: {option.delta}")
        print(f"  Gamma: {option.gamma}")
        print(f"  Theta: {option.theta}")
        print(f"  Vega: {option.vega}")
        print(f"  IV: {option.volatility}%")
```

## Best Practices

1. **Use Paper Trading First**: Always test new strategies in paper trading
2. **Monitor Rate Limits**: The library handles rate limiting automatically
3. **Handle Errors Gracefully**: Implement proper error handling for production
4. **Use Async for Performance**: Leverage async operations for better performance
5. **Save Portfolio State**: Regularly save portfolio state for recovery
6. **Validate Orders**: Always validate orders before submission
7. **Use Streaming Wisely**: Stream only necessary symbols to reduce load

## Getting Started

See the [examples](../examples/) directory for complete working examples of all features.