# Asset Types Reference Guide

This guide covers the different asset types supported by the Schwab Trader Python library and provides specific information about trading each asset class.

## Overview

The Schwab Trader library supports multiple asset classes through its comprehensive API. Each asset type has unique characteristics, trading requirements, and API considerations that are important to understand for successful trading operations.

## Supported Asset Types

The library supports the following asset types as defined in the `AssetType` enum:

- **EQUITY** - Stocks, ETFs, and ADRs
- **OPTION** - Options contracts (calls and puts)
- **MUTUAL_FUND** - Mutual funds
- **FIXED_INCOME** - Bonds and fixed income securities
- **INDEX** - Market indices (for data reference only)
- **CASH_EQUIVALENT** - Money market funds and similar instruments
- **CURRENCY** - Foreign exchange (Forex)
- **COLLECTIVE_INVESTMENT** - Other collective investment vehicles

## Equity Trading

Equities include common stocks, ETFs (Exchange-Traded Funds), ADRs (American Depositary Receipts), and similar exchange-traded instruments.

### Key Features

- Support for all standard order types (market, limit, stop, etc.)
- Pre-market and after-hours trading sessions
- Real-time quotes and Level 1 data
- Dividend reinvestment options
- Tax lot selection methods
- Short selling capabilities

### Example: Placing Equity Orders

```python
from schwab import SchwabClient

client = SchwabClient(auth=auth)

# Simple market order
order = client.create_market_order(
    symbol="AAPL",
    quantity=100,
    instruction="BUY"
)
client.place_order(account_number, order)

# Limit order with extended hours
order = client.create_limit_order(
    symbol="MSFT",
    quantity=50,
    limit_price=350.00,
    instruction="SELL",
    session="SEAMLESS",  # Includes pre/post market
    duration="GOOD_TILL_CANCEL"
)
client.place_order(account_number, order)

# Stop-loss order
order = client.create_stop_order(
    symbol="TSLA",
    quantity=25,
    stop_price=800.00,
    instruction="SELL"
)
client.place_order(account_number, order)
```

### Special Considerations

- **Pattern Day Trading**: Accounts flagged as PDT have different margin requirements
- **Hard-to-Borrow**: Some stocks may have limited availability for short selling
- **Penny Stocks**: May have restricted order types and higher commissions
- **Extended Hours**: Limited liquidity and wider spreads during pre/post market

### Symbol Format
Standard ticker symbols: `AAPL`, `MSFT`, `SPY`, `QQQ`

## Options Trading

Options are derivatives contracts that provide the right (but not obligation) to buy or sell an underlying asset at a specific strike price before expiration.

### Key Features

- Full support for calls and puts
- Complex multi-leg strategies
- Standard and weekly expirations
- Exercise and assignment handling
- Greeks calculation
- Options-specific order instructions

### Option Order Instructions

```python
# Options-specific instructions
BUY_TO_OPEN = "BUY_TO_OPEN"      # Open long position
BUY_TO_CLOSE = "BUY_TO_CLOSE"    # Close short position
SELL_TO_OPEN = "SELL_TO_OPEN"    # Open short position
SELL_TO_CLOSE = "SELL_TO_CLOSE"  # Close long position
```

### Example: Options Trading

```python
# Single option order
order = client.create_limit_order(
    symbol="AAPL_012025C150",  # Jan 2025 $150 Call
    quantity=1,
    limit_price=5.50,
    instruction="BUY_TO_OPEN",
    position_effect="OPENING"
)

# Options spread (vertical call spread)
order = Order(
    orderType="NET_DEBIT",
    session="NORMAL",
    price=2.50,  # Net debit
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
```

### Complex Option Strategies

The library supports various complex strategies through `ComplexOrderStrategyType`:

