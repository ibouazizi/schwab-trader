# Schwab API Python Library

A comprehensive Python library for interacting with Charles Schwab's Trading API. This library provides a clean, type-safe, and Pythonic interface to Schwab's RESTful trading API, supporting both synchronous and asynchronous operations.

## ⚠️ Important Disclaimer

**USE THIS SOFTWARE AT YOUR OWN RISK**. This software is provided "AS IS" without any warranties or guarantees. The authors and contributors:
- Are NOT liable for any trading losses, missed opportunities, or other financial damages
- Do NOT provide financial, investment, or trading advice
- Are NOT responsible for bugs, downtime, or technical issues that may affect trading
- Make NO guarantees about the accuracy or reliability of the software

By using this software, you acknowledge that trading involves substantial risk and that you may lose part or all of your investment. For complete terms, please read our [full disclaimer](docs/DISCLAIMER.md).

**Always verify your trades and maintain proper risk management practices.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Overview

The Schwab API Python Library offers a complete suite of trading and account management capabilities:

### Core Features
- **Account Management**: Access account details, positions, balances, and trading history
- **Order Management**: Create, modify, and cancel various types of orders
- **Real-time Data**: Stream live market quotes and order status updates
- **Portfolio Analysis**: Track positions, performance metrics, and account allocation
- **OAuth Authentication**: Secure authentication using OAuth 2.0 flow
- **Rate Limiting**: Smart rate limiting to comply with API restrictions
- **Error Handling**: Comprehensive error handling and validation

### Technical Highlights
- Type-safe implementation using Pydantic models
- Both synchronous and asynchronous API support
- Automatic token refresh and session management
- Configurable retry mechanisms with exponential backoff
- Extensive logging and debugging capabilities
- Comprehensive test coverage

### Supported Order Types
- Market Orders
- Limit Orders
- Stop Orders
- Stop-Limit Orders
- Trailing Stop Orders
- Market-on-Close Orders
- Limit-on-Close Orders
- Extended Hours Trading

### Real-time Data Features
- Live market quotes
- Order status updates
- Position updates
- Account balance updates
- Trading notifications

## Installation

### From PyPI (Recommended)

```bash
pip install schwab-trader
```

### From Source

1. Clone the repository:
```bash
git clone https://github.com/ibouazizi/schwab-trader.git
cd schwab-trader
```

2. Install in development mode:
```bash
pip install -e .
```

### Build from Source

1. Clone the repository:
```bash
git clone https://github.com/ibouazizi/schwab-trader.git
cd schwab-trader
```

2. Install build dependencies:
```bash
pip install build wheel
```

3. Build the package:
```bash
python -m build
```

This will create two files in the `dist` directory:
- A source distribution (`.tar.gz`)
- A wheel distribution (`.whl`)

4. Install the built package:
```bash
pip install dist/schwab-trader-*.whl
```

### Development Installation

For development, you might want to install additional dependencies:

```bash
pip install -e ".[dev]"
```

This will install the package in editable mode along with development dependencies.

## Features

- Complete coverage of Schwab's Trading API endpoints
- Type hints and data validation using Pydantic models
- Both synchronous and asynchronous API support
- Comprehensive error handling
- Easy-to-use interface for account management and trading

## Quick Start

