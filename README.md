# Schwab API Python Library

A comprehensive Python library for interacting with Charles Schwab's Trading API. This library provides a clean, type-safe, and Pythonic interface to Schwab's RESTful trading API, supporting both synchronous and asynchronous operations.

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
pip install schwab-api
```

### From Source

1. Clone the repository:
```bash
git clone https://github.com/openhands/schwab-api.git
cd schwab-api
```

2. Install in development mode:
```bash
pip install -e .
```

### Build from Source

1. Clone the repository:
```bash
git clone https://github.com/openhands/schwab-api.git
cd schwab-api
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
pip install dist/schwab_api-*.whl
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

## Documentation

For detailed documentation, please visit [docs/](docs/). Key documentation files:

- [API.md](docs/API.md): Complete API reference and usage examples
- [NEW_FEATURES.md](docs/NEW_FEATURES.md): Latest features and improvements

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