- **COVERED** - Covered calls/puts
- **VERTICAL** - Vertical spreads (bull/bear)
- **CALENDAR** - Calendar/time spreads
- **DIAGONAL** - Diagonal spreads
- **STRADDLE** - Long/short straddles
- **STRANGLE** - Long/short strangles
- **BUTTERFLY** - Butterfly spreads
- **CONDOR** - Condor spreads
- **IRON_CONDOR** - Iron condors
- **COLLAR_WITH_STOCK** - Protective collars

### Options Chain Access

```python
# Get options chain
chain = client.get_options_chain(
    symbol="AAPL",
    contract_type="ALL",  # CALL, PUT, or ALL
    strike_count=10,
    include_quotes=True,
    from_date="2025-01-01",
    to_date="2025-02-01",
    strike=150.0,
    range="ITM"  # ITM, OTM, NTM, SAB, SBK, SNK, ALL
)
```

### Special Considerations

- **Approval Levels**: Options trading requires appropriate approval level
- **Margin Requirements**: Options strategies have specific margin requirements
- **Early Assignment Risk**: American-style options can be assigned before expiration
- **Expiration**: Options expire on specific dates (typically Fridays)
- **Contract Multiplier**: Standard options represent 100 shares

### Symbol Format
Options use OSI (Option Symbology Initiative) format:
`UNDERLYING_EXPIRATION(MMDDYY)C/P(STRIKE)`

Examples:
- `AAPL_012025C150` - Apple Jan 2025 $150 Call
- `SPY_121524P450` - SPY Dec 15, 2024 $450 Put

## Mutual Fund Trading

Mutual funds are professionally managed pooled investment vehicles that trade at end-of-day NAV (Net Asset Value).

### Key Features

- End-of-day pricing and execution
- Dollar-based or share-based orders
- Automatic dividend reinvestment
- Systematic investment plans
- No intraday trading

### Example: Mutual Fund Orders

```python
# Buy mutual fund by dollar amount
order = Order(
    orderType="MARKET",
    session="NORMAL",
    duration="DAY",
    orderStrategyType="SINGLE",
    orderLegCollection=[
        OrderLeg(
            instruction="BUY",
            quantity=5000.00,  # $5,000 investment
            quantityType="DOLLARS",
            instrument=Instrument(
                symbol="SWPPX",
                assetType="MUTUAL_FUND"
            )
        )
    ]
)

# Buy mutual fund by shares
order = Order(
    orderType="MARKET",
    session="NORMAL",
    duration="DAY",
    orderStrategyType="SINGLE",
    orderLegCollection=[
        OrderLeg(
            instruction="BUY",
            quantity=100,  # 100 shares
            quantityType="SHARES",
            instrument=Instrument(
                symbol="VFIAX",
                assetType="MUTUAL_FUND"
            )
        )
    ]
)
```

### Special Considerations

- **Minimum Investments**: Many funds have initial and subsequent minimums
- **Trading Cutoff**: Orders must be placed before market close (4 PM ET)
- **Settlement**: Mutual funds typically settle T+1
- **Fees**: Watch for front-end loads, back-end loads, and expense ratios
- **Redemption Fees**: Some funds charge fees for short-term trading

### Symbol Format
Standard fund tickers: `SWPPX`, `VFIAX`, `FXAIX`

## Fixed Income Trading

Fixed income securities include government bonds, corporate bonds, municipal bonds, and other debt instruments.

### Key Features

- Par value and yield-based trading
- Accrued interest calculations
- Maturity dates and call provisions
- Credit ratings consideration
- CUSIP-based identification

### Example: Bond Orders

```python
# Buy corporate bond
order = Order(
    orderType="LIMIT",
    price=98.50,  # As percentage of par
    session="NORMAL",
    duration="DAY",
    orderStrategyType="SINGLE",
    orderLegCollection=[
        OrderLeg(
            instruction="BUY",
            quantity=10,  # $10,000 par value
            instrument=Instrument(
                symbol="594918BW8",  # Microsoft bond CUSIP
                assetType="FIXED_INCOME",
                cusip="594918BW8"
            )
        )
    ]
)

# Buy Treasury note
order = client.create_limit_order(
    symbol="912828ZT0",  # 10-year Treasury CUSIP
    quantity=25,  # $25,000 par value
    limit_price=99.25,
    instruction="BUY"
)
```

