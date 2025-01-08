from typing import Dict, Optional, List, Union
from enum import Enum
from datetime import datetime
from pydantic import RootModel
from .base import BaseModel

class AssetMainType(str, Enum):
    EQUITY = "EQUITY"
    MUTUAL_FUND = "MUTUAL_FUND"
    INDEX = "INDEX"
    OPTION = "OPTION"

class QuoteType(str, Enum):
    NBBO = "NBBO"

class SecurityStatus(str, Enum):
    NORMAL = "Normal"
    UNKNOWN = "Unknown"

class Reference(BaseModel):
    cusip: Optional[str] = None
    description: Optional[str] = None
    exchange: Optional[str] = None
    exchangeName: Optional[str] = None
    otcMarketTier: Optional[str] = None
    # Option specific fields
    contractType: Optional[str] = None
    daysToExpiration: Optional[int] = None
    expirationDay: Optional[int] = None
    expirationMonth: Optional[int] = None
    expirationYear: Optional[int] = None
    isPennyPilot: Optional[bool] = None
    lastTradingDay: Optional[int] = None
    multiplier: Optional[int] = None
    settlementType: Optional[str] = None
    strikePrice: Optional[float] = None
    underlying: Optional[str] = None
    uvExpirationType: Optional[str] = None

class Quote(BaseModel):
    weekHigh52: Optional[float] = None
    weekLow52: Optional[float] = None
    askMICId: Optional[str] = None
    askPrice: Optional[float] = None
    askSize: Optional[int] = None
    askTime: Optional[int] = None
    bidMICId: Optional[str] = None
    bidPrice: Optional[float] = None
    bidSize: Optional[int] = None
    bidTime: Optional[int] = None
    closePrice: Optional[float] = None
    highPrice: Optional[float] = None
    lastMICId: Optional[str] = None
    lastPrice: Optional[float] = None
    lastSize: Optional[int] = None
    lowPrice: Optional[float] = None
    mark: Optional[float] = None
    markChange: Optional[float] = None
    markPercentChange: Optional[float] = None
    netChange: Optional[float] = None
    netPercentChange: Optional[float] = None
    openPrice: Optional[float] = None
    quoteTime: Optional[int] = None
    securityStatus: Optional[SecurityStatus] = None
    totalVolume: Optional[int] = None
    tradeTime: Optional[int] = None
    volatility: Optional[float] = None
    # Mutual Fund specific
    nAV: Optional[float] = None
    # Option specific
    delta: Optional[float] = None
    gamma: Optional[float] = None
    impliedYield: Optional[float] = None
    indAskPrice: Optional[float] = None
    indBidPrice: Optional[float] = None
    indQuoteTime: Optional[int] = None
    moneyIntrinsicValue: Optional[float] = None
    openInterest: Optional[int] = None
    rho: Optional[float] = None
    theoreticalOptionValue: Optional[float] = None
    theta: Optional[float] = None
    timeValue: Optional[float] = None
    underlyingPrice: Optional[float] = None
    vega: Optional[float] = None

class Regular(BaseModel):
    regularMarketLastPrice: Optional[float] = None
    regularMarketLastSize: Optional[int] = None
    regularMarketNetChange: Optional[float] = None
    regularMarketPercentChange: Optional[float] = None
    regularMarketTradeTime: Optional[int] = None

class Fundamental(BaseModel):
    avg10DaysVolume: Optional[float] = None
    avg1YearVolume: Optional[float] = None
    declarationDate: Optional[datetime] = None
    divAmount: Optional[float] = None
    divExDate: Optional[datetime] = None
    divFreq: Optional[int] = None
    divPayAmount: Optional[float] = None
    divPayDate: Optional[datetime] = None
    divYield: Optional[float] = None
    eps: Optional[float] = None
    fundLeverageFactor: Optional[float] = None
    fundStrategy: Optional[str] = None
    nextDivExDate: Optional[datetime] = None
    nextDivPayDate: Optional[datetime] = None
    peRatio: Optional[float] = None

class QuoteData(BaseModel):
    assetMainType: Optional[AssetMainType] = None
    assetSubType: Optional[str] = None
    symbol: str
    quoteType: Optional[str] = None
    realtime: Optional[bool] = None
    ssid: Optional[int] = None
    reference: Optional[Reference] = None
    quote: Optional[Quote] = None
    regular: Optional[Regular] = None
    fundamental: Optional[Fundamental] = None

class QuoteResponse(RootModel):
    """Response model for quote endpoint containing a dictionary of symbols to their quote data"""
    root: Dict[str, QuoteData]

    def __iter__(self):
        return iter(self.root.items())

    def __getitem__(self, key):
        return self.root[key]