from typing import List, Optional, Union
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field

from .base import SchwabBaseModel
from .account import Instrument

class OrderStatus(str, Enum):
    """Order status enumeration."""
    AWAITING_PARENT_ORDER = "AWAITING_PARENT_ORDER"
    AWAITING_CONDITION = "AWAITING_CONDITION"
    AWAITING_STOP_CONDITION = "AWAITING_STOP_CONDITION"
    AWAITING_MANUAL_REVIEW = "AWAITING_MANUAL_REVIEW"
    ACCEPTED = "ACCEPTED"
    AWAITING_UR_OUT = "AWAITING_UR_OUT"
    PENDING_ACTIVATION = "PENDING_ACTIVATION"
    QUEUED = "QUEUED"
    WORKING = "WORKING"
    REJECTED = "REJECTED"
    PENDING_CANCEL = "PENDING_CANCEL"
    CANCELED = "CANCELED"
    PENDING_REPLACE = "PENDING_REPLACE"
    REPLACED = "REPLACED"
    FILLED = "FILLED"
    EXPIRED = "EXPIRED"
    NEW = "NEW"
    AWAITING_RELEASE_TIME = "AWAITING_RELEASE_TIME"
    PENDING_ACKNOWLEDGEMENT = "PENDING_ACKNOWLEDGEMENT"
    PENDING_RECALL = "PENDING_RECALL"
    UNKNOWN = "UNKNOWN"

class OrderSession(str, Enum):
    """Order session enumeration."""
    NORMAL = "NORMAL"
    # Add other session types when discovered

class OrderDuration(str, Enum):
    """Order duration enumeration."""
    DAY = "DAY"
    # Add other duration types when discovered