### Bond Pricing

- Prices quoted as percentage of par value
- Accrued interest added to purchase price
- Yield calculations important for comparison

### Special Considerations

- **Minimum Denominations**: Often $1,000 or $5,000 minimums
- **Liquidity**: Corporate bonds may have limited liquidity
- **Credit Risk**: Consider ratings from Moody's, S&P, Fitch
- **Interest Rate Risk**: Bond prices inversely related to rates
- **Call Risk**: Some bonds can be redeemed early

### Symbol Format
CUSIP numbers (9 characters): `912828ZT0`, `594918BW8`

## Index Instruments

Market indices represent baskets of securities and serve as benchmarks but cannot be directly traded.

### Key Features

- Reference data only (not tradable)
- Real-time quotes available
- Used for market analysis
- Basis for derivatives (futures, options)

### Example: Index Data Access

```python
# Get index quotes
indices = client.get_quotes([
    "$SPX.X",    # S&P 500
    "$DJI",      # Dow Jones Industrial Average
    "$COMP.X",   # Nasdaq Composite
    "$RUT.X",    # Russell 2000
    "$VIX.X"     # CBOE Volatility Index
])

for symbol, data in indices.items():
    print(f"{symbol}: {data.quote.lastPrice}")
```

### Common Indices

- **$SPX.X** - S&P 500 Index
- **$DJI** - Dow Jones Industrial Average
- **$COMP.X** - Nasdaq Composite
- **$NDX.X** - Nasdaq 100
- **$RUT.X** - Russell 2000
- **$VIX.X** - CBOE Volatility Index

### Special Considerations

- Cannot place orders for indices directly
- Use ETFs (SPY, QQQ) or futures for index exposure
- Index options available for some indices
- Different data vendors may use different symbols

## Cash Equivalents

Cash equivalents include money market funds and similar highly liquid, low-risk instruments.

### Key Features

- Stable NAV (typically $1.00)
- Daily accrual of interest
- High liquidity
- Low risk profile
- Sweep account options

### Example: Money Market Orders

```python
# Buy money market fund
order = client.create_market_order(
    symbol="SWVXX",  # Schwab Value Advantage Money Fund
    quantity=10000,  # $10,000
    instruction="BUY"
)
```

### Special Considerations

- Used for cash management
- May be default sweep vehicle
- Consider expense ratios
- Not FDIC insured (but typically very safe)

## Currency (Forex) Trading

Foreign exchange trading involves currency pairs and operates 24/5.

### Key Features

- Currency pair trading
- 24-hour market (Sunday-Friday)
- Leverage availability
- Pip-based pricing
- Major, minor, and exotic pairs

### Example: Forex Orders

```python
# Buy EUR/USD
order = Order(
    orderType="MARKET",
    session="NORMAL",
    duration="DAY",
    orderStrategyType="SINGLE",
    orderLegCollection=[
        OrderLeg(
            instruction="BUY",
            quantity=10000,  # 10,000 EUR
            instrument=Instrument(
                symbol="EUR/USD",
                assetType="CURRENCY"
            )
        )
    ]
)

# Limit order for GBP/JPY
order = client.create_limit_order(
    symbol="GBP/JPY",
    quantity=5000,
    limit_price=195.50,
    instruction="SELL"
)
```

### Major Currency Pairs

- **EUR/USD** - Euro/US Dollar
- **GBP/USD** - British Pound/US Dollar
- **USD/JPY** - US Dollar/Japanese Yen
- **USD/CHF** - US Dollar/Swiss Franc
- **AUD/USD** - Australian Dollar/US Dollar
- **USD/CAD** - US Dollar/Canadian Dollar

