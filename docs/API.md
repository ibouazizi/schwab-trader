# Schwab API Python Library Documentation

## ⚠️ Important Notice
This API documentation is provided for informational purposes only. Before using this library, please read and understand our [full disclaimer](DISCLAIMER.md). By using this library, you acknowledge that trading involves substantial risk and that you are solely responsible for verifying and validating all trading operations.

## Table of Contents
1. [Installation](#installation)
2. [Authentication](#authentication)
3. [Client Initialization](#client-initialization)
4. [Account Management](#account-management)
5. [Order Creation](#order-creation)
6. [Order Management](#order-management)
7. [Order Monitoring](#order-monitoring)
8. [Market Data](#market-data)
9. [Portfolio Management](#portfolio-management)
10. [Paper Trading](#paper-trading)
11. [Streaming Data](#streaming-data)
12. [Batch Operations](#batch-operations)
13. [Error Handling](#error-handling)
14. [Async Support](#async-support)

## Installation

### From PyPI
```bash
pip install schwab-trader
```

### From Source
```bash
git clone https://github.com/ibouazizi/schwab-trader.git
cd schwab-trader
pip install -e .
```

## Authentication

### OAuth 2.0 Flow
```python
from schwab.auth import SchwabAuth

# Initialize auth handler
auth = SchwabAuth(
    client_id="your_client_id",
    client_secret="your_client_secret",
    redirect_uri="https://localhost:8080/callback"
)

# Get authorization URL
auth_url = auth.get_authorization_url()
print(f"Please authorize at: {auth_url}")

# After user authorizes, exchange code for tokens
auth_code = "code_from_callback"
tokens = auth.exchange_code_for_tokens(auth_code)

# Tokens are automatically managed and refreshed
```

## Client Initialization

### Synchronous Client
```python
from schwab import SchwabClient

# Initialize with auth object
client = SchwabClient(auth=auth)

# Or initialize with existing tokens
client = SchwabClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    access_token="your_access_token",
    refresh_token="your_refresh_token"
)
```

### Asynchronous Client
```python
from schwab import AsyncSchwabClient

# Initialize async client
async_client = AsyncSchwabClient(auth=auth)

# Use as context manager
async with async_client as client:
    accounts = await client.get_account_numbers()
```

## Account Management

### Get Account Numbers
```python
accounts = client.get_account_numbers()
```

### Get All Accounts
```python
# Get all accounts without positions
accounts = client.get_accounts()

# Get all accounts with positions
accounts = client.get_accounts(include_positions=True)
```

### Get Account with Positions
```python
account = client.get_account(
    account_number="encrypted_account_number",
    include_positions=True
)
```

## Order Creation

### Market Order
```python
order = client.create_market_order(
    symbol="AAPL",
    quantity=100,
    instruction=OrderInstruction.BUY,
    description="APPLE INC"
)
```

### Limit Order
```python
order = client.create_limit_order(
    symbol="AAPL",
    quantity=100,
    limit_price=150.00,
    instruction=OrderInstruction.BUY,
    description="APPLE INC"
)
```

### Stop Order
```python
order = client.create_stop_order(
    symbol="AAPL",
    quantity=100,
    stop_price=140.00,
    instruction=OrderInstruction.SELL,
    description="APPLE INC"
)
```

### Stop-Limit Order
```python
order = client.create_stop_limit_order(
    symbol="AAPL",
    quantity=100,
    stop_price=140.00,
    limit_price=138.00,
    instruction=OrderInstruction.SELL,
    description="APPLE INC"
)
```

## Order Management

### Place Order
```python
client.place_order(account_number="encrypted_account_number", order=order)
```

### Get Order Status
```python
order = client.get_order(
    account_number="encrypted_account_number",
    order_id=12345
)
```

### Get Orders History
```python
from datetime import datetime, timedelta

orders = client.get_orders(
    account_number="encrypted_account_number",
    from_date=datetime.now() - timedelta(days=7),
    to_date=datetime.now(),
    status="WORKING"  # Optional status filter
)
```

### Modify Order Price
```python
modified_order = client.modify_order_price(
    account_number="encrypted_account_number",
    order_id=12345,
    new_price=155.00
)
```

### Modify Order Quantity
```python
modified_order = client.modify_order_quantity(
    account_number="encrypted_account_number",
    order_id=12345,
    new_quantity=200
)
```

### Cancel Order
```python
client.cancel_order(
    account_number="encrypted_account_number",
    order_id=12345
)
```

## Order Monitoring

### Monitor Orders with Callbacks
```python
from schwab.order_monitor import OrderMonitor

# Initialize order monitor
monitor = OrderMonitor(client)

# Define callbacks
def on_status_change(order, old_status, new_status):
    print(f"Order {order.order_id}: {old_status} -> {new_status}")

def on_execution(order, execution):
    print(f"Order {order.order_id} executed: {execution.quantity} @ ${execution.price}")

# Start monitoring
monitor.start_monitoring(
    account_number="encrypted_account_number",
    order_ids=[12345, 12346],
    on_status_change=on_status_change,
    on_execution=on_execution,
    interval=1.0  # Poll every second
)

# Stop monitoring
monitor.stop_monitoring()
```


## Market Data

### Get Quotes
```python
# Single quote
quote = client.get_quote("AAPL")

# Multiple quotes
quotes = client.get_quotes(["AAPL", "MSFT", "GOOGL"])

# Access quote data
print(f"AAPL Price: ${quotes['AAPL'].quote.lastPrice}")
print(f"AAPL Volume: {quotes['AAPL'].quote.totalVolume}")
```

### Get Options Chain
```python
options_chain = client.get_options_chain(
    symbol="AAPL",
    contract_type="ALL",  # CALL, PUT, or ALL
    strike_count=10,
    include_quotes=True,
    strategy="SINGLE",
    interval=5.0,
    strike=150.0,
    range="ITM"  # ITM, OTM, or ALL
)
```

## Portfolio Management

### Portfolio Manager
```python
from schwab.portfolio import PortfolioManager

# Create portfolio manager
portfolio = PortfolioManager(client)

# Add accounts to track
portfolio.add_account("account1")
portfolio.add_account("account2")

# Refresh all positions
portfolio.refresh_positions()

# Get portfolio summary
summary = portfolio.get_portfolio_summary()
print(f"Total Value: ${summary['total_value']:,.2f}")
print(f"Total P&L: ${summary['total_pnl']:,.2f}")

# Get aggregated position
aapl_position = portfolio.get_position("AAPL")
if aapl_position:
    print(f"Total AAPL shares: {aapl_position['total_quantity']}")
    print(f"Average cost: ${aapl_position['average_cost']:,.2f}")

# Monitor portfolio orders
def on_portfolio_update(event_type, data):
    print(f"Portfolio event: {event_type}")

portfolio.monitor_orders(callback=on_portfolio_update)
```

### Save/Load Portfolio State
```python
# Save portfolio state
portfolio.save_state("portfolio_backup.json")

# Load portfolio state
portfolio.load_state("portfolio_backup.json")
```

## Paper Trading

### Paper Trading Client
```python
from schwab.paper_trading import PaperTradingClient

# Initialize paper trading client
paper_client = PaperTradingClient(auth=auth)

# Client automatically detects paper vs real accounts
# Visual indicators show when in paper trading mode

# Place a paper trade
order = paper_client.create_market_order(
    symbol="AAPL",
    quantity=100,
    instruction="BUY"
)

result = paper_client.place_order("paper_account_id", order)
# Shows visual indicator: "[PAPER TRADING] Order placed..."
```

### Paper Trading Indicators
```python
from schwab.paper_trading.indicators import RSI, MovingAverage, MACD

# Calculate RSI
rsi = RSI(period=14)
rsi_values = rsi.calculate(price_data)

# Calculate Moving Average
ma = MovingAverage(period=20, ma_type="EMA")
ma_values = ma.calculate(price_data)

# Calculate MACD
macd = MACD(fast_period=12, slow_period=26, signal_period=9)
macd_line, signal_line, histogram = macd.calculate(price_data)
```

## Streaming Data

### WebSocket Streaming
```python
from schwab.streaming import SchwabStreamer

# Initialize streamer
streamer = SchwabStreamer(client)

# Define callback for quote updates
def on_quote_update(data):
    print(f"Quote update: {data}")

# Subscribe to real-time quotes
streamer.subscribe_quotes(
    symbols=["AAPL", "MSFT"],
    callback=on_quote_update
)

# Start streaming
streamer.start()

# Stop streaming
streamer.stop()
```

### Advanced Streaming
```python
# Subscribe to level 1 data
streamer.subscribe_level_one_equity(
    symbols=["AAPL"],
    fields=["BID_PRICE", "ASK_PRICE", "LAST_PRICE", "TOTAL_VOLUME"]
)

# Subscribe to options
streamer.subscribe_level_one_option(
    symbols=["AAPL_012025C150"],
    fields=["BID_PRICE", "ASK_PRICE", "IMPLIED_VOLATILITY"]
)

# Quality of Service
streamer.set_quality_of_service("EXPRESS")  # REAL_TIME, FAST, MODERATE, EXPRESS
```

## Batch Operations

### Batch Cancel Orders
```python
results = client.batch_cancel_orders(
    account_number="encrypted_account_number",
    order_ids=[12345, 12346, 12347]
)
# results is a dict mapping order_ids to success status
```

### Batch Modify Orders
```python
modifications = [
    {"order_id": 12345, "price": 155.00},
    {"order_id": 12346, "quantity": 200},
    {"order_id": 12347, "price": 160.00, "quantity": 150}
]

results = client.batch_modify_orders(
    account_number="encrypted_account_number",
    modifications=modifications
)
# results is a dict mapping order_ids to modified orders or exceptions
```

## Error Handling

### Order Validation Error
```python
from schwab.models.order_validation import OrderValidationError

try:
    modified_order = client.modify_order_price(
        account_number="encrypted_account_number",
        order_id=12345,
        new_price=155.00
    )
except OrderValidationError as e:
    print(f"Order modification failed: {str(e)}")
    print(f"Validation details: {e.validation_errors}")
```

### API Request Error
```python
import requests

try:
    order = client.get_order(
        account_number="encrypted_account_number",
        order_id=12345
    )
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
except requests.exceptions.RequestException as e:
    print(f"API request failed: {str(e)}")
```

### Authentication Error
```python
from schwab.auth import AuthenticationError

try:
    tokens = auth.exchange_code_for_tokens(auth_code)
except AuthenticationError as e:
    print(f"Authentication failed: {str(e)}")
```

## Async Support

### Async Operations
```python
import asyncio
from schwab import AsyncSchwabClient

async def main():
    async with AsyncSchwabClient(auth=auth) as client:
        # Concurrent operations
        accounts, quotes = await asyncio.gather(
            client.get_accounts(include_positions=True),
            client.get_quotes(["AAPL", "MSFT", "GOOGL"])
        )
        
        # Place order
        order = client.create_limit_order(
            symbol="AAPL",
            quantity=100,
            limit_price=150.00,
            instruction="BUY"
        )
        
        result = await client.place_order(accounts[0].account_number, order)
        print(f"Order placed: {result}")

# Run async function
asyncio.run(main())
```

### Async Paper Trading
```python
from schwab.paper_trading import AsyncPaperTradingClient

async def paper_trade():
    async with AsyncPaperTradingClient(auth=auth) as client:
        # All operations are async
        accounts = await client.get_account_numbers()
        
        # Paper trading with async support
        order = client.create_market_order(
            symbol="TSLA",
            quantity=50,
            instruction="BUY"
        )
        
        await client.place_order(accounts[0], order)
```

## Data Models

### Order Status Values
- `WORKING`: Order is active and working
- `PENDING_ACTIVATION`: Order is pending activation
- `PENDING_CANCEL`: Order cancellation is pending
- `PENDING_REPLACE`: Order replacement is pending
- `QUEUED`: Order is queued for submission
- `REJECTED`: Order was rejected
- `CANCELED`: Order was cancelled
- `FILLED`: Order was completely filled
- `EXPIRED`: Order has expired
- `REPLACED`: Order was replaced
- `PARTIALLY_FILLED`: Order was partially filled
- `ACCEPTED`: Order was accepted
- `AWAITING_MANUAL_REVIEW`: Order awaiting manual review
- `AWAITING_UR_OUT`: Order awaiting UR out

### Order Instructions
- `BUY`: Buy to open position
- `SELL`: Sell to close position
- `BUY_TO_COVER`: Buy to cover short position
- `SELL_SHORT`: Sell short
- `BUY_TO_CLOSE`: Buy to close (options)
- `SELL_TO_CLOSE`: Sell to close (options)
- `BUY_TO_OPEN`: Buy to open (options)
- `SELL_TO_OPEN`: Sell to open (options)

### Order Types
- `MARKET`: Market order
- `LIMIT`: Limit order
- `STOP`: Stop order
- `STOP_LIMIT`: Stop-limit order
- `TRAILING_STOP`: Trailing stop order
- `MARKET_ON_CLOSE`: Market-on-close order
- `LIMIT_ON_CLOSE`: Limit-on-close order
- `CABINET`: Cabinet order (options)
- `NON_MARKETABLE`: Non-marketable limit order
- `NET_DEBIT`: Net debit (multi-leg)
- `NET_CREDIT`: Net credit (multi-leg)
- `NET_ZERO`: Net zero (multi-leg)

### Order Duration
- `DAY`: Day order
- `GOOD_TILL_CANCEL`: Good-till-cancel order
- `FILL_OR_KILL`: Fill-or-kill order
- `IMMEDIATE_OR_CANCEL`: Immediate-or-cancel order
- `WEEK`: Week order
- `MONTH`: Month order
- `END_OF_WEEK`: End of week order
- `END_OF_MONTH`: End of month order
- `NEXT_END_OF_MONTH`: Next end of month order
- `UNKNOWN`: Unknown duration

### Complex Order Strategies
- `SINGLE`: Single leg order
- `COVERED`: Covered call/put
- `VERTICAL`: Vertical spread
- `BACK_RATIO`: Back ratio spread
- `CALENDAR`: Calendar spread
- `DIAGONAL`: Diagonal spread
- `STRADDLE`: Straddle
- `STRANGLE`: Strangle
- `COLLAR_SYNTHETIC`: Collar synthetic
- `BUTTERFLY`: Butterfly spread
- `CONDOR`: Condor spread
- `IRON_CONDOR`: Iron condor
- `VERTICAL_ROLL`: Vertical roll
- `COLLAR_WITH_STOCK`: Collar with stock
- `DOUBLE_DIAGONAL`: Double diagonal
- `UNBALANCED_BUTTERFLY`: Unbalanced butterfly
- `UNBALANCED_CONDOR`: Unbalanced condor
- `UNBALANCED_IRON_CONDOR`: Unbalanced iron condor
- `UNBALANCED_VERTICAL_ROLL`: Unbalanced vertical roll
- `CUSTOM`: Custom strategy

### Asset Types
- `EQUITY`: Stock/ETF
- `OPTION`: Option contract
- `MUTUAL_FUND`: Mutual fund
- `FIXED_INCOME`: Fixed income
- `INDEX`: Index
- `CASH_EQUIVALENT`: Cash equivalent
- `CURRENCY`: Currency
- `COLLECTIVE_INVESTMENT`: Collective investment

### Special Instructions
- `ALL_OR_NONE`: All-or-none order
- `DO_NOT_REDUCE`: Do not reduce order
- `ALL_OR_NONE_DO_NOT_REDUCE`: All-or-none and do not reduce

## Additional Resources

- [API Reference](API_REFERENCE.md) - Detailed method documentation
- [Order Types Tutorial](ORDER_TYPES_TUTORIAL.md) - Comprehensive order type guide
- [Order Strategies](ORDER_STRATEGIES.md) - Complex order strategies explained
- [Paper Trading Guide](PAPER_TRADING.md) - Safe testing environment setup
- [Asset Types](ASSET_TYPES.md) - Supported asset types and examples
- [Migration Guide](MIGRATION_GUIDE.md) - Upgrading from previous versions