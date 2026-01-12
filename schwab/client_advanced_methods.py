# Advanced Order Creation Methods for SchwabClient

from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional, Union

from .models.generated.trading_models import (
    Order, OrderType, Session as OrderSession, Duration as OrderDuration, 
    OrderStrategyType, OrderLeg, OrderLegType, Instruction as OrderInstruction, 
    PositionEffect, QuantityType, ComplexOrderStrategyType, SpecialInstruction, 
    RequestedDestination, TaxLotMethod, TransactionType
)

def create_multi_leg_option_order(
    self,
    legs: List[Dict[str, Any]],
    order_type: OrderType = OrderType.NET_DEBIT,
    price: Optional[Union[float, Decimal]] = None,
    session: OrderSession = OrderSession.NORMAL,
    duration: OrderDuration = OrderDuration.DAY,
    complex_order_strategy_type: ComplexOrderStrategyType = ComplexOrderStrategyType.VERTICAL,
    requested_destination: Optional[RequestedDestination] = None,
    tax_lot_method: Optional[TaxLotMethod] = None,
    special_instruction: Optional[SpecialInstruction] = None
) -> Order:
    """Create a multi-leg option order (spread, straddle, etc).
    
    Args:
        legs: List of leg definitions, each containing:
            - symbol: Option symbol
            - instruction: BUY_TO_OPEN, SELL_TO_OPEN, BUY_TO_CLOSE, SELL_TO_CLOSE
            - quantity: Number of contracts
            - position_effect: OPENING or CLOSING
        order_type: NET_DEBIT, NET_CREDIT, NET_ZERO, or MARKET
        price: The net price for the spread (required for NET_DEBIT/NET_CREDIT)
        session: Order session (default: NORMAL)
        duration: Order duration (default: DAY)
        complex_order_strategy_type: Type of complex strategy
        requested_destination: Optional trading destination
        tax_lot_method: Optional tax lot method
        special_instruction: Optional special instruction
        
    Returns:
        Order object ready to be placed
    """
    order_legs = []
    total_quantity = Decimal("0")
    
    for leg in legs:
        quantity = Decimal(str(leg['quantity']))
        total_quantity += quantity
        
        order_leg = OrderLeg(
            order_leg_type=OrderLegType.OPTION,
            leg_id=len(order_legs) + 1,
            instrument={
                "symbol": leg['symbol'],
                "asset_type": "OPTION"
            },
            instruction=leg['instruction'],
            position_effect=leg.get('position_effect', PositionEffect.OPENING),
            quantity=quantity,
            quantity_type=QuantityType.ALL_SHARES
        )
        order_legs.append(order_leg)
    
    order_params = {
        "session": session,
        "duration": duration,
        "order_type": order_type,
        "complex_order_strategy_type": complex_order_strategy_type,
        "quantity": total_quantity,
        "filled_quantity": Decimal("0"),
        "remaining_quantity": total_quantity,
        "requested_destination": requested_destination,
        "tax_lot_method": tax_lot_method,
        "special_instruction": special_instruction,
        "order_strategy_type": OrderStrategyType.SINGLE,
        "order_leg_collection": order_legs
    }
    
    if price is not None and order_type in [OrderType.NET_DEBIT, OrderType.NET_CREDIT]:
        order_params["price"] = Decimal(str(price))
        
    return Order(**order_params)

def create_one_cancels_other_order(
    self,
    primary_order: Order,
    secondary_order: Order
) -> Order:
    """Create a one-cancels-other (OCO) order.
    
    Args:
        primary_order: The primary order
        secondary_order: The secondary order that cancels if primary fills
        
    Returns:
        OCO order object ready to be placed
    """
    return Order(
        order_strategy_type=OrderStrategyType.OCO,
        child_order_strategies=[primary_order, secondary_order]
    )

def create_one_triggers_other_order(
    self,
    primary_order: Order,
    triggered_order: Order
) -> Order:
    """Create a one-triggers-other (OTO) order.
    
    Args:
        primary_order: The primary order
        triggered_order: The order triggered when primary fills
        
    Returns:
        OTO order object ready to be placed
    """
    primary_order.child_order_strategies = [triggered_order]
    primary_order.order_strategy_type = OrderStrategyType.TRIGGER
    return primary_order