class OrderType(str, Enum):
    """Order type enumeration."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"
    CABINET = "CABINET"
    NON_MARKETABLE = "NON_MARKETABLE"
    MARKET_ON_CLOSE = "MARKET_ON_CLOSE"
    EXERCISE = "EXERCISE"
    TRAILING_STOP_LIMIT = "TRAILING_STOP_LIMIT"
    NET_DEBIT = "NET_DEBIT"
    NET_CREDIT = "NET_CREDIT"
    NET_ZERO = "NET_ZERO"
    LIMIT_ON_CLOSE = "LIMIT_ON_CLOSE"
    UNKNOWN = "UNKNOWN"  # Only for responses, not allowed in requests

class ComplexOrderStrategyType(str, Enum):
    """Complex order strategy type enumeration."""
    NONE = "NONE"
    COVERED = "COVERED"
    VERTICAL = "VERTICAL"
    BACK_RATIO = "BACK_RATIO"
    CALENDAR = "CALENDAR"
    DIAGONAL = "DIAGONAL"
    STRADDLE = "STRADDLE"
    STRANGLE = "STRANGLE"
    COLLAR_SYNTHETIC = "COLLAR_SYNTHETIC"
    BUTTERFLY = "BUTTERFLY"
    CONDOR = "CONDOR"
    IRON_CONDOR = "IRON_CONDOR"
    VERTICAL_ROLL = "VERTICAL_ROLL"
    COLLAR_WITH_STOCK = "COLLAR_WITH_STOCK"
    DOUBLE_DIAGONAL = "DOUBLE_DIAGONAL"
    UNBALANCED_BUTTERFLY = "UNBALANCED_BUTTERFLY"
    UNBALANCED_CONDOR = "UNBALANCED_CONDOR"
    UNBALANCED_IRON_CONDOR = "UNBALANCED_IRON_CONDOR"
    UNBALANCED_VERTICAL_ROLL = "UNBALANCED_VERTICAL_ROLL"
    MUTUAL_FUND_SWAP = "MUTUAL_FUND_SWAP"
    CUSTOM = "CUSTOM"

class RequestedDestination(str, Enum):
    """Requested destination enumeration."""
    INET = "INET"
    ECN_ARCA = "ECN_ARCA"
    CBOE = "CBOE"
    AMEX = "AMEX"
    PHLX = "PHLX"
    ISE = "ISE"
    BOX = "BOX"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    BATS = "BATS"
    C2 = "C2"
    AUTO = "AUTO"

class StopPriceLinkBasis(str, Enum):
    """Stop price link basis enumeration."""
    MANUAL = "MANUAL"
    # Add other basis types when discovered

class StopPriceLinkType(str, Enum):
    """Stop price link type enumeration."""
    VALUE = "VALUE"
    # Add other link types when discovered

class StopType(str, Enum):
    """Stop type enumeration."""
    STANDARD = "STANDARD"
    # Add other stop types when discovered

class PriceLinkBasis(str, Enum):
    """Price link basis enumeration."""
    MANUAL = "MANUAL"
    # Add other basis types when discovered

class PriceLinkType(str, Enum):
    """Price link type enumeration."""
    VALUE = "VALUE"
    # Add other link types when discovered

class TaxLotMethod(str, Enum):
    """Tax lot method enumeration."""
    FIFO = "FIFO"
    # Add other methods when discovered

class OrderLegType(str, Enum):
    """Order leg type enumeration."""
    EQUITY = "EQUITY"
    # Add other leg types when discovered

class OrderInstruction(str, Enum):
    """Order instruction enumeration."""
    BUY = "BUY"
    # Add other instructions when discovered

class PositionEffect(str, Enum):
    """Position effect enumeration."""
    OPENING = "OPENING"
    # Add other effects when discovered

class QuantityType(str, Enum):
    """Quantity type enumeration."""
    ALL_SHARES = "ALL_SHARES"
    # Add other types when discovered

class DividendCapitalGains(str, Enum):
    """Dividend capital gains enumeration."""
    REINVEST = "REINVEST"
    # Add other options when discovered

class SpecialInstruction(str, Enum):
    """Special instruction enumeration."""
    ALL_OR_NONE = "ALL_OR_NONE"
    # Add other instructions when discovered

class OrderStrategyType(str, Enum):
    """Order strategy type enumeration."""
    SINGLE = "SINGLE"
    # Add other strategy types when discovered

class SettlementInstruction(str, Enum):
    """Settlement instruction enumeration."""
    REGULAR = "REGULAR"
    CASH = "CASH"
    NEXT_DAY = "NEXT_DAY"
    UNKNOWN = "UNKNOWN"

class AmountIndicator(str, Enum):
    """Amount indicator enumeration."""
    DOLLARS = "DOLLARS"
    # Add other indicators when discovered

class ActivityType(str, Enum):
    """Activity type enumeration."""
    EXECUTION = "EXECUTION"
    # Add other activity types when discovered

class ExecutionType(str, Enum):
    """Execution type enumeration."""
    FILL = "FILL"
    # Add other execution types when discovered

class ExecutionLeg(SchwabBaseModel):
    """Execution leg model."""
    leg_id: int = Field(..., alias="legId")
    price: Decimal
    quantity: Decimal
    mismarked_quantity: Decimal = Field(..., alias="mismarkedQuantity")
    instrument_id: int = Field(..., alias="instrumentId")
    time: datetime

class OrderActivity(SchwabBaseModel):
    """Order activity model."""
    activity_type: ActivityType = Field(..., alias="activityType")
    execution_type: ExecutionType = Field(..., alias="executionType")
    quantity: Decimal
    order_remaining_quantity: Decimal = Field(..., alias="orderRemainingQuantity")
    execution_legs: List[ExecutionLeg] = Field(..., alias="executionLegs")

class OrderLeg(SchwabBaseModel):
    """Order leg model."""
    order_leg_type: OrderLegType = Field(..., alias="orderLegType")
    leg_id: int = Field(..., alias="legId")
    instrument: Instrument
    instruction: OrderInstruction
    position_effect: PositionEffect = Field(..., alias="positionEffect")
    quantity: Decimal
    quantity_type: QuantityType = Field(..., alias="quantityType")
    div_cap_gains: DividendCapitalGains = Field(..., alias="divCapGains")
    to_symbol: Optional[str] = Field(None, alias="toSymbol")

class Order(SchwabBaseModel):
    """Order model."""
    session: OrderSession
    duration: OrderDuration
    order_type: OrderType = Field(..., alias="orderType")
    cancel_time: Optional[datetime] = Field(None, alias="cancelTime")
    complex_order_strategy_type: ComplexOrderStrategyType = Field(..., alias="complexOrderStrategyType")
    quantity: Decimal
    filled_quantity: Decimal = Field(..., alias="filledQuantity")
    remaining_quantity: Decimal = Field(..., alias="remainingQuantity")
    requested_destination: Optional[RequestedDestination] = Field(None, alias="requestedDestination")
    destination_link_name: Optional[str] = Field(None, alias="destinationLinkName")
    release_time: Optional[datetime] = Field(None, alias="releaseTime")
    stop_price: Optional[Decimal] = Field(None, alias="stopPrice")
    stop_price_link_basis: Optional[StopPriceLinkBasis] = Field(None, alias="stopPriceLinkBasis")
    stop_price_link_type: Optional[StopPriceLinkType] = Field(None, alias="stopPriceLinkType")
    stop_price_offset: Optional[Decimal] = Field(None, alias="stopPriceOffset")
    stop_type: Optional[StopType] = Field(None, alias="stopType")
    price_link_basis: Optional[PriceLinkBasis] = Field(None, alias="priceLinkBasis")
    price_link_type: Optional[PriceLinkType] = Field(None, alias="priceLinkType")
    price: Optional[Decimal] = None
    tax_lot_method: Optional[TaxLotMethod] = Field(None, alias="taxLotMethod")
    order_leg_collection: List[OrderLeg] = Field(..., alias="orderLegCollection")
    activation_price: Optional[Decimal] = Field(None, alias="activationPrice")
    special_instruction: Optional[SpecialInstruction] = Field(None, alias="specialInstruction")
    order_strategy_type: OrderStrategyType = Field(..., alias="orderStrategyType")
    order_id: Optional[int] = Field(None, alias="orderId")
    cancelable: Optional[bool] = None
    editable: Optional[bool] = None
    status: Optional[OrderStatus] = None
    entered_time: Optional[datetime] = Field(None, alias="enteredTime")
    close_time: Optional[datetime] = Field(None, alias="closeTime")
    account_number: Optional[str] = Field(None, alias="accountNumber")
    order_activity_collection: Optional[List[OrderActivity]] = Field(None, alias="orderActivityCollection")
    replacing_order_collection: Optional[List[str]] = Field(None, alias="replacingOrderCollection")
    child_order_strategies: Optional[List[str]] = Field(None, alias="childOrderStrategies")
    status_description: Optional[str] = Field(None, alias="statusDescription")
    order_value: Optional[Decimal] = Field(None, alias="orderValue")
    sell_non_marginable_first: Optional[bool] = Field(None, alias="sellNonMarginableFirst")
    settlement_instruction: Optional[SettlementInstruction] = Field(None, alias="settlementInstruction")
    amount_indicator: Optional[AmountIndicator] = Field(None, alias="amountIndicator")

class OrderList(SchwabBaseModel):
    """List of orders."""
    orders: List[Order]
