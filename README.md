# Schwab Trader

A comprehensive Python library for Charles Schwab's Trading API with full support for account management, order execution, real-time streaming, and portfolio analytics.

[![PyPI version](https://badge.fury.io/py/schwab-trader.svg)](https://badge.fury.io/py/schwab-trader)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Disclaimer

**USE AT YOUR OWN RISK.** This software is provided "AS IS" without warranties. The authors are not liable for trading losses, bugs, or technical issues. Trading involves substantial risk. Always verify trades and maintain proper risk management. See [DISCLAIMER.md](docs/DISCLAIMER.md) for full terms.

## Features

- **Complete Trading API** - All order types: market, limit, stop, trailing stop, OCO, brackets
- **Real-time Streaming** - WebSocket streaming for quotes, order book, and account activity
- **Portfolio Management** - Multi-account tracking, position management, execution history
- **Type Safety** - Full Pydantic models with validation
- **Async Support** - Both synchronous and asynchronous clients
- **Paper Trading** - Safety features for paper trading accounts

## Installation

```bash
pip install schwab-trader
```

**From source:**
```bash
git clone https://github.com/ibouazizi/schwab-trader.git
cd schwab-trader
pip install -e .
```

## Quick Start

### Authentication Setup

```python
from schwab import SchwabAuth, SchwabClient

# Initialize auth and get authorization URL
auth = SchwabAuth(
    client_id="your_client_id",
    client_secret="your_client_secret",
    redirect_uri="https://localhost:8443/callback"
)

# Open this URL in browser, authorize, and get the callback URL
print(auth.get_authorization_url())

# Exchange authorization code for tokens
auth.exchange_code_for_tokens("authorization_code_from_callback")

# Create client with authenticated session
client = SchwabClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    redirect_uri="https://localhost:8443/callback",
    auth=auth
)
```

### Account Information

```python
# Get all account numbers
accounts = client.get_account_numbers()
for acc in accounts.accounts:
    print(f"Account: {acc.account_number}, Hash: {acc.hash_value}")

# Get account with positions
account = client.get_account(account_hash, include_positions=True)
```

### Placing Orders

```python
from schwab.models.generated.trading_models import Instruction as OrderInstruction

# Market order
order = client.create_market_order(
    symbol="AAPL",
    quantity=10,
    instruction=OrderInstruction.BUY
)
client.place_order(account_hash, order)

# Limit order
order = client.create_limit_order(
    symbol="AAPL",
    quantity=10,
    limit_price=150.00,
    instruction=OrderInstruction.BUY
)
client.place_order(account_hash, order)

# Stop-loss order
order = client.create_stop_order(
    symbol="AAPL",
    quantity=10,
    stop_price=140.00,
    instruction=OrderInstruction.SELL
)
client.place_order(account_hash, order)
```

### Order Management

```python
from datetime import datetime, timedelta

# Get recent orders
orders = client.get_orders(
    account_number=account_hash,
    from_entered_time=datetime.now() - timedelta(days=7),
    to_entered_time=datetime.now()
)

# Cancel an order
client.cancel_order(account_hash, order_id)

# Replace an order
new_order = client.create_limit_order("AAPL", 10, 155.00, OrderInstruction.BUY)
client.replace_order(account_hash, order_id, new_order)
```

### Market Data

```python
# Get quotes
quotes = client.get_quotes(["AAPL", "MSFT", "GOOGL"])

# Get price history
history = client.get_price_history(
    symbol="AAPL",
    period_type="day",
    period=10,
    frequency_type="minute",
    frequency=5
)

# Get option chain
options = client.get_option_chain(
    symbol="AAPL",
    contract_type="CALL",
    strike_count=10
)
```

### Async Usage

```python
import asyncio
from schwab import AsyncSchwabClient

async def main():
    async with AsyncSchwabClient(
        client_id="your_client_id",
        client_secret="your_client_secret",
        redirect_uri="https://localhost:8443/callback",
        auth=auth
    ) as client:
        accounts = await client.get_account_numbers()
        quotes = await client.get_quotes(["AAPL"])

asyncio.run(main())
```

### Portfolio Management

```python
from schwab import PortfolioManager

# Initialize portfolio manager
portfolio = PortfolioManager(client)

# Add accounts to track
portfolio.add_account(account_hash)

# Get portfolio summary
summary = portfolio.get_portfolio_summary()
print(f"Total Value: ${summary['total_value']:,.2f}")

# Get all positions
positions = portfolio.get_all_positions()
```

### Real-time Streaming

```python
from schwab.streaming import StreamerClient

async def on_quote(data):
    print(f"Quote update: {data}")

streamer = StreamerClient(client)
await streamer.connect()
await streamer.subscribe_level_one_equities(["AAPL", "MSFT"], callback=on_quote)
```

## Example Applications

The `examples/` directory contains ready-to-run applications:

| Script | Description |
|--------|-------------|
| `portfolio_gui.py` | Full-featured GUI for portfolio management |
| `account_overview.py` | Terminal-based account dashboard |
| `live_quotes.py` | Real-time quote monitor |
| `streaming_demo.py` | Streaming API demonstration |
| `level2_order_book.py` | Level 2 order book visualization |
| `options_greeks_monitor.py` | Options Greeks tracking |
| `paper_trading_demo.py` | Paper trading example |

**Run examples:**
```bash
# Setup credentials first
python -m examples.setup_credentials
python -m examples.setup_oauth

# Run GUI
python -m examples.portfolio_gui

# Run terminal apps
python -m examples.account_overview
python -m examples.live_quotes
```

## Supported Order Types

| Type | Description |
|------|-------------|
| Market | Execute immediately at market price |
| Limit | Execute at specified price or better |
| Stop | Trigger market order when price reached |
| Stop-Limit | Trigger limit order when price reached |
| Trailing Stop | Dynamic stop that follows price |
| Market-on-Close | Execute at market close |
| Limit-on-Close | Execute at close if limit met |
| OCO | One-Cancels-Other linked orders |
| OTO | One-Triggers-Other sequential orders |
| Bracket | Entry with stop-loss and take-profit |

## Documentation

- [API Reference](docs/API.md) - Complete API documentation
- [Order Types Tutorial](docs/ORDER_TYPES_TUTORIAL.md) - Guide to order types
- [Order Strategies](docs/ORDER_STRATEGIES.md) - Complex order strategies
- [Paper Trading](docs/PAPER_TRADING.md) - Paper trading guide
- [Implementation Status](IMPLEMENTATION.md) - Feature status and roadmap

## Requirements

- Python 3.9+
- Charles Schwab developer account with API access
- OAuth application credentials

## Dependencies

- `requests` - HTTP client
- `pydantic` - Data validation
- `aiohttp` - Async HTTP client
- `python-dateutil` - Date handling

## Contributing

Contributions welcome! See [IMPLEMENTATION.md](IMPLEMENTATION.md) for priority areas:

1. Async client completion
2. Test coverage improvements
3. Streaming validation
4. Documentation enhancements

```bash
# Development setup
pip install -e ".[dev]"

# Run tests
pytest tests/

# Code formatting
black schwab/
isort schwab/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [PyPI Package](https://pypi.org/project/schwab-trader/)
- [GitHub Repository](https://github.com/ibouazizi/schwab-trader)
- [Schwab Developer Portal](https://developer.schwab.com/)