```python
from schwab import SchwabClient

# Initialize the client
client = SchwabClient(api_key="your_api_key")

# Get account numbers
accounts = client.get_account_numbers()

# Get account details
account_details = client.get_account_details(account_number="encrypted_account_number")

# Get positions for an account
account = client.get_account(account_number="encrypted_account_number", include_positions=True)

# Create and place different types of orders

## Market Order
# Simple market order to buy 100 shares of AAPL
order = client.create_market_order(
    symbol="AAPL",
    quantity=100,
    instruction=OrderInstruction.BUY,
    description="APPLE INC"
)
client.place_order(account_number="encrypted_account_number", order=order)

## Limit Order
# Buy 100 shares of AAPL with a limit price of $150
order = client.create_limit_order(
    symbol="AAPL",
    quantity=100,
    limit_price=150.00,
    instruction=OrderInstruction.BUY,
    description="APPLE INC"
)
client.place_order(account_number="encrypted_account_number", order=order)

## Stop Order
# Sell 100 shares of AAPL if price falls below $140
order = client.create_stop_order(
    symbol="AAPL",
    quantity=100,
    stop_price=140.00,
    instruction=OrderInstruction.SELL,
    description="APPLE INC"
)
client.place_order(account_number="encrypted_account_number", order=order)

## Stop-Limit Order
# Sell 100 shares of AAPL if price falls below $140, but not less than $138
order = client.create_stop_limit_order(
    symbol="AAPL",
    quantity=100,
    stop_price=140.00,
    limit_price=138.00,
    instruction=OrderInstruction.SELL,
    description="APPLE INC"
)
client.place_order(account_number="encrypted_account_number", order=order)

## Trailing Stop Order
# Sell 100 shares of AAPL with a $5 trailing stop
order = client.create_trailing_stop_order(
    symbol="AAPL",
    quantity=100,
    stop_price_offset=5.00,
    instruction=OrderInstruction.SELL,
    description="APPLE INC"
)
client.place_order(account_number="encrypted_account_number", order=order)

## Market-on-Close Order
# Buy 100 shares of AAPL at market price at market close
order = client.create_market_on_close_order(
    symbol="AAPL",
    quantity=100,
    instruction=OrderInstruction.BUY,
    description="APPLE INC"
)
client.place_order(account_number="encrypted_account_number", order=order)

## Limit-on-Close Order
# Buy 100 shares of AAPL at market close if price is at or below $150
order = client.create_limit_on_close_order(
    symbol="AAPL",
    quantity=100,
    limit_price=150.00,
    instruction=OrderInstruction.BUY,
    description="APPLE INC"
)
client.place_order(account_number="encrypted_account_number", order=order)

# Order Management

## Get Order Status
from datetime import datetime, timedelta

# Get all orders from the last 7 days
orders = client.get_orders(
    account_number="encrypted_account_number",
    from_entered_time=datetime.now() - timedelta(days=7),
    to_entered_time=datetime.now(),
    status="WORKING"  # Optional status filter
)

# Get a specific order by ID
order = client.get_order(
    account_number="encrypted_account_number",
    order_id=12345
)

## Modify Orders

# Replace an existing order
original_order = client.get_order(
    account_number="encrypted_account_number",
    order_id=12345
)

# Create a new order with modified parameters
modified_order = client.create_limit_order(
    symbol="AAPL",
    quantity=100,
    limit_price=155.00,  # New price
    instruction=OrderInstruction.BUY,
    description="APPLE INC"
)

# Replace the order
client.replace_order(
    account_number="encrypted_account_number",
    order_id=12345,
    new_order=modified_order
)

## Cancel Orders

# Cancel a specific order
client.cancel_order(
    account_number="encrypted_account_number",
    order_id=12345
)
```

### Async Usage

```python
import asyncio
from schwab import AsyncSchwabClient

async def main():
    async with AsyncSchwabClient(api_key="your_api_key") as client:
        # Get account numbers
        accounts = await client.get_account_numbers()
        
        # Get account details with positions
        account = await client.get_account(
            account_number="encrypted_account_number",
            include_positions=True
        )
        
        # Place an order
        order = Order(...)  # Same order structure as sync example
        await client.place_order(
            account_number="encrypted_account_number",
            order=order
        )
        
        # Get all orders
        orders = await client.get_orders(
            account_number="encrypted_account_number",
            from_entered_time=datetime.now() - timedelta(days=7),
            to_entered_time=datetime.now()
        )
        
        # Get a specific order
        order = await client.get_order(
            account_number="encrypted_account_number",
            order_id=12345
        )
        
        # Replace an order
        modified_order = client.create_limit_order(
            symbol="AAPL",
            quantity=100,
            limit_price=155.00,
            instruction=OrderInstruction.BUY,
            description="APPLE INC"
        )
        await client.replace_order(
            account_number="encrypted_account_number",
            order_id=12345,
            new_order=modified_order
        )
        
        # Cancel an order
        await client.cancel_order(
            account_number="encrypted_account_number",
            order_id=12345
        )

if __name__ == "__main__":
    asyncio.run(main())
```

## Example Scripts

The library comes with several example scripts demonstrating its capabilities:

### Account Overview (`examples/account_overview.py`)
A comprehensive account monitoring tool that provides:
- Account balances and cash positions
- Current equity positions with P&L tracking
- Open orders status
- Portfolio allocation analysis
- Real-time position valuation
- Performance metrics

Features:
- OAuth authentication flow
- Formatted tabular output
- Color-coded profit/loss display
- Automatic data refresh
- Multi-account support

### Live Quotes Monitor (`examples/live_quotes.py`)
A real-time stock quote monitoring tool that provides:
- Live price updates
- Bid/Ask spreads
- Trading volume
- Price change tracking
- Color-coded price movements

Features:
- Asynchronous data streaming
- Automatic token refresh
- Rate-limited API calls
- Clean console interface
- Configurable symbol list
- Graceful error handling

### Direct API Access (`examples/account_overview_direct.py`)
A demonstration of direct API access without the client wrapper, showing:
- Raw API endpoint usage
- Manual authentication handling
- Direct response processing
- Error handling patterns

### Streaming Demo (`examples/streaming_demo.py`)
Comprehensive demonstration of all streaming capabilities:
- Level 1 equity quotes with bid/ask spreads
- Level 2 order book depth with market maker tracking
- Options quotes with real-time Greeks (Delta, Gamma, Theta, Vega, Rho)
- Real-time news headlines and alerts
- Account activity monitoring (fills, orders, etc.)
- Chart data streaming (OHLCV bars)
- Automatic reconnection handling

