def create_stop_limit_order(
    self,
    symbol: str,
    quantity: Union[int, Decimal],
    stop_price: Union[float, Decimal],
    limit_price: Union[float, Decimal],
    instruction: OrderInstruction,
    description: Optional[str] = None,
    instrument_id: Optional[int] = None,
    session: OrderSession = OrderSession.NORMAL,
    duration: OrderDuration = OrderDuration.DAY,
    requested_destination: Optional[RequestedDestination] = None,
    tax_lot_method: Optional[TaxLotMethod] = None,
    special_instruction: Optional[SpecialInstruction] = None
) -> Order:
    """Create a stop-limit order.
    
    Args:
        symbol: The symbol to trade
        quantity: The quantity to trade
        stop_price: The stop price
        limit_price: The limit price
        instruction: BUY or SELL
        description: Optional description of the instrument
        instrument_id: Optional instrument ID
        session: Order session (default: NORMAL)
        duration: Order duration (default: DAY)
        requested_destination: Optional trading destination
        tax_lot_method: Optional tax lot method
        special_instruction: Optional special instruction
        
    Returns:
        Order object ready to be placed
    """
    quantity = Decimal(str(quantity))
    stop_price = Decimal(str(stop_price))
    limit_price = Decimal(str(limit_price))
    return Order(
        session=session,
        duration=duration,
        order_type=OrderType.STOP_LIMIT,
        complex_order_strategy_type=ComplexOrderStrategyType.NONE,
        quantity=quantity,
        filled_quantity=Decimal("0"),
        remaining_quantity=quantity,
        requested_destination=requested_destination,
        stop_price=stop_price,
        stop_price_link_basis=StopPriceLinkBasis.MANUAL,
        stop_price_link_type=StopPriceLinkType.VALUE,
        stop_type=StopType.STANDARD,
        price=limit_price,
        tax_lot_method=tax_lot_method,
        special_instruction=special_instruction,
        order_strategy_type=OrderStrategyType.SINGLE,
        order_leg_collection=[
            OrderLeg(
                order_leg_type=OrderLegType.EQUITY,
                leg_id=1,
                instrument={
                    "symbol": symbol,
                    "description": description or symbol,
                    "instrument_id": instrument_id or 0,
                    "net_change": Decimal("0"),
                    "type": "EQUITY"
                },
                instruction=instruction,
                position_effect=PositionEffect.OPENING,
                quantity=quantity,
                quantity_type=QuantityType.ALL_SHARES,
                div_cap_gains=DividendCapitalGains.REINVEST
            )
        ]
    )

def create_trailing_stop_order(
    self,
    symbol: str,
    quantity: Union[int, Decimal],
    stop_price_offset: Union[float, Decimal],
    instruction: OrderInstruction,
    description: Optional[str] = None,
    instrument_id: Optional[int] = None,
    session: OrderSession = OrderSession.NORMAL,
    duration: OrderDuration = OrderDuration.DAY,
    requested_destination: Optional[RequestedDestination] = None,
    tax_lot_method: Optional[TaxLotMethod] = None,
    special_instruction: Optional[SpecialInstruction] = None
) -> Order:
    """Create a trailing stop order.
    
    Args:
        symbol: The symbol to trade
        quantity: The quantity to trade
        stop_price_offset: The trailing amount
        instruction: BUY or SELL
        description: Optional description of the instrument
        instrument_id: Optional instrument ID
        session: Order session (default: NORMAL)
        duration: Order duration (default: DAY)
        requested_destination: Optional trading destination
        tax_lot_method: Optional tax lot method
        special_instruction: Optional special instruction
        
    Returns:
        Order object ready to be placed
    """
    quantity = Decimal(str(quantity))
    stop_price_offset = Decimal(str(stop_price_offset))
    return Order(
        session=session,
        duration=duration,
        order_type=OrderType.TRAILING_STOP,
        complex_order_strategy_type=ComplexOrderStrategyType.NONE,
        quantity=quantity,
        filled_quantity=Decimal("0"),
        remaining_quantity=quantity,
        requested_destination=requested_destination,
        stop_price_offset=stop_price_offset,
        stop_price_link_basis=StopPriceLinkBasis.MANUAL,
        stop_price_link_type=StopPriceLinkType.VALUE,
        stop_type=StopType.STANDARD,
        tax_lot_method=tax_lot_method,
        special_instruction=special_instruction,
        order_strategy_type=OrderStrategyType.SINGLE,
        order_leg_collection=[
            OrderLeg(
                order_leg_type=OrderLegType.EQUITY,
                leg_id=1,
                instrument={
                    "symbol": symbol,
                    "description": description or symbol,
                    "instrument_id": instrument_id or 0,
                    "net_change": Decimal("0"),
                    "type": "EQUITY"
                },
                instruction=instruction,
                position_effect=PositionEffect.OPENING,
                quantity=quantity,
                quantity_type=QuantityType.ALL_SHARES,
                div_cap_gains=DividendCapitalGains.REINVEST
            )
        ]
    )

