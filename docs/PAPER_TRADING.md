# Paper Trading Guide

This comprehensive guide covers the paper trading features of the Schwab Trader library, allowing you to test strategies safely without risking real money.

## Table of Contents
1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Paper Trading Client](#paper-trading-client)
4. [Safety Features](#safety-features)
5. [Account Management](#account-management)
6. [Technical Indicators](#technical-indicators)
7. [Strategy Development](#strategy-development)
8. [Portfolio Integration](#portfolio-integration)
9. [Best Practices](#best-practices)
10. [Examples](#examples)

## Overview

Paper trading allows you to:
- Test strategies without financial risk
- Practice order placement and management
- Evaluate trading ideas with real market data
- Build confidence before live trading

The Schwab Trader library provides specialized paper trading clients with:
- Visual indicators for paper trading mode
- Safety checks to prevent accidental real trades
- Full API compatibility with live trading
- Built-in technical indicators
- Comprehensive account management

## Getting Started

### Prerequisites

1. **Schwab Account**: You need a Schwab brokerage account
2. **Paper Trading Access**: Contact Schwab to enable paper trading
3. **API Credentials**: Same credentials work for both paper and live trading

### Installation

```bash
pip install schwab-trader
```

### Basic Setup

```python
from schwab.auth import SchwabAuth
from schwab.paper_trading import PaperTradingClient

# Initialize authentication
auth = SchwabAuth(
    client_id="your_client_id",
    client_secret="your_client_secret",
    redirect_uri="https://localhost:8080/callback"
)

# Create paper trading client
paper_client = PaperTradingClient(auth=auth)

# Visual indicator shows paper trading is active
print("Paper trading mode active")
```

## Paper Trading Client

### PaperTradingClient

The synchronous paper trading client extends `SchwabClient` with safety features.

```python
from schwab.paper_trading import PaperTradingClient

# Initialize client
client = PaperTradingClient(auth=auth)

# All operations show visual indicators
order = client.create_market_order(
    symbol="AAPL",
    quantity=100,
    instruction="BUY"
)

# Place order - shows paper trading indicator
result = client.place_order(paper_account_number, order)
# Output: [PAPER TRADING] Order placed successfully for 100 shares of AAPL

# Get account info with visual indicators
account = client.get_account(paper_account_number, include_positions=True)
# Output: [PAPER TRADING] Retrieved account details
```

### AsyncPaperTradingClient

For asynchronous operations:

```python
import asyncio
from schwab.paper_trading import AsyncPaperTradingClient

async def paper_trade():
    async with AsyncPaperTradingClient(auth=auth) as client:
        # Get accounts
        accounts = await client.get_account_numbers()
        
        # Filter paper accounts
        paper_accounts = [a for a in accounts if is_paper_account(a)]
        
        # Place order
        order = client.create_limit_order(
            symbol="MSFT",
            quantity=50,
            limit_price=350.00,
            instruction="BUY"
        )
        
        await client.place_order(paper_accounts[0].accountNumber, order)
        # Output: [PAPER TRADING] Order placed successfully

asyncio.run(paper_trade())
```

## Safety Features

### Automatic Account Detection

The paper trading client automatically detects account types:

```python
from schwab.paper_trading.account import PaperAccountManager

# Initialize manager
manager = PaperAccountManager(client)

# Check if account is paper
account_number = "12345678"
if manager.is_paper_account(account_number):
    print(f"Account {account_number} is a paper trading account")
else:
    print(f"Account {account_number} is a REAL account - be careful!")

# Get account type
account_type = manager.detect_account_type(account_number)
print(f"Account type: {account_type}")  # "paper" or "real"
```

### Visual Indicators

All paper trading operations include clear visual indicators:

```python
from schwab.paper_trading import PaperTradingIndicator

# Show paper trading status
PaperTradingIndicator.show()
# Output: 
# ════════════════════════════════════════
#          PAPER TRADING MODE
# ════════════════════════════════════════

# Format messages with indicator
message = PaperTradingIndicator.format_message("Order filled")
print(message)
# Output: [PAPER TRADING] Order filled
```

### Safety Decorators

The library uses decorators to ensure paper trading safety:

```python
@paper_trading_check
def place_order(self, account_number: str, order: Order):
    # Decorator ensures this is a paper account
    # Raises exception if trying to trade on real account
    pass
```

## Account Management

### Finding Paper Accounts

```python
# Get all accounts
all_accounts = client.get_account_numbers()

# Filter paper accounts manually
paper_accounts = []
for account in all_accounts:
    account_details = client.get_account(account.accountNumber)
    # Paper accounts often have specific characteristics
    # Check account type, balance, or naming convention
    if is_paper_trading_account(account_details):
        paper_accounts.append(account)

print(f"Found {len(paper_accounts)} paper trading accounts")
```

### Account Information

```python
# Get paper account details
for paper_account in paper_accounts:
    account = client.get_account(
        paper_account.accountNumber,
        include_positions=True
    )
    
    print(f"\nPaper Account: {paper_account.accountNumber}")
    print(f"Account Value: ${account.securitiesAccount.currentBalances.accountValue:,.2f}")
    print(f"Cash Balance: ${account.securitiesAccount.currentBalances.cashBalance:,.2f}")
    print(f"Buying Power: ${account.securitiesAccount.currentBalances.buyingPower:,.2f}")
    
    # Show positions
    if account.securitiesAccount.positions:
        print("\nPositions:")
        for position in account.securitiesAccount.positions:
            print(f"  {position.instrument.symbol}: {position.longQuantity} shares @ ${position.averagePrice}")
```

## Technical Indicators

The paper trading module includes built-in technical indicators for strategy development:

### RSI (Relative Strength Index)

```python
from schwab.paper_trading.indicators import RSI

# Create RSI indicator
rsi = RSI(period=14)

# Calculate RSI from price data
prices = [100, 102, 101, 103, 104, 103, 105, 107, 106, 108]
rsi_values = rsi.calculate(prices)

print(f"Current RSI: {rsi_values[-1]:.2f}")

# Trading signal
if rsi_values[-1] < 30:
    print("Oversold - potential buy signal")
elif rsi_values[-1] > 70:
    print("Overbought - potential sell signal")
```

### Moving Averages

```python
from schwab.paper_trading.indicators import MovingAverage

# Simple Moving Average
sma = MovingAverage(period=20, ma_type="SMA")
sma_values = sma.calculate(prices)

# Exponential Moving Average
ema = MovingAverage(period=20, ma_type="EMA")
ema_values = ema.calculate(prices)

# Weighted Moving Average
wma = MovingAverage(period=20, ma_type="WMA")
wma_values = wma.calculate(prices)

# Crossover strategy
fast_ma = MovingAverage(period=10, ma_type="EMA")
slow_ma = MovingAverage(period=20, ma_type="EMA")

fast_values = fast_ma.calculate(prices)
slow_values = slow_ma.calculate(prices)

if fast_values[-1] > slow_values[-1] and fast_values[-2] <= slow_values[-2]:
    print("Bullish crossover - buy signal")
elif fast_values[-1] < slow_values[-1] and fast_values[-2] >= slow_values[-2]:
    print("Bearish crossover - sell signal")
```

### MACD (Moving Average Convergence Divergence)

```python
from schwab.paper_trading.indicators import MACD

# Create MACD indicator
macd = MACD(fast_period=12, slow_period=26, signal_period=9)

# Calculate MACD
macd_line, signal_line, histogram = macd.calculate(prices)

# Trading signals
if macd_line[-1] > signal_line[-1] and macd_line[-2] <= signal_line[-2]:
    print("MACD bullish crossover")
elif macd_line[-1] < signal_line[-1] and macd_line[-2] >= signal_line[-2]:
    print("MACD bearish crossover")

# Divergence detection
if histogram[-1] > 0 and histogram[-1] > histogram[-2]:
    print("Bullish momentum increasing")
```

### Bollinger Bands

```python
from schwab.paper_trading.indicators import BollingerBands

# Create Bollinger Bands
bb = BollingerBands(period=20, std_dev=2)

# Calculate bands
upper_band, middle_band, lower_band = bb.calculate(prices)

current_price = prices[-1]

# Trading signals
if current_price < lower_band[-1]:
    print("Price below lower band - potential buy")
elif current_price > upper_band[-1]:
    print("Price above upper band - potential sell")

# Band squeeze detection
band_width = upper_band[-1] - lower_band[-1]
if band_width < min(upper_band[-20:] - lower_band[-20:]):
    print("Bollinger Band squeeze - potential breakout coming")
```

## Strategy Development

### Example: Mean Reversion Strategy

```python
class MeanReversionStrategy:
    def __init__(self, client, symbol, period=20, std_dev=2):
        self.client = client
        self.symbol = symbol
        self.bb = BollingerBands(period=period, std_dev=std_dev)
        self.position = 0
        
    def get_price_history(self, days=30):
        """Get historical prices"""
        history = self.client.get_price_history(
            symbol=self.symbol,
            period_type="day",
            period=days,
            frequency_type="daily",
            frequency=1
        )
        return [candle.close for candle in history.candles]
    
    def check_signals(self, account_number):
        """Check for trading signals"""
        prices = self.get_price_history()
        upper, middle, lower = self.bb.calculate(prices)
        
        current_price = prices[-1]
        
        # Buy signal
        if current_price < lower[-1] and self.position == 0:
            order = self.client.create_market_order(
                symbol=self.symbol,
                quantity=100,
                instruction="BUY"
            )
            self.client.place_order(account_number, order)
            self.position = 100
            print(f"[PAPER] Bought {self.symbol} at ${current_price}")
            
        # Sell signal
        elif current_price > upper[-1] and self.position > 0:
            order = self.client.create_market_order(
                symbol=self.symbol,
                quantity=self.position,
                instruction="SELL"
            )
            self.client.place_order(account_number, order)
            print(f"[PAPER] Sold {self.symbol} at ${current_price}")
            self.position = 0

# Use the strategy
strategy = MeanReversionStrategy(paper_client, "SPY")
strategy.check_signals(paper_account_number)
```

### Example: Momentum Strategy

```python
class MomentumStrategy:
    def __init__(self, client, symbols, lookback=20):
        self.client = client
        self.symbols = symbols
        self.lookback = lookback
        self.positions = {}
        
    def calculate_momentum(self, symbol):
        """Calculate momentum score"""
        history = self.client.get_price_history(
            symbol=symbol,
            period_type="day",
            period=self.lookback + 1,
            frequency_type="daily",
            frequency=1
        )
        
        prices = [candle.close for candle in history.candles]
        if len(prices) >= 2:
            return (prices[-1] - prices[0]) / prices[0]
        return 0
    
    def rebalance(self, account_number, top_n=5):
        """Rebalance to top momentum stocks"""
        # Calculate momentum for all symbols
        momentum_scores = {}
        for symbol in self.symbols:
            momentum_scores[symbol] = self.calculate_momentum(symbol)
        
        # Sort by momentum
        sorted_symbols = sorted(
            momentum_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Select top N
        new_holdings = [s[0] for s in sorted_symbols[:top_n]]
        
        # Sell positions not in top N
        for symbol in list(self.positions.keys()):
            if symbol not in new_holdings:
                order = self.client.create_market_order(
                    symbol=symbol,
                    quantity=self.positions[symbol],
                    instruction="SELL"
                )
                self.client.place_order(account_number, order)
                print(f"[PAPER] Sold {symbol}")
                del self.positions[symbol]
        
        # Buy new positions
        account = self.client.get_account(account_number)
        cash = account.securitiesAccount.currentBalances.cashBalance
        position_size = cash / len(new_holdings)
        
        for symbol in new_holdings:
            if symbol not in self.positions:
                quote = self.client.get_quote(symbol)
                shares = int(position_size / quote.quote.lastPrice)
                
                if shares > 0:
                    order = self.client.create_market_order(
                        symbol=symbol,
                        quantity=shares,
                        instruction="BUY"
                    )
                    self.client.place_order(account_number, order)
                    self.positions[symbol] = shares
                    print(f"[PAPER] Bought {shares} shares of {symbol}")

# Use the strategy
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
momentum = MomentumStrategy(paper_client, symbols)
momentum.rebalance(paper_account_number)
```

## Portfolio Integration

### Using with PortfolioManager

```python
from schwab.portfolio import PortfolioManager

# Create portfolio manager with paper client
portfolio = PortfolioManager(paper_client)

# Add paper accounts
for account in paper_accounts:
    portfolio.add_account(account.accountNumber)

# Track performance
portfolio.refresh_positions()
summary = portfolio.get_portfolio_summary()

print(f"Total Portfolio Value: ${summary['total_value']:,.2f}")
print(f"Total P&L: ${summary['total_pnl']:,.2f} ({summary['total_pnl_percentage']:.2f}%)")

# Monitor orders
def on_order_update(event_type, data):
    print(f"[PAPER] {event_type}: {data}")

portfolio.monitor_orders(callback=on_order_update)
```

### Performance Tracking

```python
class PaperTradingPerformance:
    def __init__(self, client, account_number):
        self.client = client
        self.account_number = account_number
        self.initial_value = None
        self.trades = []
        
    def start_tracking(self):
        """Record initial account value"""
        account = self.client.get_account(self.account_number)
        self.initial_value = account.securitiesAccount.currentBalances.accountValue
        print(f"Starting value: ${self.initial_value:,.2f}")
        
    def record_trade(self, symbol, quantity, side, price):
        """Record a trade"""
        self.trades.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'quantity': quantity,
            'side': side,
            'price': price,
            'value': quantity * price
        })
        
    def get_performance(self):
        """Calculate performance metrics"""
        account = self.client.get_account(self.account_number)
        current_value = account.securitiesAccount.currentBalances.accountValue
        
        # Basic metrics
        total_return = current_value - self.initial_value
        return_pct = (total_return / self.initial_value) * 100
        
        # Trade statistics
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if self._is_winning_trade(t)])
        
        return {
            'initial_value': self.initial_value,
            'current_value': current_value,
            'total_return': total_return,
            'return_percentage': return_pct,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0
        }

# Track performance
tracker = PaperTradingPerformance(paper_client, paper_account_number)
tracker.start_tracking()

# After some trades...
performance = tracker.get_performance()
print(f"Return: ${performance['total_return']:,.2f} ({performance['return_percentage']:.2f}%)")
print(f"Win Rate: {performance['win_rate']:.1f}%")
```

## Best Practices

### 1. Realistic Trading

```python
# Use realistic position sizes
account = paper_client.get_account(paper_account_number)
account_value = account.securitiesAccount.currentBalances.accountValue

# Risk 1-2% per trade
max_risk = account_value * 0.02
position_size = max_risk / stop_loss_amount

# Don't overtrade
max_positions = 10
current_positions = len(account.securitiesAccount.positions or [])
if current_positions >= max_positions:
    print("Maximum positions reached")
```

### 2. Strategy Testing Framework

```python
class StrategyTester:
    def __init__(self, client, strategy, account_number):
        self.client = client
        self.strategy = strategy
        self.account_number = account_number
        self.results = []
        
    def backtest(self, start_date, end_date):
        """Run backtest on historical data"""
        # Implementation depends on strategy
        pass
        
    def paper_trade(self, duration_days=30):
        """Run paper trading test"""
        start_time = datetime.now()
        end_time = start_time + timedelta(days=duration_days)
        
        while datetime.now() < end_time:
            try:
                # Run strategy
                signals = self.strategy.generate_signals()
                
                for signal in signals:
                    if signal['action'] == 'BUY':
                        order = self.client.create_market_order(
                            symbol=signal['symbol'],
                            quantity=signal['quantity'],
                            instruction="BUY"
                        )
                    elif signal['action'] == 'SELL':
                        order = self.client.create_market_order(
                            symbol=signal['symbol'],
                            quantity=signal['quantity'],
                            instruction="SELL"
                        )
                    
                    self.client.place_order(self.account_number, order)
                    
                # Wait for next iteration
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Error in paper trading: {e}")
```

### 3. Risk Management

```python
def calculate_position_size(account_value, risk_per_trade, stop_loss_pct):
    """Calculate appropriate position size"""
    risk_amount = account_value * risk_per_trade
    position_size = risk_amount / stop_loss_pct
    return int(position_size)

def set_stop_loss(client, account_number, symbol, entry_price, stop_pct):
    """Set stop loss order"""
    stop_price = entry_price * (1 - stop_pct)
    
    order = client.create_stop_order(
        symbol=symbol,
        quantity=position_size,
        stop_price=stop_price,
        instruction="SELL"
    )
    
    client.place_order(account_number, order)
    print(f"[PAPER] Stop loss set at ${stop_price:.2f}")
```

### 4. Logging and Analysis

```python
import json
from datetime import datetime

class PaperTradingLogger:
    def __init__(self, filename="paper_trades.json"):
        self.filename = filename
        self.trades = []
        
    def log_trade(self, trade_data):
        """Log a trade"""
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': trade_data['symbol'],
            'side': trade_data['side'],
            'quantity': trade_data['quantity'],
            'price': trade_data['price'],
            'order_type': trade_data['order_type'],
            'strategy': trade_data.get('strategy', 'manual')
        }
        
        self.trades.append(trade)
        self.save()
        
    def save(self):
        """Save trades to file"""
        with open(self.filename, 'w') as f:
            json.dump(self.trades, f, indent=2)
            
    def analyze(self):
        """Analyze trading performance"""
        if not self.trades:
            return "No trades to analyze"
            
        # Group by symbol
        by_symbol = {}
        for trade in self.trades:
            symbol = trade['symbol']
            if symbol not in by_symbol:
                by_symbol[symbol] = []
            by_symbol[symbol].append(trade)
            
        # Calculate statistics
        stats = {}
        for symbol, trades in by_symbol.items():
            total_trades = len(trades)
            buy_trades = len([t for t in trades if t['side'] == 'BUY'])
            sell_trades = len([t for t in trades if t['side'] == 'SELL'])
            
            stats[symbol] = {
                'total_trades': total_trades,
                'buy_trades': buy_trades,
                'sell_trades': sell_trades
            }
            
        return stats

# Use the logger
logger = PaperTradingLogger()
logger.log_trade({
    'symbol': 'AAPL',
    'side': 'BUY',
    'quantity': 100,
    'price': 150.00,
    'order_type': 'MARKET',
    'strategy': 'momentum'
})
```

## Examples

### Complete Paper Trading Script

```python
#!/usr/bin/env python3
"""
Paper Trading Demo Script
"""

import asyncio
from datetime import datetime
from schwab.auth import SchwabAuth
from schwab.paper_trading import AsyncPaperTradingClient
from schwab.paper_trading.indicators import RSI, MovingAverage

async def main():
    # Initialize auth
    auth = SchwabAuth(
        client_id="your_client_id",
        client_secret="your_client_secret",
        redirect_uri="https://localhost:8080/callback"
    )
    
    # Create paper trading client
    async with AsyncPaperTradingClient(auth=auth) as client:
        print("Paper Trading Demo Started")
        print("=" * 50)
        
        # Get paper accounts
        accounts = await client.get_account_numbers()
        paper_account = accounts[0].accountNumber  # Assume first is paper
        
        # Show account info
        account = await client.get_account(paper_account, include_positions=True)
        print(f"\nAccount: {paper_account}")
        print(f"Balance: ${account.securitiesAccount.currentBalances.cashBalance:,.2f}")
        print(f"Buying Power: ${account.securitiesAccount.currentBalances.buyingPower:,.2f}")
        
        # Show positions
        if account.securitiesAccount.positions:
            print("\nCurrent Positions:")
            for pos in account.securitiesAccount.positions:
                print(f"  {pos.instrument.symbol}: {pos.longQuantity} @ ${pos.averagePrice}")
        
        # Example trade with technical indicators
        symbol = "SPY"
        
        # Get price history
        history = await client.get_price_history(
            symbol=symbol,
            period_type="day",
            period=30,
            frequency_type="daily",
            frequency=1
        )
        
        prices = [candle.close for candle in history.candles]
        
        # Calculate indicators
        rsi = RSI(period=14)
        rsi_values = rsi.calculate(prices)
        
        ma20 = MovingAverage(period=20, ma_type="SMA")
        ma20_values = ma20.calculate(prices)
        
        print(f"\n{symbol} Analysis:")
        print(f"Current Price: ${prices[-1]:.2f}")
        print(f"20-day MA: ${ma20_values[-1]:.2f}")
        print(f"RSI(14): {rsi_values[-1]:.2f}")
        
        # Trading decision
        if rsi_values[-1] < 30 and prices[-1] < ma20_values[-1]:
            print("\nBuy Signal Detected!")
            
            # Calculate position size (risk 1% of account)
            risk_amount = account.securitiesAccount.currentBalances.accountValue * 0.01
            shares = int(risk_amount / prices[-1])
            
            # Place order
            order = client.create_limit_order(
                symbol=symbol,
                quantity=shares,
                limit_price=prices[-1] * 1.001,  # Slightly above market
                instruction="BUY"
            )
            
            result = await client.place_order(paper_account, order)
            print(f"Order placed: Buy {shares} shares of {symbol}")
            
        elif rsi_values[-1] > 70 and prices[-1] > ma20_values[-1]:
            print("\nSell Signal Detected!")
            # Check if we have position to sell
            # ... implementation ...
            
        else:
            print("\nNo clear signal - holding current positions")
        
        print("\n" + "=" * 50)
        print("Paper Trading Demo Complete")

if __name__ == "__main__":
    asyncio.run(main())
```

### Paper Trading with Real-Time Monitoring

```python
import asyncio
from schwab.paper_trading import AsyncPaperTradingClient
from schwab.order_monitor import OrderMonitor

async def monitor_paper_trades():
    async with AsyncPaperTradingClient(auth=auth) as client:
        monitor = OrderMonitor(client)
        
        def on_status_change(order, old_status, new_status):
            print(f"[PAPER] Order {order.orderId}: {old_status} -> {new_status}")
            
        def on_execution(order, execution):
            print(f"[PAPER] Executed: {execution.quantity} @ ${execution.price}")
            
        # Start monitoring
        monitor.start_monitoring(
            account_number=paper_account_number,
            order_ids=active_order_ids,
            on_status_change=on_status_change,
            on_execution=on_execution
        )
        
        # Keep running
        await asyncio.sleep(300)  # Monitor for 5 minutes
        
        monitor.stop_monitoring()

asyncio.run(monitor_paper_trades())
```

## Transitioning to Live Trading

When you're ready to move from paper to live trading:

1. **Review Performance**: Analyze your paper trading results thoroughly
2. **Start Small**: Begin with smaller position sizes in live trading
3. **Keep Same Strategy**: Don't change your strategy when going live
4. **Monitor Closely**: Watch your first few live trades carefully
5. **Have Stop Losses**: Always use stop losses in live trading

```python
# Switch from paper to live trading
from schwab import SchwabClient  # Regular client for live trading

# Same code works for live trading
live_client = SchwabClient(auth=auth)

# Use same strategies but with real account
real_account = "your_real_account_number"

# IMPORTANT: Double-check account number!
print(f"Trading on account: {real_account}")
response = input("Confirm this is your REAL account (yes/no): ")

if response.lower() == "yes":
    # Place real trades...
    pass
```

## Troubleshooting

### Common Issues

1. **Account Detection**
   - Paper accounts may have specific naming patterns
   - Check account balance patterns (often round numbers)
   - Contact Schwab support if unsure

2. **Order Rejections**
   - Ensure market hours for the asset type
   - Check buying power and margin requirements
   - Verify symbol format

3. **Missing Data**
   - Some features may be limited in paper accounts
   - Historical data access is the same as live accounts

### Debug Mode

```python
# Enable debug logging
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('schwab.paper_trading')

# This will show detailed information about paper trading operations
```

## Conclusion

Paper trading with the Schwab Trader library provides a safe, realistic environment to:
- Test and refine trading strategies
- Practice order management
- Build confidence before risking real money
- Develop and backtest technical analysis strategies

Remember that while paper trading is valuable, it doesn't perfectly replicate the psychological aspects of real trading. Always start small when transitioning to live trading and never risk more than you can afford to lose.

For more examples, see the [examples directory](../examples/paper_trading_demo.py).