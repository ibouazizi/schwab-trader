# Schwab API Python Library Documentation

## ⚠️ Important Notice
This API documentation is provided for informational purposes only. Before using this library, please read and understand our [full disclaimer](DISCLAIMER.md). By using this library, you acknowledge that trading involves substantial risk and that you are solely responsible for verifying and validating all trading operations.

## Table of Contents
1. [Installation](#installation)
2. [Client Initialization](#client-initialization)
3. [Account Management](#account-management)
4. [Order Creation](#order-creation)
5. [Order Management](#order-management)
6. [Order Monitoring](#order-monitoring)
7. [Batch Operations](#batch-operations)
8. [Error Handling](#error-handling)

## Installation

### From PyPI
```bash
pip install schwab
```

### From Source
```bash
git clone https://github.com/ibouazizi/schwab.git
cd schwab
pip install -e .
```

## Client Initialization

```python
from schwab import SchwabClient

client = SchwabClient(api_key="your_api_key")
```

## Account Management

### Get Account Numbers
```python
accounts = client.get_account_numbers()
```

### Get Account Details
```python
account_details = client.get_account_details(account_number="encrypted_account_number")
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
    from_entered_time=datetime.now() - timedelta(days=7),
    to_entered_time=datetime.now(),
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
def status_callback(order: Order, status: str):
    print(f"Order {order.order_id} status changed to {status}")

def execution_callback(report: ExecutionReport):
    print(f"Order {report.order_id} executed: {report.quantity} @ {report.price}")

client.monitor_orders(
    account_number="encrypted_account_number",
    order_ids=[12345, 12346],
    status_callback=status_callback,
    execution_callback=execution_callback,
    interval=1.0  # Poll every second
)
```

### Stop Monitoring
```python
client.stop_monitoring()
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
```

### API Request Error
```python
import requests

try:
    order = client.get_order(
        account_number="encrypted_account_number",
        order_id=12345
    )
except requests.exceptions.RequestException as e:
    print(f"API request failed: {str(e)}")
```

## Data Models

### Order Status Values
- `WORKING`: Order is active and working
- `PENDING`: Order is pending submission
- `QUEUED`: Order is queued for submission
- `REJECTED`: Order was rejected
- `CANCELLED`: Order was cancelled
- `FILLED`: Order was completely filled
- `EXPIRED`: Order has expired
- `REPLACED`: Order was replaced

### Order Instructions
- `BUY`: Buy order
- `SELL`: Sell order
- `BUY_TO_COVER`: Buy to cover a short position
- `SELL_SHORT`: Sell short

### Order Types
- `MARKET`: Market order
- `LIMIT`: Limit order
- `STOP`: Stop order
- `STOP_LIMIT`: Stop-limit order
- `TRAILING_STOP`: Trailing stop order
- `MARKET_ON_CLOSE`: Market-on-close order
- `LIMIT_ON_CLOSE`: Limit-on-close order

### Order Duration
- `DAY`: Day order
- `GOOD_TILL_CANCEL`: Good-till-cancel order
- `FILL_OR_KILL`: Fill-or-kill order
- `IMMEDIATE_OR_CANCEL`: Immediate-or-cancel order

### Special Instructions
- `ALL_OR_NONE`: All-or-none order
- `DO_NOT_REDUCE`: Do not reduce order
- `ALL_OR_NONE_DO_NOT_REDUCE`: All-or-none and do not reduce