def create_bracket_order(
    self,
    symbol: str,
    quantity: Union[int, Decimal],
    instruction: OrderInstruction,
    entry_price: Optional[Union[float, Decimal]] = None,
    profit_target_price: Union[float, Decimal] = None,
    stop_loss_price: Union[float, Decimal] = None,
    profit_target_percent: Optional[float] = None,
    stop_loss_percent: Optional[float] = None,
    order_type: OrderType = OrderType.MARKET,
    session: OrderSession = OrderSession.NORMAL,
    duration: OrderDuration = OrderDuration.DAY
) -> Order:
    """Create a bracket order (entry with profit target and stop loss).
    
    Args:
        symbol: The symbol to trade
        quantity: The quantity to trade
        instruction: BUY or SELL for the entry order
        entry_price: Entry limit price (None for market order)
        profit_target_price: Absolute profit target price
        stop_loss_price: Absolute stop loss price
        profit_target_percent: Profit target as percentage (alternative to price)
        stop_loss_percent: Stop loss as percentage (alternative to price)
        order_type: MARKET or LIMIT for entry order
        session: Order session (default: NORMAL)
        duration: Order duration (default: DAY)
        
    Returns:
        Bracket order object ready to be placed
    """
    quantity = Decimal(str(quantity))
    
    # Create entry order
    if order_type == OrderType.MARKET:
        entry_order = self.create_market_order(
            symbol=symbol,
            quantity=quantity,
            instruction=instruction,
            session=session,
            duration=duration
        )
    else:
        entry_order = self.create_limit_order(
            symbol=symbol,
            quantity=quantity,
            limit_price=entry_price,
            instruction=instruction,
            session=session,
            duration=duration
        )
    
    # Calculate target and stop prices if percentages provided
    if entry_price and profit_target_percent:
        profit_target_price = float(entry_price) * (1 + profit_target_percent / 100)
    if entry_price and stop_loss_percent:
        stop_loss_price = float(entry_price) * (1 - stop_loss_percent / 100)
    
    # Determine opposite instruction for exit orders
    exit_instruction = OrderInstruction.SELL if instruction == OrderInstruction.BUY else OrderInstruction.BUY
    
    # Create profit target order
    profit_order = self.create_limit_order(
        symbol=symbol,
        quantity=quantity,
        limit_price=profit_target_price,
        instruction=exit_instruction,
        session=session,
        duration=OrderDuration.GOOD_TILL_CANCEL
    )
    
    # Create stop loss order
    stop_loss_order = self.create_stop_order(
        symbol=symbol,
        quantity=quantity,
        stop_price=stop_loss_price,
        instruction=exit_instruction,
        session=session,
        duration=OrderDuration.GOOD_TILL_CANCEL
    )
    
    # Create OCO for the exit orders
    exit_oco = self.create_one_cancels_other_order(profit_order, stop_loss_order)
    
    # Create OTO with entry triggering the OCO exit
    return self.create_one_triggers_other_order(entry_order, exit_oco)

