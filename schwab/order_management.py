from typing import List, Optional, Dict
from datetime import datetime
from .models.orders import Order, OrderStatus
from .models.order_validation import OrderValidator, OrderValidationError

class OrderManagement:
    def __init__(self, client):
        self.client = client

    def modify_price(self, account_number: str, order_id: int, new_price: float) -> Order:
        """
        Modify the price of an existing order.
        
        Args:
            account_number: The encrypted account number
            order_id: The order ID to modify
            new_price: The new price for the order
            
        Returns:
            Modified order object
        """
        original_order = self.client.get_order(account_number, order_id)
        OrderValidator.validate_price_modification(original_order, new_price)
        
        modified_order = original_order.copy()
        modified_order.price = new_price
        
        return self.client.replace_order(account_number, order_id, modified_order)

    def modify_quantity(self, account_number: str, order_id: int, new_quantity: int) -> Order:
        """
        Modify the quantity of an existing order.
        
        Args:
            account_number: The encrypted account number
            order_id: The order ID to modify
            new_quantity: The new quantity for the order
            
        Returns:
            Modified order object
        """
        original_order = self.client.get_order(account_number, order_id)
        OrderValidator.validate_quantity_modification(original_order, new_quantity)
        
        modified_order = original_order.copy()
        modified_order.quantity = new_quantity
        
        return self.client.replace_order(account_number, order_id, modified_order)

    def batch_cancel_orders(self, account_number: str, order_ids: List[int]) -> Dict[int, bool]:
        """
        Cancel multiple orders in batch.
        
        Args:
            account_number: The encrypted account number
            order_ids: List of order IDs to cancel
            
        Returns:
            Dictionary mapping order IDs to cancellation success status
        """
        results = {}
        for order_id in order_ids:
            try:
                self.client.cancel_order(account_number, order_id)
                results[order_id] = True
            except Exception as e:
                results[order_id] = False
        return results

    def batch_modify_orders(self, account_number: str, modifications: List[Dict]) -> Dict[int, Order]:
        """
        Modify multiple orders in batch.
        
        Args:
            account_number: The encrypted account number
            modifications: List of dictionaries containing order_id and modifications
            
        Returns:
            Dictionary mapping order IDs to modified Order objects
        """
        results = {}
        for mod in modifications:
            order_id = mod['order_id']
            try:
                original_order = self.client.get_order(account_number, order_id)
                modified_order = original_order.copy()
                
                if 'price' in mod:
                    OrderValidator.validate_price_modification(original_order, mod['price'])
                    modified_order.price = mod['price']
                
                if 'quantity' in mod:
                    OrderValidator.validate_quantity_modification(original_order, mod['quantity'])
                    modified_order.quantity = mod['quantity']
                
                results[order_id] = self.client.replace_order(account_number, order_id, modified_order)
            except Exception as e:
                results[order_id] = e
        
        return results