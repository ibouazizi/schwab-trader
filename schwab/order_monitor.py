from typing import Callable, Dict, List, Optional
from datetime import datetime
import asyncio
from .models.orders import Order, OrderStatus
from .models.execution import ExecutionReport, ExecutionReportList

class OrderMonitor:
    def __init__(self, client):
        self.client = client
        self._status_callbacks: Dict[int, List[Callable]] = {}
        self._execution_callbacks: Dict[int, List[Callable]] = {}
        self._monitored_orders: Dict[int, Order] = {}
        self._running = False

    def add_status_callback(self, order_id: int, callback: Callable[[Order, OrderStatus], None]) -> None:
        """
        Add a callback for order status changes.
        
        Args:
            order_id: The order ID to monitor
            callback: Function to call when status changes
        """
        if order_id not in self._status_callbacks:
            self._status_callbacks[order_id] = []
        self._status_callbacks[order_id].append(callback)

    def add_execution_callback(self, order_id: int, callback: Callable[[ExecutionReport], None]) -> None:
        """
        Add a callback for order execution reports.
        
        Args:
            order_id: The order ID to monitor
            callback: Function to call when execution report is received
        """
        if order_id not in self._execution_callbacks:
            self._execution_callbacks[order_id] = []
        self._execution_callbacks[order_id].append(callback)

    async def start_monitoring(self, account_number: str, order_ids: List[int], interval: float = 1.0):
        """
        Start monitoring orders for status changes and executions.
        
        Args:
            account_number: The encrypted account number
            order_ids: List of order IDs to monitor
            interval: Polling interval in seconds
        """
        self._running = True
        
        while self._running:
            for order_id in order_ids:
                try:
                    current_order = await self.client.get_order(account_number, order_id)
                    previous_order = self._monitored_orders.get(order_id)
                    
                    # Check for status changes
                    if previous_order and previous_order.status != current_order.status:
                        if order_id in self._status_callbacks:
                            for callback in self._status_callbacks[order_id]:
                                callback(current_order, current_order.status)
                    
                    # Check for executions
                    if current_order.executions:
                        new_executions = []
                        if previous_order:
                            new_executions = [
                                exec for exec in current_order.executions 
                                if exec not in previous_order.executions
                            ]
                        else:
                            new_executions = current_order.executions
                        
                        if new_executions and order_id in self._execution_callbacks:
                            for execution in new_executions:
                                for callback in self._execution_callbacks[order_id]:
                                    callback(execution)
                    
                    self._monitored_orders[order_id] = current_order
                
                except Exception as e:
                    print(f"Error monitoring order {order_id}: {str(e)}")
            
            await asyncio.sleep(interval)

    def stop_monitoring(self):
        """Stop monitoring all orders."""
        self._running = False

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
    ):
        self.order_id = order_id
        self.execution_id = execution_id
        self.timestamp = timestamp
        self.quantity = quantity
        self.price = price
        self.commission = commission
        self.exchange = exchange

    @property
    def value(self) -> float:
        """Calculate the total value of the execution."""
        return self.quantity * self.price

    @property
    def total_cost(self) -> float:
        """Calculate the total cost including commission."""
        return self.value + self.commission