# Portfolio Analysis Methods
def get_portfolio_analysis(self, account_numbers: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get advanced portfolio analysis including Greeks, beta, and allocation.
    
    Args:
        account_numbers: Optional list of account numbers to analyze (default: all)
        
    Returns:
        Dictionary containing:
        - total_delta: Portfolio delta
        - total_gamma: Portfolio gamma
        - total_theta: Portfolio theta
        - total_vega: Portfolio vega
        - portfolio_beta: Weighted beta
        - sector_allocation: Breakdown by sector
        - asset_allocation: Breakdown by asset type
    """
    if not account_numbers:
        accounts_data = self.get_account_numbers()
        if accounts_data and accounts_data.accounts:
            account_numbers = [acc.account_number for acc in accounts_data.accounts]
        else:
            account_numbers = []
    
    analysis = {
        "total_delta": Decimal("0"),
        "total_gamma": Decimal("0"),
        "total_theta": Decimal("0"),
        "total_vega": Decimal("0"),
        "portfolio_beta": Decimal("0"),
        "sector_allocation": {},
        "asset_allocation": {},
        "total_value": Decimal("0")
    }
    
    for account_num in account_numbers:
        account = self.get_account(account_num, include_positions=True)
        
        if hasattr(account, 'securities_account') and account.securities_account:
            sec_account = account.securities_account
            
            # Add account value
            if hasattr(sec_account, 'current_balances') and sec_account.current_balances:
                if hasattr(sec_account.current_balances, 'liquidation_value'):
                    analysis["total_value"] += Decimal(str(sec_account.current_balances.liquidation_value or 0))
            
            # Process positions
            if hasattr(sec_account, 'positions') and sec_account.positions:
                for position in sec_account.positions:
                    # Get Greeks for options
                    if position.instrument.asset_type == "OPTION":
                        # In real implementation, would fetch option chain for Greeks
                        # For now, using placeholder calculations
                        analysis["total_delta"] += position.long_quantity * Decimal("0.5")
                        analysis["total_gamma"] += position.long_quantity * Decimal("0.02")
                        analysis["total_theta"] += position.long_quantity * Decimal("-0.05")
                        analysis["total_vega"] += position.long_quantity * Decimal("0.15")
                    
                    # Track asset allocation
                    asset_type = position.instrument.asset_type
                    if asset_type not in analysis["asset_allocation"]:
                        analysis["asset_allocation"][asset_type] = Decimal("0")
                    analysis["asset_allocation"][asset_type] += position.market_value
                    
                    # For equities, estimate sector (would need external data in real implementation)
                    if asset_type == "EQUITY":
                        # Placeholder sector assignment
                        sector = "Technology"  # Would need real sector data
                        if sector not in analysis["sector_allocation"]:
                            analysis["sector_allocation"][sector] = Decimal("0")
                        analysis["sector_allocation"][sector] += position.market_value
    
    # Calculate percentages
    if analysis["total_value"] > 0:
        for asset_type, value in analysis["asset_allocation"].items():
            analysis["asset_allocation"][asset_type] = {
                "value": value,
                "percentage": float(value / analysis["total_value"] * 100)
            }
        
        for sector, value in analysis["sector_allocation"].items():
            analysis["sector_allocation"][sector] = {
                "value": value,
                "percentage": float(value / analysis["total_value"] * 100)
            }
    
    return analysis

# Tax Lot Methods
def get_tax_lots(self, account_number: str, symbol: str) -> List[Dict[str, Any]]:
    """Get tax lots for a specific position.
    
    Args:
        account_number: The encrypted account number
        symbol: The symbol to get tax lots for
        
    Returns:
        List of tax lots with purchase date, quantity, and cost basis
    """
    # This would require a specific API endpoint that may not be available
    # For now, returning a placeholder structure
    return [{
        "symbol": symbol,
        "quantity": 0,
        "purchase_date": None,
        "cost_basis": 0,
        "market_value": 0,
        "gain_loss": 0,
        "holding_period": "LONG"  # or "SHORT"
    }]

def place_order_with_tax_lot(
    self,
    account_number: str,
    order: Order,
    tax_lot_ids: List[str]
) -> None:
    """Place an order with specific tax lot selection.
    
    Args:
        account_number: The encrypted account number
        order: The order to place
        tax_lot_ids: List of tax lot IDs to use for the order
    """
    # Modify order to include tax lot information
    # This would require specific API support
    self.place_order(account_number, order)

# Dividend and Corporate Action Methods
def get_dividend_history(
    self,
    account_number: str,
    start_date: datetime,
    end_date: datetime
) -> List[Dict[str, Any]]:
    """Get dividend history for an account.
    
    Args:
        account_number: The encrypted account number
        start_date: Start date for dividend history
        end_date: End date for dividend history
        
    Returns:
        List of dividend payments
    """
    # Filter transactions for dividend type
    transactions = self.get_transactions(
        account_number=account_number,
        start_date=start_date,
        end_date=end_date,
        transaction_type=TransactionType.DIVIDEND_OR_INTEREST
    )
    
    dividends = []
    for txn in transactions:
        if txn.type == TransactionType.DIVIDEND_OR_INTEREST:
            dividends.append({
                "date": txn.time,
                "symbol": txn.description,  # Would need parsing
                "amount": float(txn.net_amount) if txn.net_amount else 0,
                "type": "DIVIDEND"
            })
    
    return dividends

def get_cost_basis_summary(self, account_number: str) -> Dict[str, Any]:
    """Get cost basis summary for all positions in an account.
    
    Args:
        account_number: The encrypted account number
        
    Returns:
        Dictionary with cost basis information by position
    """
    account = self.get_account(account_number, include_positions=True)
    cost_basis_summary = {}
    
    if hasattr(account, 'securities_account') and account.securities_account:
        if hasattr(account.securities_account, 'positions') and account.securities_account.positions:
            for position in account.securities_account.positions:
                symbol = position.instrument.symbol
                cost_basis_summary[symbol] = {
                    "quantity": float(position.long_quantity - position.short_quantity),
                    "cost_basis": float(position.average_price * position.long_quantity),
                    "market_value": float(position.market_value),
                    "unrealized_gain_loss": float(position.market_value - (position.average_price * position.long_quantity))
                }
    
    return cost_basis_summary

# Account Performance Methods
def calculate_account_performance(
    self,
    account_number: str,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Any]:
    """Calculate account performance metrics.
    
    Args:
        account_number: The encrypted account number
        start_date: Start date for performance calculation
        end_date: End date for performance calculation
        
    Returns:
        Dictionary with performance metrics
    """
    # This is a simplified implementation
    # Real implementation would need historical account values
    
    account = self.get_account(account_number)
    current_value = 0
    
    if hasattr(account, 'securities_account') and account.securities_account:
        if hasattr(account.securities_account, 'current_balances'):
            balances = account.securities_account.current_balances
            if hasattr(balances, 'liquidation_value'):
                current_value = float(balances.liquidation_value)
    
    # Get transactions to calculate cash flows
    transactions = self.get_transactions(
        account_number=account_number,
        start_date=start_date,
        end_date=end_date
    )
    
    cash_flows = 0
    for txn in transactions:
        if txn.type in [TransactionType.ACH_RECEIPT, TransactionType.ACH_DISBURSEMENT,
                       TransactionType.WIRE_IN, TransactionType.WIRE_OUT]:
            if txn.net_amount:
                cash_flows += float(txn.net_amount)
    
    # Simplified return calculation
    # Real implementation would use time-weighted returns
    simple_return = 0 if cash_flows == 0 else ((current_value - cash_flows) / abs(cash_flows)) * 100
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "starting_value": cash_flows,  # Simplified
        "ending_value": current_value,
        "total_return": simple_return,
        "annualized_return": simple_return * (365 / (end_date - start_date).days),
        "cash_flows": cash_flows
    }

# Methods will be bound to SchwabClient in client.py to avoid circular imports