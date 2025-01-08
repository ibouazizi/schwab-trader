from typing import List, Optional
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field
from .base import SchwabBaseModel

class InstrumentType(str, Enum):
    SWEEP_VEHICLE = "SWEEP_VEHICLE"
    # Note: Other instrument types are missing from the API documentation
    # They should be added here when discovered

class Instrument(SchwabBaseModel):
    """Financial instrument model."""
    cusip: Optional[str] = None
    symbol: str
    description: str
    instrument_id: int = Field(..., alias="instrumentId")
    net_change: Decimal
    type: InstrumentType

class Position(SchwabBaseModel):
    """Position model."""
    short_quantity: Decimal = Field(0, alias="shortQuantity")
    average_price: Decimal = Field(..., alias="averagePrice")
    current_day_profit_loss: Decimal = Field(..., alias="currentDayProfitLoss")
    current_day_profit_loss_percentage: Decimal = Field(..., alias="currentDayProfitLossPercentage")
    long_quantity: Decimal = Field(0, alias="longQuantity")
    settled_long_quantity: Decimal = Field(0, alias="settledLongQuantity")
    settled_short_quantity: Decimal = Field(0, alias="settledShortQuantity")
    aged_quantity: Decimal = Field(0, alias="agedQuantity")
    instrument: Instrument
    market_value: Decimal = Field(..., alias="marketValue")
    maintenance_requirement: Decimal = Field(..., alias="maintenanceRequirement")
    average_long_price: Decimal = Field(..., alias="averageLongPrice")
    average_short_price: Decimal = Field(..., alias="averageShortPrice")
    tax_lot_average_long_price: Decimal = Field(..., alias="taxLotAverageLongPrice")
    tax_lot_average_short_price: Decimal = Field(..., alias="taxLotAverageShortPrice")
    long_open_profit_loss: Decimal = Field(..., alias="longOpenProfitLoss")
    short_open_profit_loss: Decimal = Field(..., alias="shortOpenProfitLoss")
    previous_session_long_quantity: Decimal = Field(..., alias="previousSessionLongQuantity")
    previous_session_short_quantity: Decimal = Field(..., alias="previousSessionShortQuantity")
    current_day_cost: Decimal = Field(..., alias="currentDayCost")

class InitialBalances(SchwabBaseModel):
    """Initial balances model."""
    accrued_interest: Decimal = Field(..., alias="accruedInterest")
    available_funds_non_marginable_trade: Decimal = Field(..., alias="availableFundsNonMarginableTrade")
    bond_value: Decimal = Field(..., alias="bondValue")
    buying_power: Decimal
    cash_balance: Decimal = Field(..., alias="cashBalance")
    cash_available_for_trading: Decimal = Field(..., alias="cashAvailableForTrading")
    cash_receipts: Decimal = Field(..., alias="cashReceipts")
    day_trading_buying_power: Decimal = Field(..., alias="dayTradingBuyingPower")
    day_trading_buying_power_call: Decimal = Field(..., alias="dayTradingBuyingPowerCall")
    day_trading_equity_call: Decimal = Field(..., alias="dayTradingEquityCall")
    equity: Decimal
    equity_percentage: Decimal = Field(..., alias="equityPercentage")
    liquidation_value: Decimal = Field(..., alias="liquidationValue")
    long_margin_value: Decimal = Field(..., alias="longMarginValue")
    long_option_market_value: Decimal = Field(..., alias="longOptionMarketValue")
    long_stock_value: Decimal = Field(..., alias="longStockValue")
    maintenance_call: Decimal = Field(..., alias="maintenanceCall")
    maintenance_requirement: Decimal = Field(..., alias="maintenanceRequirement")
    margin: Decimal
    margin_equity: Decimal = Field(..., alias="marginEquity")
    money_market_fund: Decimal = Field(..., alias="moneyMarketFund")
    mutual_fund_value: Decimal = Field(..., alias="mutualFundValue")
    reg_t_call: Decimal = Field(..., alias="regTCall")
    short_margin_value: Decimal = Field(..., alias="shortMarginValue")
    short_option_market_value: Decimal = Field(..., alias="shortOptionMarketValue")
    short_stock_value: Decimal = Field(..., alias="shortStockValue")
    total_cash: Decimal = Field(..., alias="totalCash")
    is_in_call: bool = Field(..., alias="isInCall")
    unsettled_cash: Decimal = Field(..., alias="unsettledCash")
    pending_deposits: Decimal = Field(..., alias="pendingDeposits")
    margin_balance: Decimal = Field(..., alias="marginBalance")
    short_balance: Decimal = Field(..., alias="shortBalance")
    account_value: Decimal = Field(..., alias="accountValue")

class CurrentBalances(SchwabBaseModel):
    """Current balances model."""
    available_funds: Decimal = Field(..., alias="availableFunds")
    available_funds_non_marginable_trade: Decimal = Field(..., alias="availableFundsNonMarginableTrade")
    buying_power: Decimal = Field(..., alias="buyingPower")
    buying_power_non_marginable_trade: Decimal = Field(..., alias="buyingPowerNonMarginableTrade")
    day_trading_buying_power: Decimal = Field(..., alias="dayTradingBuyingPower")
    day_trading_buying_power_call: Decimal = Field(..., alias="dayTradingBuyingPowerCall")
    equity: Decimal
    equity_percentage: Decimal = Field(..., alias="equityPercentage")
    long_margin_value: Decimal = Field(..., alias="longMarginValue")
    maintenance_call: Decimal = Field(..., alias="maintenanceCall")
    maintenance_requirement: Decimal = Field(..., alias="maintenanceRequirement")
    margin_balance: Decimal = Field(..., alias="marginBalance")
    reg_t_call: Decimal = Field(..., alias="regTCall")
    short_balance: Decimal = Field(..., alias="shortBalance")
    short_margin_value: Decimal = Field(..., alias="shortMarginValue")
    sma: Decimal
    is_in_call: bool = Field(..., alias="isInCall")
    stock_buying_power: Decimal = Field(..., alias="stockBuyingPower")
    option_buying_power: Decimal = Field(..., alias="optionBuyingPower")

class ProjectedBalances(CurrentBalances):
    """Projected balances model - inherits from CurrentBalances as they have the same structure."""
    pass

class SecuritiesAccount(SchwabBaseModel):
    """Securities account model."""
    account_number: str = Field(..., alias="accountNumber")
    round_trips: int = Field(..., alias="roundTrips")
    is_day_trader: bool = Field(..., alias="isDayTrader")
    is_closing_only_restricted: bool = Field(..., alias="isClosingOnlyRestricted")
    pfcb_flag: bool = Field(..., alias="pfcbFlag")
    positions: Optional[List[Position]] = None
    initial_balances: InitialBalances = Field(..., alias="initialBalances")
    current_balances: CurrentBalances = Field(..., alias="currentBalances")
    projected_balances: ProjectedBalances = Field(..., alias="projectedBalances")

class Account(SchwabBaseModel):
    """Account model."""
    securities_account: SecuritiesAccount = Field(..., alias="securitiesAccount")
