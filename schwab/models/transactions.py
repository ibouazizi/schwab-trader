"""Transaction models for Schwab API."""
from typing import List, Optional, Union, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field

from .base import SchwabBaseModel

class TransactionType(str, Enum):
    """Transaction type enumeration."""
    TRADE = "TRADE"
    RECEIVE_AND_DELIVER = "RECEIVE_AND_DELIVER" 
    DIVIDEND_OR_INTEREST = "DIVIDEND_OR_INTEREST"
    ACH_RECEIPT = "ACH_RECEIPT"
    ACH_DISBURSEMENT = "ACH_DISBURSEMENT"
    CASH_RECEIPT = "CASH_RECEIPT"
    CASH_DISBURSEMENT = "CASH_DISBURSEMENT"
    ELECTRONIC_FUND = "ELECTRONIC_FUND"
    WIRE_OUT = "WIRE_OUT"
    WIRE_IN = "WIRE_IN"
    JOURNAL = "JOURNAL"
    MEMORANDUM = "MEMORANDUM"
    MARGIN_CALL = "MARGIN_CALL"
    MONEY_MARKET = "MONEY_MARKET"
    SMA_ADJUSTMENT = "SMA_ADJUSTMENT"

class TransactionStatus(str, Enum):
    """Transaction status enumeration."""
    VALID = "VALID"
    INVALID = "INVALID"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"

class SubAccount(str, Enum):
    """Sub-account type enumeration."""
    CASH = "CASH"
    MARGIN = "MARGIN"
    SHORT = "SHORT"
    DIV = "DIV"
    INCOME = "INCOME"
    UNKNOWN = "UNKNOWN"

class ActivityType(str, Enum):
    """Activity type enumeration."""
    ACTIVITY_CORRECTION = "ACTIVITY_CORRECTION"
    EXECUTION = "EXECUTION"
    ORDER_ACTION = "ORDER_ACTION"
    TRANSFER = "TRANSFER"
    UNKNOWN = "UNKNOWN"

class UserType(str, Enum):
    """User type enumeration."""
    ADVISOR_USER = "ADVISOR_USER"
    BROKER_USER = "BROKER_USER"
    CLIENT_USER = "CLIENT_USER"
    SYSTEM_USER = "SYSTEM_USER"
    UNKNOWN = "UNKNOWN"

class FeeType(str, Enum):
    """Fee type enumeration."""
    COMMISSION = "COMMISSION"
    SEC_FEE = "SEC_FEE"
    STR_FEE = "STR_FEE"
    R_FEE = "R_FEE"
    CDSC_FEE = "CDSC_FEE"
    OPT_REG_FEE = "OPT_REG_FEE"
    ADDITIONAL_FEE = "ADDITIONAL_FEE"
    MISCELLANEOUS_FEE = "MISCELLANEOUS_FEE"
    FTT = "FTT"
    FUTURES_CLEARING_FEE = "FUTURES_CLEARING_FEE"
    FUTURES_DESK_OFFICE_FEE = "FUTURES_DESK_OFFICE_FEE"
    FUTURES_EXCHANGE_FEE = "FUTURES_EXCHANGE_FEE"
    FUTURES_GLOBEX_FEE = "FUTURES_GLOBEX_FEE"
    FUTURES_NFA_FEE = "FUTURES_NFA_FEE"
    FUTURES_PIT_BROKERAGE_FEE = "FUTURES_PIT_BROKERAGE_FEE"
    FUTURES_TRANSACTION_FEE = "FUTURES_TRANSACTION_FEE"
    LOW_PROCEEDS_COMMISSION = "LOW_PROCEEDS_COMMISSION"
    BASE_CHARGE = "BASE_CHARGE"
    GENERAL_CHARGE = "GENERAL_CHARGE"
    GST_FEE = "GST_FEE"
    TAF_FEE = "TAF_FEE"
    INDEX_OPTION_FEE = "INDEX_OPTION_FEE"
    TEFRA_TAX = "TEFRA_TAX"
    STATE_TAX = "STATE_TAX"
    UNKNOWN = "UNKNOWN"

class TransactionBaseInstrument(SchwabBaseModel):
    """Base transaction instrument model."""
    asset_type: str = Field(..., alias="assetType")
    cusip: Optional[str] = None
    symbol: Optional[str] = None
    description: Optional[str] = None
    instrument_id: Optional[int] = Field(None, alias="instrumentId")
    net_change: Optional[Decimal] = Field(None, alias="netChange")

class TransactionCashEquivalent(TransactionBaseInstrument):
    """Cash equivalent instrument model."""
    type: str = Field(..., alias="type")

class CollectiveInvestment(TransactionBaseInstrument):
    """Collective investment instrument model."""
    type: str = Field(..., alias="type")

class Currency(TransactionBaseInstrument):
    """Currency instrument model."""
    pass

class TransactionEquity(TransactionBaseInstrument):
    """Equity instrument model."""
    type: str = Field(..., alias="type")

