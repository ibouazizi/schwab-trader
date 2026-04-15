# Complex Order Strategies Guide

This comprehensive guide covers all complex order strategies supported by the Schwab Trader library, including multi-leg options strategies and advanced order types.

## Table of Contents
1. [Overview](#overview)
2. [Basic Order Strategies](#basic-order-strategies)
3. [Options Spread Strategies](#options-spread-strategies)
4. [Volatility Strategies](#volatility-strategies)
5. [Income Strategies](#income-strategies)
6. [Advanced Strategies](#advanced-strategies)
7. [Order Types for Complex Strategies](#order-types-for-complex-strategies)
8. [Implementation Guide](#implementation-guide)
9. [Risk Management](#risk-management)

## Overview

Complex order strategies allow you to execute sophisticated trading strategies involving multiple options contracts or combinations of options and underlying securities. The Schwab Trader library supports all major complex order strategy types through the `ComplexOrderStrategyType` enum.

### Available Strategy Types

```python
from schwab.models.generated.trading_models import ComplexOrderStrategyType

# All supported complex order strategies
NONE = "NONE"                              # Simple single-leg orders
COVERED = "COVERED"                        # Covered calls/puts
VERTICAL = "VERTICAL"                      # Vertical spreads
BACK_RATIO = "BACK_RATIO"                  # Back ratio spreads
CALENDAR = "CALENDAR"                      # Calendar spreads
DIAGONAL = "DIAGONAL"                      # Diagonal spreads
STRADDLE = "STRADDLE"                      # Straddles
STRANGLE = "STRANGLE"                      # Strangles
COLLAR_SYNTHETIC = "COLLAR_SYNTHETIC"      # Synthetic collars
BUTTERFLY = "BUTTERFLY"                    # Butterfly spreads
CONDOR = "CONDOR"                          # Condor spreads
IRON_CONDOR = "IRON_CONDOR"                # Iron condors
VERTICAL_ROLL = "VERTICAL_ROLL"            # Vertical rolls
COLLAR_WITH_STOCK = "COLLAR_WITH_STOCK"    # Collar with stock
DOUBLE_DIAGONAL = "DOUBLE_DIAGONAL"        # Double diagonal
UNBALANCED_BUTTERFLY = "UNBALANCED_BUTTERFLY"
UNBALANCED_CONDOR = "UNBALANCED_CONDOR"
UNBALANCED_IRON_CONDOR = "UNBALANCED_IRON_CONDOR"
UNBALANCED_VERTICAL_ROLL = "UNBALANCED_VERTICAL_ROLL"
MUTUAL_FUND_SWAP = "MUTUAL_FUND_SWAP"
CUSTOM = "CUSTOM"                          # Custom strategies
```

## Basic Order Strategies

### SINGLE (None)
The default strategy for simple, single-leg orders.

```python
from schwab import SchwabClient
from schwab.models.generated.trading_models import Order, OrderLeg, Instrument

client = SchwabClient(auth=auth)

# Simple stock purchase
order = client.create_market_order(
    symbol="AAPL",
    quantity=100,
    instruction="BUY"
)
```

### COVERED
Combines a long stock position with a short call (covered call) or short stock with a short put (covered put).

```python
# Covered Call: Buy stock + Sell call
order = Order(
    orderType="NET_DEBIT",
    session="NORMAL",
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="COVERED",
    orderLegCollection=[
        OrderLeg(
            instruction="BUY",
            quantity=100,
            instrument=Instrument(
                symbol="AAPL",
                assetType="EQUITY"
            )
        ),
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="AAPL_012025C200",  # Jan 2025 $200 Call
                assetType="OPTION"
            )
        )
    ]
)

client.place_order(account_number, order)
```

## Options Spread Strategies

### VERTICAL
Same expiration, different strikes. Used for directional bets with limited risk.

```python
# Bull Call Spread
order = Order(
    orderType="NET_DEBIT",
    session="NORMAL",
    price=2.50,  # Net debit of $2.50
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="VERTICAL",
    orderLegCollection=[
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025C440",  # Buy $440 call
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025C450",  # Sell $450 call
                assetType="OPTION"
            )
        )
    ]
)

# Bear Put Spread
order = Order(
    orderType="NET_DEBIT",
    session="NORMAL",
    price=3.00,
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="VERTICAL",
    orderLegCollection=[
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025P450",  # Buy $450 put
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025P440",  # Sell $440 put
                assetType="OPTION"
            )
        )
    ]
)
```

### CALENDAR
Same strike, different expirations. Profits from time decay and volatility changes.

```python
# Calendar Spread (Time Spread)
order = Order(
    orderType="NET_DEBIT",
    session="NORMAL",
    price=1.50,
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="CALENDAR",
    orderLegCollection=[
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="MSFT_121524C400",  # Sell Dec 15, 2024 $400 call
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="MSFT_012025C400",  # Buy Jan 2025 $400 call
                assetType="OPTION"
            )
        )
    ]
)
```

### DIAGONAL
Different strikes AND different expirations. Combines vertical and calendar spread characteristics.

```python
# Diagonal Spread
order = Order(
    orderType="NET_DEBIT",
    session="NORMAL",
    price=2.00,
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="DIAGONAL",
    orderLegCollection=[
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="AAPL_121524C195",  # Sell Dec $195 call
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="AAPL_012025C190",  # Buy Jan $190 call
                assetType="OPTION"
            )
        )
    ]
)
```

### BACK_RATIO
Unequal number of long and short options. Used for volatility plays.

```python
# Call Back Ratio (1x2)
order = Order(
    orderType="NET_CREDIT",
    session="NORMAL",
    price=0.50,  # Net credit
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="BACK_RATIO",
    orderLegCollection=[
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="TSLA_012025C800",  # Sell 1 ITM call
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=2,
            instrument=Instrument(
                symbol="TSLA_012025C850",  # Buy 2 OTM calls
                assetType="OPTION"
            )
        )
    ]
)
```

## Volatility Strategies

### STRADDLE
Buy or sell both call and put at same strike and expiration. Profits from large moves (long) or low volatility (short).

```python
# Long Straddle
order = Order(
    orderType="NET_DEBIT",
    session="NORMAL",
    price=10.00,
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="STRADDLE",
    orderLegCollection=[
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="NFLX_012025C600",  # Buy $600 call
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="NFLX_012025P600",  # Buy $600 put
                assetType="OPTION"
            )
        )
    ]
)

# Short Straddle (income strategy)
order = Order(
    orderType="NET_CREDIT",
    session="NORMAL",
    price=10.00,
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="STRADDLE",
    orderLegCollection=[
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025C450",
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025P450",
                assetType="OPTION"
            )
        )
    ]
)
```

### STRANGLE
Similar to straddle but with different strikes. Cheaper than straddle but requires larger move.

```python
# Long Strangle
order = Order(
    orderType="NET_DEBIT",
    session="NORMAL",
    price=5.00,
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="STRANGLE",
    orderLegCollection=[
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="TSLA_012025C850",  # OTM call
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="TSLA_012025P750",  # OTM put
                assetType="OPTION"
            )
        )
    ]
)
```

## Income Strategies

### BUTTERFLY
Three strikes, with middle strike having 2x quantity. Limited risk, limited reward.

```python
# Long Call Butterfly
order = Order(
    orderType="NET_DEBIT",
    session="NORMAL",
    price=2.00,
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="BUTTERFLY",
    orderLegCollection=[
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="AMZN_012025C180",  # Buy lower strike
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=2,
            instrument=Instrument(
                symbol="AMZN_012025C190",  # Sell 2x middle strike
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="AMZN_012025C200",  # Buy upper strike
                assetType="OPTION"
            )
        )
    ]
)

# Iron Butterfly (using puts and calls)
order = Order(
    orderType="NET_CREDIT",
    session="NORMAL",
    price=4.00,
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="BUTTERFLY",
    orderLegCollection=[
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025P440",  # Buy OTM put
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025P450",  # Sell ATM put
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025C450",  # Sell ATM call
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025C460",  # Buy OTM call
                assetType="OPTION"
            )
        )
    ]
)
```

### CONDOR
Four different strikes. Similar to butterfly but with wider profit zone.

```python
# Long Call Condor
order = Order(
    orderType="NET_DEBIT",
    session="NORMAL",
    price=1.50,
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="CONDOR",
    orderLegCollection=[
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025C430",  # Buy lowest strike
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025C440",  # Sell lower middle
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025C450",  # Sell upper middle
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025C460",  # Buy highest strike
                assetType="OPTION"
            )
        )
    ]
)
```

### IRON_CONDOR
Combination of bull put spread and bear call spread. Popular income strategy.

```python
# Iron Condor
order = Order(
    orderType="NET_CREDIT",
    session="NORMAL",
    price=3.00,  # Collect $3.00 credit
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="IRON_CONDOR",
    orderLegCollection=[
        # Bull Put Spread (lower strikes)
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="QQQ_012025P370",  # Buy OTM put
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="QQQ_012025P380",  # Sell higher put
                assetType="OPTION"
            )
        ),
        # Bear Call Spread (upper strikes)
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="QQQ_012025C420",  # Sell lower call
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="QQQ_012025C430",  # Buy OTM call
                assetType="OPTION"
            )
        )
    ]
)
```

## Advanced Strategies

### COLLAR_WITH_STOCK
Protective collar: Long stock + long put + short call

```python
# Collar with Stock
order = Order(
    orderType="NET_DEBIT",
    session="NORMAL",
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="COLLAR_WITH_STOCK",
    orderLegCollection=[
        OrderLeg(
            instruction="BUY",
            quantity=100,
            instrument=Instrument(
                symbol="MSFT",
                assetType="EQUITY"
            )
        ),
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="MSFT_012025P390",  # Protective put
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="MSFT_012025C410",  # Covered call
                assetType="OPTION"
            )
        )
    ]
)
```

### COLLAR_SYNTHETIC
Options-only collar using synthetic stock position

```python
# Synthetic Collar
order = Order(
    orderType="NET_CREDIT",
    session="NORMAL",
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="COLLAR_SYNTHETIC",
    orderLegCollection=[
        # Synthetic long stock
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="AAPL_012025C190",
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="AAPL_012025P190",
                assetType="OPTION"
            )
        ),
        # Collar
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="AAPL_012025P180",  # Protective put
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="AAPL_012025C200",  # Covered call
                assetType="OPTION"
            )
        )
    ]
)
```

### DOUBLE_DIAGONAL
Two diagonal spreads at different strikes

```python
# Double Diagonal
order = Order(
    orderType="NET_DEBIT",
    session="NORMAL",
    price=4.00,
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="DOUBLE_DIAGONAL",
    orderLegCollection=[
        # Lower diagonal (puts)
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_121524P440",  # Near-term put
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025P435",  # Far-term put
                assetType="OPTION"
            )
        ),
        # Upper diagonal (calls)
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_121524C460",  # Near-term call
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="SPY_012025C465",  # Far-term call
                assetType="OPTION"
            )
        )
    ]
)
```

### VERTICAL_ROLL
Rolling a vertical spread to a different expiration

```python
# Vertical Roll
order = Order(
    orderType="NET_CREDIT",
    session="NORMAL",
    duration="DAY",
    orderStrategyType="SINGLE",
    complexOrderStrategyType="VERTICAL_ROLL",
    orderLegCollection=[
        # Close existing spread
        OrderLeg(
            instruction="BUY_TO_CLOSE",
            quantity=1,
            instrument=Instrument(
                symbol="AAPL_121524C190",
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="SELL_TO_CLOSE",
            quantity=1,
            instrument=Instrument(
                symbol="AAPL_121524C200",
                assetType="OPTION"
            )
        ),
        # Open new spread
        OrderLeg(
            instruction="SELL_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="AAPL_012025C195",
                assetType="OPTION"
            )
        ),
        OrderLeg(
            instruction="BUY_TO_OPEN",
            quantity=1,
            instrument=Instrument(
                symbol="AAPL_012025C205",
                assetType="OPTION"
            )
        )
    ]
)
```

## Order Types for Complex Strategies

Complex strategies often use special order types:

### NET_DEBIT / NET_CREDIT / NET_ZERO

```python
# Net Debit Order (you pay)
order = Order(
    orderType="NET_DEBIT",
    price=2.50,  # Maximum debit to pay
    # ... rest of order
)

# Net Credit Order (you receive)
order = Order(
    orderType="NET_CREDIT",
    price=3.00,  # Minimum credit to receive
    # ... rest of order
)

# Net Zero Order (even exchange)
order = Order(
    orderType="NET_ZERO",
    # ... rest of order
)
```

## Implementation Guide

### Best Practices

1. **Order Validation**
```python
# Always validate complex orders before submission
def validate_complex_order(order):
    # Check strategy type matches leg configuration
    if order.complexOrderStrategyType == "VERTICAL":
        # Ensure same expiration
        expirations = set()
        for leg in order.orderLegCollection:
            # Extract expiration from symbol
            exp = leg.instrument.symbol.split('_')[1][:6]
            expirations.add(exp)
        
        if len(expirations) != 1:
            raise ValueError("Vertical spreads must have same expiration")
    
    # Check quantities match strategy
    if order.complexOrderStrategyType == "BUTTERFLY":
        quantities = [leg.quantity for leg in order.orderLegCollection]
        if len(quantities) != 3 or quantities[1] != quantities[0] + quantities[2]:
            raise ValueError("Butterfly middle strike must be 2x outer strikes")
    
    return True
```

2. **Price Calculation**
```python
# Calculate net price for complex orders
def calculate_net_price(quotes, order):
    net_price = 0
    
    for leg in order.orderLegCollection:
        symbol = leg.instrument.symbol
        quote = quotes[symbol]
        
        if leg.instruction in ["BUY", "BUY_TO_OPEN", "BUY_TO_CLOSE"]:
            # Use ask for buys
            price = quote.askPrice * leg.quantity * 100
            net_price += price
        else:
            # Use bid for sells
            price = quote.bidPrice * leg.quantity * 100
            net_price -= price
    
    return net_price
```

3. **Position Management**
```python
# Track complex positions
class ComplexPosition:
    def __init__(self, strategy_type, legs):
        self.strategy_type = strategy_type
        self.legs = legs
        self.entry_date = datetime.now()
        self.entry_prices = {}
    
    def calculate_pnl(self, current_quotes):
        total_pnl = 0
        for leg in self.legs:
            current_price = current_quotes[leg.symbol].lastPrice
            entry_price = self.entry_prices[leg.symbol]
            
            if leg.position_type == "LONG":
                pnl = (current_price - entry_price) * leg.quantity * 100
            else:  # SHORT
                pnl = (entry_price - current_price) * leg.quantity * 100
            
            total_pnl += pnl
        
        return total_pnl
```

## Risk Management

### Position Sizing
```python
def calculate_position_size(account_value, risk_percent, max_loss):
    """
    Calculate appropriate position size for complex strategies
    """
    risk_amount = account_value * (risk_percent / 100)
    position_size = risk_amount / max_loss
    return int(position_size)

# Example: Iron Condor sizing
account_value = 100000
risk_percent = 2  # Risk 2% per trade
max_loss = 500    # Max loss per contract

contracts = calculate_position_size(account_value, risk_percent, max_loss)
print(f"Trade {contracts} contracts")  # Trade 4 contracts
```

### Greeks Analysis
```python
# Analyze Greeks for complex positions
def analyze_position_greeks(option_chain, position_legs):
    total_delta = 0
    total_gamma = 0
    total_theta = 0
    total_vega = 0
    
    for leg in position_legs:
        option = option_chain.get_option(leg.symbol)
        multiplier = leg.quantity if leg.position_type == "LONG" else -leg.quantity
        
        total_delta += option.delta * multiplier * 100
        total_gamma += option.gamma * multiplier * 100
        total_theta += option.theta * multiplier * 100
        total_vega += option.vega * multiplier * 100
    
    return {
        "delta": total_delta,
        "gamma": total_gamma,
        "theta": total_theta,
        "vega": total_vega
    }
```

### Exit Strategies
```python
# Set up exit orders for complex strategies
def create_exit_orders(original_order, profit_target, stop_loss):
    """
    Create profit target and stop loss orders
    """
    # Profit target order (close at 50% of max profit)
    profit_order = Order(
        orderType="NET_DEBIT" if original_order.orderType == "NET_CREDIT" else "NET_CREDIT",
        price=original_order.price * 0.5,  # 50% profit target
        duration="GOOD_TILL_CANCEL",
        orderStrategyType="SINGLE",
        complexOrderStrategyType=original_order.complexOrderStrategyType,
        orderLegCollection=[
            # Reverse all legs
            OrderLeg(
                instruction=reverse_instruction(leg.instruction),
                quantity=leg.quantity,
                instrument=leg.instrument
            ) for leg in original_order.orderLegCollection
        ]
    )
    
    # Stop loss order
    stop_order = Order(
        orderType="NET_DEBIT" if original_order.orderType == "NET_CREDIT" else "NET_CREDIT",
        price=original_order.price * 2,  # 100% loss
        duration="GOOD_TILL_CANCEL",
        # ... rest of order
    )
    
    return profit_order, stop_order

def reverse_instruction(instruction):
    mapping = {
        "BUY_TO_OPEN": "SELL_TO_CLOSE",
        "SELL_TO_OPEN": "BUY_TO_CLOSE",
        "BUY_TO_CLOSE": "SELL_TO_OPEN",
        "SELL_TO_CLOSE": "BUY_TO_OPEN"
    }
    return mapping.get(instruction, instruction)
```

## Common Pitfalls and Solutions

### 1. Leg Ordering
Some brokers require legs in specific order:
```python
# Sort legs by strike price for consistency
order.orderLegCollection.sort(key=lambda x: extract_strike(x.instrument.symbol))
```

### 2. Execution Risk
```python
# Use all-or-none for complex orders
order.specialInstruction = "ALL_OR_NONE"
```

### 3. Pin Risk Management
```python
# Close positions before expiration to avoid assignment
def check_expiration_risk(position, days_to_expiration):
    if days_to_expiration <= 1 and position.has_short_options:
        return "HIGH_RISK: Consider closing position"
    return "OK"
```

## Additional Resources

- [Order Types Tutorial](ORDER_TYPES_TUTORIAL.md) - Detailed order type guide
- [Asset Types](ASSET_TYPES.md) - Asset-specific information
- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Paper Trading Guide](PAPER_TRADING.md) - Test strategies safely

## Disclaimer

Options trading involves substantial risk and is not suitable for all investors. Complex strategies can result in significant losses. Always understand the maximum risk and reward before entering any position.