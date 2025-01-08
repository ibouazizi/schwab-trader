from enum import Enum
from typing import Optional, List
from datetime import datetime
from .orders import Order, OrderStatus, OrderInstruction

class OrderValidationError(Exception):
    pass

class EditableOrderStatus(Enum):
    WORKING = "WORKING"
    PENDING = "PENDING"
    QUEUED = "QUEUED"

class OrderValidator:
    @staticmethod
    def is_order_editable(order: Order) -> bool:
        """Check if an order can be modified based on its current status."""
        return order.status in [status.value for status in EditableOrderStatus]

    @staticmethod
    def validate_price_modification(order: Order, new_price: float) -> None:
        """Validate if a price modification is allowed for the order."""
        if not OrderValidator.is_order_editable(order):
            raise OrderValidationError(f"Order with status {order.status} cannot be modified")
        
        if new_price <= 0:
            raise OrderValidationError("New price must be greater than 0")

    @staticmethod
    def validate_quantity_modification(order: Order, new_quantity: int) -> None:
        """Validate if a quantity modification is allowed for the order."""
        if not OrderValidator.is_order_editable(order):
            raise OrderValidationError(f"Order with status {order.status} cannot be modified")
        
        if new_quantity <= 0:
            raise OrderValidationError("New quantity must be greater than 0")