class TransactionFixedIncome(TransactionBaseInstrument):
    """Fixed income instrument model."""
    type: str = Field(..., alias="type")
    maturity_date: Optional[datetime] = Field(None, alias="maturityDate")
    factor: Optional[Decimal] = None
    multiplier: Optional[Decimal] = None
    variable_rate: Optional[Decimal] = Field(None, alias="variableRate")

class Forex(TransactionBaseInstrument):
    """Forex instrument model."""
    type: str = Field(..., alias="type")
    base_currency: Currency = Field(..., alias="baseCurrency")
    counter_currency: Currency = Field(..., alias="counterCurrency")

class Future(TransactionBaseInstrument):
    """Future instrument model."""
    active_contract: bool = Field(False, alias="activeContract")
    type: str = Field(..., alias="type")
    expiration_date: Optional[datetime] = Field(None, alias="expirationDate")
    last_trading_date: Optional[datetime] = Field(None, alias="lastTradingDate")
    first_notice_date: Optional[datetime] = Field(None, alias="firstNoticeDate")
    multiplier: Optional[Decimal] = None

class Index(TransactionBaseInstrument):
    """Index instrument model."""
    active_contract: bool = Field(False, alias="activeContract")
    type: str = Field(..., alias="type")

class TransactionMutualFund(TransactionBaseInstrument):
    """Mutual fund instrument model."""
    fund_family_name: Optional[str] = Field(None, alias="fundFamilyName")
    fund_family_symbol: Optional[str] = Field(None, alias="fundFamilySymbol")
    fund_group: Optional[str] = Field(None, alias="fundGroup")
    type: str = Field(..., alias="type")
    exchange_cutoff_time: Optional[datetime] = Field(None, alias="exchangeCutoffTime")
    purchase_cutoff_time: Optional[datetime] = Field(None, alias="purchaseCutoffTime")
    redemption_cutoff_time: Optional[datetime] = Field(None, alias="redemptionCutoffTime")

class TransactionAPIOptionDeliverable(SchwabBaseModel):
    """Option deliverable model."""
    root_symbol: Optional[str] = Field(None, alias="rootSymbol")
    strike_percent: Optional[int] = Field(None, alias="strikePercent")
    deliverable_number: Optional[int] = Field(None, alias="deliverableNumber")
    deliverable_units: Optional[Decimal] = Field(None, alias="deliverableUnits")
    deliverable: Optional[Dict[str, Any]] = None
    asset_type: Optional[str] = Field(None, alias="assetType")

class TransactionOption(TransactionBaseInstrument):
    """Option instrument model."""
    expiration_date: Optional[datetime] = Field(None, alias="expirationDate")
    option_deliverables: Optional[List[TransactionAPIOptionDeliverable]] = Field(None, alias="optionDeliverables")
    option_premium_multiplier: Optional[int] = Field(None, alias="optionPremiumMultiplier")
    put_call: str = Field(..., alias="putCall")
    strike_price: Decimal = Field(..., alias="strikePrice")
    type: str = Field(..., alias="type")
    underlying_symbol: Optional[str] = Field(None, alias="underlyingSymbol")
    underlying_cusip: Optional[str] = Field(None, alias="underlyingCusip")
    deliverable: Optional[Dict[str, Any]] = None

class Product(TransactionBaseInstrument):
    """Product instrument model."""
    type: str = Field(..., alias="type")

class UserDetails(SchwabBaseModel):
    """User details model."""
    cd_domain_id: Optional[str] = Field(None, alias="cdDomainId")
    login: Optional[str] = None
    type: UserType
    user_id: Optional[int] = Field(None, alias="userId")
    system_user_name: Optional[str] = Field(None, alias="systemUserName")
    first_name: Optional[str] = Field(None, alias="firstName")
    last_name: Optional[str] = Field(None, alias="lastName")
    broker_rep_code: Optional[str] = Field(None, alias="brokerRepCode")

class TransferItem(SchwabBaseModel):
    """Transfer item model."""
    instrument: Dict[str, Any]  # TransactionInstrument Union type - complex to implement
    amount: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    price: Optional[Decimal] = None
    fee_type: Optional[FeeType] = Field(None, alias="feeType")
    position_effect: Optional[str] = Field(None, alias="positionEffect")

class Transaction(SchwabBaseModel):
    """Transaction model."""
    activity_id: int = Field(..., alias="activityId")
    time: datetime
    user: UserDetails
    description: Optional[str] = None
    account_number: str = Field(..., alias="accountNumber")
    type: TransactionType
    status: TransactionStatus
    sub_account: Optional[SubAccount] = Field(None, alias="subAccount")
    trade_date: Optional[datetime] = Field(None, alias="tradeDate")
    settlement_date: Optional[datetime] = Field(None, alias="settlementDate")
    position_id: Optional[int] = Field(None, alias="positionId")
    order_id: Optional[int] = Field(None, alias="orderId")
    net_amount: Optional[Decimal] = Field(None, alias="netAmount")
    activity_type: ActivityType = Field(..., alias="activityType")
    transfer_items: Optional[List[TransferItem]] = Field(None, alias="transferItems")

class TransactionList(SchwabBaseModel):
    """List of transactions."""
    transactions: List[Transaction]