def create_market_on_close_order(
    self,
    symbol: str,
    quantity: Union[int, Decimal],
    instruction: OrderInstruction,
    description: Optional[str] = None,
    instrument_id: Optional[int] = None,
    session: OrderSession = OrderSession.NORMAL,
    requested_destination: Optional[RequestedDestination] = None,
    tax_lot_method: Optional[TaxLotMethod] = None,
    special_instruction: Optional[SpecialInstruction] = None
) -> Order:
    """Create a market-on-close order.
    
    Args:
        symbol: The symbol to trade
        quantity: The quantity to trade
        instruction: BUY or SELL
        description: Optional description of the instrument
        instrument_id: Optional instrument ID
        session: Order session (default: NORMAL)
        requested_destination: Optional trading destination
        tax_lot_method: Optional tax lot method
        special_instruction: Optional special instruction
        
    Returns:
        Order object ready to be placed
    """
    quantity = Decimal(str(quantity))
    return Order(
        session=session,
        duration=OrderDuration.DAY,  # MOC orders must be DAY orders
        order_type=OrderType.MARKET_ON_CLOSE,
        complex_order_strategy_type=ComplexOrderStrategyType.NONE,
        quantity=quantity,
        filled_quantity=Decimal("0"),
        remaining_quantity=quantity,
        requested_destination=requested_destination,
        tax_lot_method=tax_lot_method,
        special_instruction=special_instruction,
        order_strategy_type=OrderStrategyType.SINGLE,
        order_leg_collection=[
            OrderLeg(
                order_leg_type=OrderLegType.EQUITY,
                leg_id=1,
                instrument={
                    "symbol": symbol,
                    "description": description or symbol,
                    "instrument_id": instrument_id or 0,
                    "net_change": Decimal("0"),
                    "type": "EQUITY"
                },
                instruction=instruction,
                position_effect=PositionEffect.OPENING,
                quantity=quantity,
                quantity_type=QuantityType.ALL_SHARES,
                div_cap_gains=DividendCapitalGains.REINVEST
            )
        ]
    )

def create_limit_on_close_order(
    self,
    symbol: str,
    quantity: Union[int, Decimal],
    limit_price: Union[float, Decimal],
    instruction: OrderInstruction,
    description: Optional[str] = None,
    instrument_id: Optional[int] = None,
    session: OrderSession = OrderSession.NORMAL,
    requested_destination: Optional[RequestedDestination] = None,
    tax_lot_method: Optional[TaxLotMethod] = None,
    special_instruction: Optional[SpecialInstruction] = None
) -> Order:
    """Create a limit-on-close order.
    
    Args:
        symbol: The symbol to trade
        quantity: The quantity to trade
        limit_price: The limit price
        instruction: BUY or SELL
        description: Optional description of the instrument
        instrument_id: Optional instrument ID
        session: Order session (default: NORMAL)
        requested_destination: Optional trading destination
        tax_lot_method: Optional tax lot method
        special_instruction: Optional special instruction
        
    Returns:
        Order object ready to be placed
    """
    quantity = Decimal(str(quantity))
    limit_price = Decimal(str(limit_price))
    return Order(
        session=session,
        duration=OrderDuration.DAY,  # LOC orders must be DAY orders
        order_type=OrderType.LIMIT_ON_CLOSE,
        complex_order_strategy_type=ComplexOrderStrategyType.NONE,
        quantity=quantity,
        filled_quantity=Decimal("0"),
        remaining_quantity=quantity,
        requested_destination=requested_destination,
        price=limit_price,
        tax_lot_method=tax_lot_method,
        special_instruction=special_instruction,
        order_strategy_type=OrderStrategyType.SINGLE,
        order_leg_collection=[
            OrderLeg(
                order_leg_type=OrderLegType.EQUITY,
                leg_id=1,
                instrument={
                    "symbol": symbol,
                    "description": description or symbol,
                    "instrument_id": instrument_id or 0,
                    "net_change": Decimal("0"),
                    "type": "EQUITY"
                },
                instruction=instruction,
                position_effect=PositionEffect.OPENING,
                quantity=quantity,
                quantity_type=QuantityType.ALL_SHARES,
                div_cap_gains=DividendCapitalGains.REINVEST
            )
        ]
    )