### Special Considerations

- **Leverage**: Forex typically offers high leverage
- **Spreads**: Watch bid-ask spreads
- **Roll Over**: Positions held overnight may incur charges
- **Volatility**: Currency markets can be highly volatile

## Order Type Compatibility Matrix

Not all order types are available for all asset classes:

| Order Type | Equity | Options | Mutual Fund | Fixed Income | Currency | Index |
|------------|--------|---------|-------------|--------------|----------|-------|
| MARKET | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| LIMIT | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ |
| STOP | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ |
| STOP_LIMIT | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ |
| TRAILING_STOP | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| MARKET_ON_CLOSE | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| LIMIT_ON_CLOSE | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| NET_DEBIT | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| NET_CREDIT | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |

## Trading Hours by Asset Class

Different asset classes have different trading hours:

### Regular Trading Hours

- **Equity**: 9:30 AM - 4:00 PM ET
  - Pre-market: 7:00 AM - 9:30 AM ET
  - After-hours: 4:00 PM - 8:00 PM ET
- **Options**: 9:30 AM - 4:00 PM ET (some until 4:15 PM)
- **Mutual Funds**: Orders accepted until 4:00 PM ET
- **Fixed Income**: 8:00 AM - 5:00 PM ET (varies by instrument)
- **Currency**: 24 hours, 5 PM ET Sunday - 5 PM ET Friday

### Session Types

```python
# Session types for orders
NORMAL = "NORMAL"           # Regular trading hours
AM = "AM"                   # Pre-market session
PM = "PM"                   # After-hours session
SEAMLESS = "SEAMLESS"       # All sessions
```

## Best Practices by Asset Type

### General Best Practices

1. **Verify Asset Type**: Always ensure the correct asset type is specified
2. **Check Market Hours**: Be aware of trading hours for each asset class
3. **Understand Symbols**: Use correct symbol format for each asset type
4. **Review Order Types**: Confirm order type is supported for the asset
5. **Consider Liquidity**: Some assets have better liquidity at certain times
6. **Account Permissions**: Ensure account has appropriate trading permissions

### Asset-Specific Tips

#### Equity
- Use limit orders in pre/post market for better price control
- Consider liquidity when trading small-cap stocks
- Be aware of dividend dates for dividend capture strategies

#### Options
- Always check implied volatility before trading
- Understand the Greeks for your positions
- Be aware of early assignment risk for ITM options
- Consider time decay (theta) for long positions

#### Mutual Funds
- Place orders before 4 PM ET cutoff
- Consider expense ratios in total return calculations
- Understand any redemption fees or holding periods

#### Fixed Income
- Compare yields across similar securities
- Understand credit ratings and risks
- Consider duration for interest rate sensitivity
- Factor in accrued interest for settlements

#### Currency
- Monitor economic calendars for volatility events
- Understand pip values for position sizing
- Be aware of weekend gaps
- Consider correlation between pairs

## Error Handling for Asset Types

```python
from schwab.models.order_validation import OrderValidationError

try:
    # Attempt to place order
    order = client.create_limit_order(
        symbol="INVALID",
        quantity=100,
        limit_price=50.00,
        instruction="BUY"
    )
    client.place_order(account_number, order)
    
except OrderValidationError as e:
    if "Invalid symbol" in str(e):
        print("Symbol not found or invalid for asset type")
    elif "Order type not supported" in str(e):
        print("This order type is not available for this asset")
    elif "Market closed" in str(e):
        print("Market is closed for this asset type")
    else:
        print(f"Order validation failed: {e}")
```

## Additional Resources

- [Order Types Tutorial](ORDER_TYPES_TUTORIAL.md) - Detailed order type guide
- [Order Strategies](ORDER_STRATEGIES.md) - Complex order strategies
- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Paper Trading Guide](PAPER_TRADING.md) - Test strategies safely