### Level 2 Order Book Monitor (`examples/level2_order_book.py`)
Advanced order book visualization tool:
- Real-time bid/ask depth display
- Market maker identification
- Spread and mid-price calculations
- Book imbalance indicators
- Top-of-book statistics
- Market microstructure analysis

### Options Greeks Monitor (`examples/options_greeks_monitor.py`)
Real-time options analytics dashboard:
- Live options quotes with full Greeks
- Implied volatility tracking
- P&L scenario analysis
- Portfolio-level Greeks aggregation
- Moneyness and value breakdown
- Risk metrics visualization

## Documentation

For detailed documentation, please visit [docs/](docs/). Key documentation files:

- [API.md](docs/API.md): Complete API reference and usage examples
- [NEW_FEATURES.md](docs/NEW_FEATURES.md): Latest features and improvements
- [API_REFERENCE.md](docs/API_REFERENCE.md): Detailed API endpoint documentation
- [ORDER_STRATEGIES.md](docs/ORDER_STRATEGIES.md): Complex order strategies guide
- [ORDER_TYPES_TUTORIAL.md](docs/ORDER_TYPES_TUTORIAL.md): Tutorial on different order types
- [PAPER_TRADING.md](docs/PAPER_TRADING.md): Paper trading implementation guide
- [ASSET_TYPES.md](docs/ASSET_TYPES.md): Supported asset types reference

## TODO: Feature Implementation Status

### Summary of Implemented Features

✅ **Fully Implemented Categories:**
- All Trading API Features
- All Market Data API Features  
- All Portfolio & Account Features
- Streaming Infrastructure (with message format issue)

⚠️ **Partially Implemented:**
- Streaming/WebSocket (works but needs correct message format from Schwab docs)
- Order Management (complex strategies and conditional orders done)
- Data and Calculations (performance, tax lots, dividends done)

❌ **Not Implemented:**
- Portfolio GUI enhancements
- Paper Trading reset/creation
- Some auxiliary features

### Detailed Feature Status

### Trading API Features
- [x] **Preview Order** (`/accounts/{accountNumber}/previewOrder`) - Preview order before placement ✅
- [x] **Transaction History** (`/accounts/{accountNumber}/transactions`) - Get detailed transaction history ✅
- [x] **Get Specific Transaction** (`/accounts/{accountNumber}/transactions/{transactionId}`) - Get details of a specific transaction ✅
- [x] **User Preferences** (`/userPreference`) - Get and update user trading preferences ✅
- [x] **All Orders Across Accounts** (`/orders`) - Get orders for all linked accounts ✅

### Market Data API Features
- [x] **Price History** (`/pricehistory`) - Get historical price data for charting ✅
- [x] **Market Hours** (`/markets` and `/markets/{market_id}`) - Get market hours and status ✅
- [x] **Movers** (`/movers/{symbol_id}`) - Get top market movers ✅
- [x] **Instrument Search** (`/instruments`) - Search for tradable instruments ✅
- [x] **Get Instrument by CUSIP** (`/instruments/{cusip_id}`) - Get instrument details by CUSIP ✅

### Portfolio & Account Features
- [x] **Multi-leg Options Orders** - Complex options strategies (spreads, straddles, etc.) ✅
- [x] **Conditional Orders** - One-cancels-other (OCO), one-triggers-other (OTO) ✅
- [x] **Bracket Orders** - Automatic profit target and stop loss orders ✅
- [x] **Advanced Position Analysis** - Greeks aggregation, portfolio beta, sector allocation ✅
- [x] **Tax Lot Selection** - Specific tax lot selection for closing positions ✅
- [x] **Cost Basis Tracking** - Detailed cost basis and tax implications ✅
- [x] **Dividend Tracking** - Dividend history and projections ✅
- [x] **Account Performance Metrics** - Time-weighted returns, benchmarking ✅

### Streaming & Real-time Features
- [x] **Level II Data Streaming** - Full order book depth ✅
- [x] **Options Streaming** - Real-time options quotes and Greeks ✅
- [x] **News Streaming** - Real-time news headlines and stories ✅
- [x] **Account Activity Streaming** - Real-time account updates and fills ✅
- [x] **Chart Data Streaming** - Real-time chart data updates ✅

### Known Streaming Issues
- [ ] **WebSocket Message Format** - Streaming connection fails with "Bad command formatting" error
- [ ] **Requires Official Documentation** - Need Schwab's streaming API documentation for correct message format
- [ ] **Authentication Works** - Connection and auth setup work, only message format is incorrect

