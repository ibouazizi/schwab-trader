# New Features Documentation

## Order Validation and Modification

The library now includes comprehensive order validation and modification capabilities:

### Order Validation
- Automatic validation of order modifications
- Checks for editable order status
- Price and quantity validation
- Custom validation error messages

```python
from schwab import SchwabClient
from schwab.models.order_validation import OrderValidationError

client = SchwabClient(api_key="your_api_key")

try:
    modified_order = client.modify_order_price(
        account_number="encrypted_account_number",
        order_id=12345,
        new_price=155.00
    )
except OrderValidationError as e:
    print(f"Validation failed: {str(e)}")
```

### Convenience Methods
The library provides simple methods for common order modifications:

```python
# Modify order price
modified_order = client.modify_order_price(
    account_number="encrypted_account_number",
    order_id=12345,
    new_price=155.00
)

# Modify order quantity
modified_order = client.modify_order_quantity(
    account_number="encrypted_account_number",
    order_id=12345,
    new_quantity=200
)
```

## Batch Operations

New batch operation capabilities for efficient order management:

### Batch Cancel Orders
```python
results = client.batch_cancel_orders(
    account_number="encrypted_account_number",
    order_ids=[12345, 12346, 12347]
)

for order_id, success in results.items():
    print(f"Order {order_id}: {'Cancelled' if success else 'Failed'}")
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

for order_id, result in results.items():
    if isinstance(result, Exception):
        print(f"Order {order_id} modification failed: {str(result)}")
    else:
        print(f"Order {order_id} modified successfully")
```

## Order Status Change Notifications

Real-time order status monitoring with callback support:

```python
def status_callback(order: Order, status: str):
    print(f"Order {order.order_id} status changed to {status}")

def execution_callback(report: ExecutionReport):
    print(f"Order {report.order_id} executed: {report.quantity} @ {report.price}")

# Start monitoring specific orders
client.monitor_orders(
    account_number="encrypted_account_number",
    order_ids=[12345, 12346],
    status_callback=status_callback,
    execution_callback=execution_callback
)

# Stop monitoring when done
client.stop_monitoring()
```

## Order Execution Reports

Detailed execution reports for filled orders:

```python
class ExecutionReport:
    def __init__(
        self,
        order_id: int,
        execution_id: str,
        timestamp: datetime,
        quantity: int,
        price: float,
        commission: float,
        exchange: str
    )
```

### Properties
- `order_id`: The ID of the order that was executed
- `execution_id`: Unique identifier for this execution
- `timestamp`: When the execution occurred
- `quantity`: Number of shares executed
- `price`: Execution price
- `commission`: Commission charged for this execution
- `exchange`: Exchange where the execution occurred
- `value`: Total value of the execution (quantity * price)
- `total_cost`: Total cost including commission

### Example Usage
```python
def execution_callback(report: ExecutionReport):
    print(f"Execution Report:")
    print(f"  Order ID: {report.order_id}")
    print(f"  Execution ID: {report.execution_id}")
    print(f"  Time: {report.timestamp}")
    print(f"  Quantity: {report.quantity}")
    print(f"  Price: ${report.price:.2f}")
    print(f"  Value: ${report.value:.2f}")
    print(f"  Commission: ${report.commission:.2f}")
    print(f"  Total Cost: ${report.total_cost:.2f}")
    print(f"  Exchange: {report.exchange}")

client.monitor_orders(
    account_number="encrypted_account_number",
    order_ids=[12345],
    execution_callback=execution_callback
)
```

## Error Handling

The library includes comprehensive error handling:

### Order Validation Errors
```python
try:
    modified_order = client.modify_order_price(
        account_number="encrypted_account_number",
        order_id=12345,
        new_price=155.00
    )
except OrderValidationError as e:
    print(f"Validation error: {str(e)}")
```

### API Request Errors
```python
try:
    order = client.get_order(
        account_number="encrypted_account_number",
        order_id=12345
    )
except requests.exceptions.RequestException as e:
    print(f"API error: {str(e)}")
```

### Batch Operation Error Handling
```python
results = client.batch_modify_orders(
    account_number="encrypted_account_number",
    modifications=[
        {"order_id": 12345, "price": 155.00},
        {"order_id": 12346, "quantity": 200}
    ]
)

for order_id, result in results.items():
    if isinstance(result, Exception):
        print(f"Order {order_id} failed: {str(result)}")
    else:
        print(f"Order {order_id} modified successfully: {result}")
```