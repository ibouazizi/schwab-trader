# Order Types Tutorial

This comprehensive tutorial covers all order types supported by the Schwab Trader library, with detailed explanations, use cases, and practical examples.

## Table of Contents
1. [Basic Order Types](#basic-order-types)
2. [Advanced Order Types](#advanced-order-types)
3. [Market Close Orders](#market-close-orders)
4. [Special Order Types](#special-order-types)
5. [Order Instructions](#order-instructions)
6. [Order Duration](#order-duration)
7. [Order Sessions](#order-sessions)
8. [Special Instructions](#special-instructions)
9. [Order Modification](#order-modification)
10. [Best Practices](#best-practices)

## Basic Order Types

### Market Orders

Market orders execute immediately at the best available price.

```python
from schwab import SchwabClient

client = SchwabClient(auth=auth)

# Buy 100 shares at market price
market_order = client.create_market_order(
    symbol="AAPL",
    quantity=100,
    instruction="BUY"
)
client.place_order(account_number, market_order)

# Sell 50 shares at market price
sell_order = client.create_market_order(
    symbol="MSFT",
    quantity=50,
    instruction="SELL"
)
```

**When to use:**
- Need immediate execution
- Trading highly liquid securities
- Small orders unlikely to move the market

**Pros:**
- Guaranteed execution (in liquid markets)
- Fast fills
- Simple to use

**Cons:**
- No price control
- Slippage risk in volatile markets
- Can be expensive in illiquid securities

### Limit Orders

Limit orders specify the maximum price (buy) or minimum price (sell) you're willing to accept.

```python
# Buy at $150 or better
limit_buy = client.create_limit_order(
    symbol="AAPL",
    quantity=100,
    limit_price=150.00,
    instruction="BUY"
)

# Sell at $155 or better
limit_sell = client.create_limit_order(
    symbol="AAPL",
    quantity=100,
    limit_price=155.00,
    instruction="SELL"
)

# Good-till-cancel limit order
gtc_limit = client.create_limit_order(
    symbol="MSFT",
    quantity=50,
    limit_price=350.00,
    instruction="BUY",
    duration="GOOD_TILL_CANCEL"
)
```

**When to use:**
- Price is more important than execution speed
- Trading less liquid securities
- Setting entry/exit points in advance

**Pros:**
- Price protection
- Can get better fills than market orders
- Set and forget capability

**Cons:**
- No guarantee of execution
- May miss opportunities if price moves away
- Partial fills possible

## Advanced Order Types

### Stop Orders

Stop orders become market orders when a trigger price is reached.

```python
# Stop loss order
stop_loss = client.create_stop_order(
    symbol="AAPL",
    quantity=100,
    stop_price=140.00,
    instruction="SELL"
)

# Stop entry order (buy if price breaks above resistance)
stop_entry = client.create_stop_order(
    symbol="TSLA",
    quantity=25,
    stop_price=850.00,
    instruction="BUY"
)
```

**When to use:**
- Protecting profits or limiting losses
- Entering positions on breakouts
- Automated exit strategies

**Pros:**
- Automatic execution at trigger
- Risk management tool
- Works while you're away

**Cons:**
- Converts to market order (no price guarantee)
- Can be triggered by brief price spikes
- Gap risk in fast-moving markets

### Stop-Limit Orders

Stop-limit orders become limit orders when triggered.

```python
# Stop-limit sell order
stop_limit_sell = client.create_stop_limit_order(
    symbol="AAPL",
    quantity=100,
    stop_price=140.00,    # Trigger price
    limit_price=138.00,   # Minimum acceptable price
    instruction="SELL"
)

# Stop-limit buy order
stop_limit_buy = client.create_stop_limit_order(
    symbol="NVDA",
    quantity=50,
    stop_price=650.00,    # Trigger when price rises to this
    limit_price=655.00,   # Maximum price to pay
    instruction="BUY"
)
```

**When to use:**
- Want stop protection with price control
- Avoiding slippage in volatile markets
- More precise exit strategies

**Pros:**
- Price protection after trigger
- Avoids bad fills in fast markets
- More control than regular stops

**Cons:**
- May not execute if price gaps past limit
- More complex to set up
- Requires careful price selection

### Trailing Stop Orders

Trailing stops adjust automatically as price moves favorably.

```python
# Dollar-based trailing stop
trailing_dollar = client.create_trailing_stop_order(
    symbol="AAPL",
    quantity=100,
    stop_price_offset=5.00,  # $5 below market
    instruction="SELL",
    stop_price_link_type="VALUE"  # Dollar amount
)

# Percentage-based trailing stop
trailing_percent = client.create_trailing_stop_order(
    symbol="TSLA",
    quantity=50,
    stop_price_offset=0.05,  # 5% below market
    instruction="SELL",
    stop_price_link_type="PERCENT"  # Percentage
)
```

**When to use:**
- Protecting profits in trending markets
- Letting winners run
- Dynamic risk management

**Pros:**
- Automatically adjusts with favorable moves
- Locks in profits
- No manual adjustment needed

**Cons:**
- Can be triggered by normal pullbacks
- Becomes market order when triggered
- Requires choosing appropriate trail amount

## Market Close Orders

### Market-on-Close (MOC) Orders

Execute at the official closing price.

```python
# Buy at market close
moc_buy = client.create_market_on_close_order(
    symbol="SPY",
    quantity=100,
    instruction="BUY"
)

# Sell at market close
moc_sell = client.create_market_on_close_order(
    symbol="QQQ",
    quantity=50,
    instruction="SELL"
)
```

**When to use:**
- Index fund rebalancing
- Matching closing benchmarks
- End-of-day portfolio adjustments

**Pros:**
- Executes at official close
- Good liquidity at close
- Used by institutional investors

**Cons:**
- Must submit before cutoff (usually 3:45 PM ET)
- No price control
- Can't cancel near close

### Limit-on-Close (LOC) Orders

Execute at close if price meets limit criteria.

```python
# Buy at close if price is below limit
loc_buy = client.create_limit_on_close_order(
    symbol="AAPL",
    quantity=100,
    limit_price=150.00,
    instruction="BUY"
)

# Sell at close if price is above limit
loc_sell = client.create_limit_on_close_order(
    symbol="MSFT",
    quantity=50,
    limit_price=355.00,
    instruction="SELL"
)
```

**When to use:**
- Want closing price with protection
- Index-related strategies with limits
- Risk-controlled closing trades

**Pros:**
- Price protection at close
- Participates in closing auction
- Combines MOC benefits with limits

**Cons:**
- May not execute if limit not met
- Cutoff time restrictions
- Less flexible than regular limits

## Special Order Types

### Cabinet Orders (Options)

Used to close out cheap options positions.

```python
# Close out worthless options
from schwab.models.generated.trading_models import Order, OrderLeg, Instrument

cabinet_order = Order(
    orderType="CABINET",
    session="NORMAL",
    duration="DAY",
    orderStrategyType="SINGLE",
    orderLegCollection=[
        OrderLeg(
            instruction="SELL_TO_CLOSE",
            quantity=10,
            instrument=Instrument(
                symbol="AAPL_012025C200",
                assetType="OPTION"
            )
        )
    ]
)
```

### Non-Marketable Orders

Limit orders intentionally priced away from market.

```python
# Non-marketable limit order
non_marketable = Order(
    orderType="NON_MARKETABLE",
    session="NORMAL",
    price=140.00,  # Well below current price
    duration="DAY",
    orderStrategyType="SINGLE",
    orderLegCollection=[
        OrderLeg(
            instruction="BUY",
            quantity=100,
            instrument=Instrument(
                symbol="AAPL",
                assetType="EQUITY"
            )
        )
    ]
)
```

### Net Debit/Credit Orders (Multi-leg)

For complex options strategies with net pricing.

```python
# Net debit order for vertical spread
net_debit = Order(
    orderType="NET_DEBIT",
    price=2.50,  # Maximum debit to pay
    session="NORMAL",
    duration="DAY",
    complexOrderStrategyType="VERTICAL",
    orderLegCollection=[
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025C440",
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025C450",
                assetType="OPTION"
            )
        )
    ]
)
```

## Order Instructions

### Equity Instructions

```python
# Standard buy/sell
BUY = "BUY"              # Buy to establish/add position
SELL = "SELL"            # Sell to reduce/close position

# Short selling
SELL_SHORT = "SELL_SHORT"     # Sell shares you don't own
BUY_TO_COVER = "BUY_TO_COVER" # Buy back short position

# Examples
# Going long
buy_long = client.create_market_order(
    symbol="AAPL",
    quantity=100,
    instruction="BUY"
)

# Going short
sell_short = client.create_market_order(
    symbol="TSLA",
    quantity=50,
    instruction="SELL_SHORT"
)

# Covering short
buy_cover = client.create_market_order(
    symbol="TSLA",
    quantity=50,
    instruction="BUY_TO_COVER"
)
```

### Options Instructions

```python
# Opening positions
BUY_TO_OPEN = "BUY_TO_OPEN"    # Buy options to open
SELL_TO_OPEN = "SELL_TO_OPEN"  # Sell (write) options to open

# Closing positions
SELL_TO_CLOSE = "SELL_TO_CLOSE"  # Sell options to close
BUY_TO_CLOSE = "BUY_TO_CLOSE"    # Buy options to close

# Examples
# Buy a call option
buy_call = client.create_limit_order(
    symbol="AAPL_012025C150",
    quantity=1,
    limit_price=5.50,
    instruction="BUY_TO_OPEN"
)

# Write a covered call
sell_call = client.create_limit_order(
    symbol="AAPL_012025C160",
    quantity=1,
    limit_price=3.00,
    instruction="SELL_TO_OPEN"
)

# Close option position
close_option = client.create_limit_order(
    symbol="AAPL_012025C150",
    quantity=1,
    limit_price=8.00,
    instruction="SELL_TO_CLOSE"
)
```

## Order Duration

Control how long orders remain active:

```python
# Day order (expires at close)
day_order = client.create_limit_order(
    symbol="AAPL",
    quantity=100,
    limit_price=150.00,
    instruction="BUY",
    duration="DAY"  # Default
)

# Good-till-cancel (GTC)
gtc_order = client.create_limit_order(
    symbol="MSFT",
    quantity=50,
    limit_price=350.00,
    instruction="BUY",
    duration="GOOD_TILL_CANCEL"
)

# Fill-or-kill (FOK)
fok_order = client.create_limit_order(
    symbol="SPY",
    quantity=1000,
    limit_price=440.00,
    instruction="BUY",
    duration="FILL_OR_KILL"
)

# Immediate-or-cancel (IOC)
ioc_order = client.create_limit_order(
    symbol="QQQ",
    quantity=500,
    limit_price=360.00,
    instruction="SELL",
    duration="IMMEDIATE_OR_CANCEL"
)

# Other durations
WEEK = "WEEK"                    # Expires end of week
MONTH = "MONTH"                  # Expires end of month
END_OF_WEEK = "END_OF_WEEK"      # Expires Friday
END_OF_MONTH = "END_OF_MONTH"    # Expires last trading day
```

## Order Sessions

Trade in different market sessions:

```python
# Regular hours only
regular_order = client.create_limit_order(
    symbol="AAPL",
    quantity=100,
    limit_price=150.00,
    instruction="BUY",
    session="NORMAL"  # 9:30 AM - 4:00 PM ET
)

# Pre-market order
premarket_order = client.create_limit_order(
    symbol="TSLA",
    quantity=50,
    limit_price=800.00,
    instruction="BUY",
    session="AM"  # 7:00 AM - 9:30 AM ET
)

# After-hours order
afterhours_order = client.create_limit_order(
    symbol="NVDA",
    quantity=25,
    limit_price=650.00,
    instruction="SELL",
    session="PM"  # 4:00 PM - 8:00 PM ET
)

# All sessions (seamless)
seamless_order = client.create_limit_order(
    symbol="SPY",
    quantity=100,
    limit_price=440.00,
    instruction="BUY",
    session="SEAMLESS"  # All available sessions
)
```

## Special Instructions

Additional order handling instructions:

```python
# All-or-none (AON)
aon_order = Order(
    orderType="LIMIT",
    price=150.00,
    session="NORMAL",
    duration="DAY",
    specialInstruction="ALL_OR_NONE",
    orderLegCollection=[
        OrderLeg(
            instruction="BUY",
            quantity=1000,
            instrument=Instrument(
                symbol="AAPL",
                assetType="EQUITY"
            )
        )
    ]
)

# Do-not-reduce (DNR)
dnr_order = Order(
    orderType="LIMIT",
    price=50.00,
    session="NORMAL",
    duration="GOOD_TILL_CANCEL",
    specialInstruction="DO_NOT_REDUCE",
    orderLegCollection=[
        OrderLeg(
            instruction="SELL",
            quantity=100,
            instrument=Instrument(
                symbol="T",  # AT&T
                assetType="EQUITY"
            )
        )
    ]
)
```

## Order Modification

### Modify Existing Orders

```python
# Change order price
modified = client.modify_order_price(
    account_number=account_number,
    order_id=12345,
    new_price=155.00
)

# Change order quantity
modified = client.modify_order_quantity(
    account_number=account_number,
    order_id=12345,
    new_quantity=200
)

# Replace entire order
new_order = client.create_limit_order(
    symbol="AAPL",
    quantity=150,
    limit_price=152.00,
    instruction="BUY"
)

replaced = client.replace_order(
    account_number=account_number,
    order_id=12345,
    new_order=new_order
)
```

### Cancel Orders

```python
# Cancel single order
client.cancel_order(
    account_number=account_number,
    order_id=12345
)

# Batch cancel
results = client.batch_cancel_orders(
    account_number=account_number,
    order_ids=[12345, 12346, 12347]
)

# Check results
for order_id, success in results.items():
    if success:
        print(f"Order {order_id} cancelled")
    else:
        print(f"Failed to cancel {order_id}")
```

## Best Practices

### 1. Order Type Selection

```python
def select_order_type(volatility, urgency, price_sensitivity):
    """
    Guide for selecting appropriate order type
    """
    if urgency == "HIGH" and price_sensitivity == "LOW":
        return "MARKET"
    elif price_sensitivity == "HIGH":
        return "LIMIT"
    elif volatility == "HIGH" and urgency == "MEDIUM":
        return "STOP_LIMIT"
    else:
        return "LIMIT"  # Default to limit for safety
```

### 2. Risk Management

```python
def create_bracket_order(symbol, entry_price, quantity):
    """
    Create entry with profit target and stop loss
    """
    # Entry order
    entry = client.create_limit_order(
        symbol=symbol,
        quantity=quantity,
        limit_price=entry_price,
        instruction="BUY"
    )
    
    # Profit target (2% above entry)
    target = client.create_limit_order(
        symbol=symbol,
        quantity=quantity,
        limit_price=entry_price * 1.02,
        instruction="SELL"
    )
    
    # Stop loss (1% below entry)
    stop_loss = client.create_stop_order(
        symbol=symbol,
        quantity=quantity,
        stop_price=entry_price * 0.99,
        instruction="SELL"
    )
    
    return entry, target, stop_loss
```

### 3. Extended Hours Considerations

```python
def place_extended_hours_order(symbol, quantity, limit_price, session):
    """
    Place order with extended hours best practices
    """
    # Always use limit orders in extended hours
    if session in ["AM", "PM"]:
        order = client.create_limit_order(
            symbol=symbol,
            quantity=quantity,
            limit_price=limit_price,
            instruction="BUY",
            session=session
        )
    else:
        raise ValueError("Use AM or PM for extended hours")
    
    return order
```

### 4. Order Validation

```python
def validate_order_parameters(order_type, price, stop_price=None):
    """
    Validate order parameters before submission
    """
    if order_type == "LIMIT" and price <= 0:
        raise ValueError("Limit price must be positive")
    
    if order_type == "STOP_LIMIT":
        if not stop_price or stop_price <= 0:
            raise ValueError("Stop price required and must be positive")
        if price <= 0:
            raise ValueError("Limit price must be positive")
    
    return True
```

### 5. Smart Order Routing

```python
# Let Schwab's smart order router find best execution
order = Order(
    orderType="LIMIT",
    price=150.00,
    session="NORMAL",
    duration="DAY",
    # No specific destination - uses smart routing
    orderLegCollection=[
        OrderLeg(
            instruction="BUY",
            quantity=100,
            instrument=Instrument(
                symbol="AAPL",
                assetType="EQUITY"
            )
        )
    ]
)
```

## Common Pitfalls to Avoid

1. **Using market orders in pre/post market** - Always use limits
2. **Setting stops too close** - Account for normal volatility
3. **Forgetting GTC expiration** - GTC orders expire after 60-90 days
4. **Ignoring partial fills** - Monitor fill status
5. **Wrong instruction for position** - Verify BUY vs BUY_TO_COVER

## Order Type Quick Reference

| Order Type | Execution | Price Control | Best For |
|------------|-----------|---------------|----------|
| Market | Immediate | None | Liquid stocks, urgent trades |
| Limit | When price met | Full control | Most situations |
| Stop | Triggered, then market | None after trigger | Stop losses, breakout entries |
| Stop-Limit | Triggered, then limit | Control after trigger | Volatile markets |
| Trailing Stop | Dynamic trigger | None after trigger | Trend following |
| MOC | At close | None | Index tracking |
| LOC | At close if limit met | Yes | Protected closing trades |

## Conclusion

Understanding order types is crucial for effective trading. Start with simple limit orders, then gradually incorporate more advanced types as your strategy requires. Always test new order types with small positions first, and remember that the best order type depends on your specific goals, market conditions, and risk tolerance.

For complex strategies involving multiple order types, see the [Order Strategies Guide](ORDER_STRATEGIES.md).