### Paper Trading Limitations
- [ ] **Reset Paper Account** - `reset()` and `reset_account()` methods raise `NotImplementedError`
- [ ] **Account Creation** - Cannot create new paper trading accounts programmatically
- [ ] **Historical Performance** - No historical performance tracking for paper accounts
- [ ] **Multiple Paper Accounts** - Limited support for multiple paper trading strategies

### Streaming/WebSocket Features
- [x] **Full Streaming Implementation** - WebSocket streaming client fully implemented ✅
- [x] **Automatic Reconnection** - Automatic reconnection with exponential backoff ✅
- [x] **Subscription Management** - Comprehensive subscription management for all data types ✅
- [x] **Level 2 Data** - Full Level 2 market data streaming with order book depth ✅
- [x] **News Streaming** - NEWS_HEADLINE and NEWS_STORY services implemented ✅

### Portfolio GUI Limitations
- [ ] **Order Modification** - Currently shows "not yet implemented" message
- [ ] **Transaction History View** - Currently shows "not yet implemented" message  
- [ ] **Real-time Chart Updates** - Charts don't update with real-time streaming data
- [ ] **Technical Indicators** - No technical indicators on charts (RSI, MACD, etc.)
- [ ] **Drawing Tools** - No chart drawing tools (trend lines, annotations)
- [ ] **Multiple Chart Layouts** - Cannot display multiple charts simultaneously
- [ ] **Export Functionality** - Limited export options for portfolio data

### Data and Calculations
- [x] **Historical Performance Metrics** - Account performance calculation implemented ✅
- [ ] **Risk Metrics** - No Value at Risk (VaR), Sharpe ratio calculations (currently placeholder)
- [x] **Tax Lot Tracking** - Tax lot retrieval and specific lot selection implemented ✅
- [x] **Dividend Tracking** - Dividend history retrieval implemented ✅
- [ ] **Corporate Actions** - No handling of splits, mergers, or other corporate actions
- [ ] **Portfolio Optimization** - No mean-variance optimization or efficient frontier
- [ ] **Backtesting Framework** - No built-in backtesting capabilities

### Order Management
- [x] **Complex Order Strategies** - Multi-leg options orders implemented ✅
- [x] **Conditional Orders** - OCO (one-cancels-other) and OTO (one-triggers-other) implemented ✅
- [ ] **Basket Orders** - Cannot place multiple orders as a basket
- [ ] **Order Templates** - No saved order templates or favorites
- [ ] **Algorithmic Orders** - No VWAP, TWAP, or other algorithmic order types
- [ ] **Pre/Post Market Orders** - Limited extended hours trading support

### Authentication & Security
- [ ] **Multi-Account OAuth** - Limited support for multiple account authentication
- [ ] **Token Management UI** - No GUI for managing OAuth tokens
- [ ] **Biometric Authentication** - No support for biometric authentication
- [ ] **Session Management** - Basic session management, no advanced features

### Mock/Placeholder Data
- [ ] **Watchlist Symbols** - Initially populated with dummy price data (0, 0, 0)
- [ ] **Performance Metrics** - Day change and Sharpe ratio are placeholders
- [ ] **Chart Data Generation** - OHLCV data is generated from line data when not available
- [ ] **Risk Analytics** - Risk metrics show placeholder values

### Infrastructure & Quality
- [ ] **Comprehensive Test Coverage** - Many tests need updating for new model structure
- [ ] **AsyncSchwabClient** - Async client is incomplete (missing many methods from sync client)
- [ ] **Rate Limiting** - Basic implementation, needs enhancement for production use
- [ ] **Retry Logic** - Simple retry mechanism, needs circuit breaker pattern
- [ ] **Caching Layer** - No caching for frequently accessed data
- [ ] **Logging Configuration** - Basic logging, needs structured logging
- [ ] **Error Handling** - Some API errors not properly parsed or categorized

### Documentation & Examples
- [ ] **API Reference** - Incomplete API documentation
- [ ] **Trading Strategies** - No example trading strategies
- [ ] **Integration Guides** - No guides for integrating with other tools
- [ ] **Performance Optimization** - No optimization guidelines
- [ ] **Troubleshooting Guide** - Limited troubleshooting documentation

## Known Issues & Limitations

- **Option Chain Data**: The option chain functionality is newly implemented and may need adjustments based on actual API response formats
- **Test Suite**: Many tests need updating after recent model changes to use generated Pydantic models
- **Error Messages**: Some error messages from the API may not be properly parsed or displayed
- **Rate Limiting**: Current implementation is basic and may need enhancement for heavy usage
- **WebSocket Reconnection**: Streaming client may need manual restart on connection loss

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. Priority areas for contribution:
1. Implementing TODO items listed above
2. Improving test coverage
3. Enhancing documentation
4. Adding more examples
5. Performance optimizations

## License

This project is licensed under the MIT License - see the LICENSE file for details.
