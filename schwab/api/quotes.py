from typing import List, Optional, Union, Dict, Any
from datetime import datetime
from ..models.quotes import QuoteResponse

class QuotesMixin:
    """Mixin class providing quote-related API methods"""
    
    def _build_quote_url(self, symbols: Union[str, List[str]], fields: Optional[List[str]] = None, 
                        indicative: Optional[bool] = None) -> str:
        """Build the URL for the quotes endpoint with query parameters"""
        if isinstance(symbols, list):
            symbols = ','.join(symbols)
            
        url = f"/marketdata/v1/quotes?symbols={symbols}"
        
        if fields:
            url += f"&fields={','.join(fields)}"
        if indicative is not None:
            url += f"&indicative={str(indicative).lower()}"
            
        return url

    def get_quotes(self, symbols: Union[str, List[str]], 
                  fields: Optional[List[str]] = None,
                  indicative: Optional[bool] = None) -> QuoteResponse:
        """
        Get quotes for one or more symbols.
        
        Args:
            symbols: Single symbol string or list of symbol strings
            fields: Optional list of data fields to include. Available values:
                   ['quote', 'fundamental', 'extended', 'reference', 'regular']
            indicative: Include indicative symbol quotes for ETF symbols
        
        Returns:
            QuoteResponse object containing quote data for requested symbols
        """
        url = self._build_quote_url(symbols, fields, indicative)
        
        # Check if we're in async context
        if hasattr(self, '_async_get'):
            import asyncio
            if asyncio.iscoroutinefunction(self._async_get):
                # We're in async context
                response = asyncio.get_event_loop().run_until_complete(self._async_get(url))
            else:
                response = self._async_get(url)
        else:
            # We're in sync context
            response = self._get(url)
            
        return QuoteResponse.parse_obj(response)

    async def async_get_quotes(self, symbols: Union[str, List[str]], 
                             fields: Optional[List[str]] = None,
                             indicative: Optional[bool] = None) -> QuoteResponse:
        """
        Get quotes for one or more symbols asynchronously.
        
        Args:
            symbols: Single symbol string or list of symbol strings
            fields: Optional list of data fields to include. Available values:
                   ['quote', 'fundamental', 'extended', 'reference', 'regular']
            indicative: Include indicative symbol quotes for ETF symbols
        
        Returns:
            QuoteResponse object containing quote data for requested symbols
        """
        url = self._build_quote_url(symbols, fields, indicative)
        response = await self._async_get(url)
        return QuoteResponse.parse_obj(response)
    
    # Price History Methods
    def get_price_history(
        self,
        symbol: str,
        period_type: str = "day",
        period: int = 10,
        frequency_type: str = "minute",
        frequency: int = 5,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        need_extended_hours_data: bool = True,
        need_previous_close: bool = True
    ) -> Dict[str, Any]:
        """Get historical price data for a symbol.
        
        Args:
            symbol: The symbol to get price history for
            period_type: The type of period (day, month, year, ytd)
            period: The number of periods
            frequency_type: The type of frequency (minute, daily, weekly, monthly)
            frequency: The frequency value
            start_date: Optional start date (overrides period)
            end_date: Optional end date
            need_extended_hours_data: Include extended hours data
            need_previous_close: Include previous close price
            
        Returns:
            Dictionary containing candles data with OHLCV information
        """
        params = {
            "periodType": period_type,
            "period": period,
            "frequencyType": frequency_type,
            "frequency": frequency,
            "needExtendedHoursData": need_extended_hours_data,
            "needPreviousClose": need_previous_close
        }
        
        if start_date:
            params["startDate"] = int(start_date.timestamp() * 1000)
        if end_date:
            params["endDate"] = int(end_date.timestamp() * 1000)
            
        url = f"/marketdata/v1/pricehistory?symbol={symbol}"
        for key, value in params.items():
            url += f"&{key}={value}"
            
        return self._make_request("GET", url) if hasattr(self, '_make_request') else self._get(url)
    
    # Market Hours Methods
    def get_market_hours(self, markets: Union[str, List[str]], date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get market hours for specified markets.
        
        Args:
            markets: Single market or list of markets (equity, option, bond, future, forex)
            date: Optional date to get market hours for (default: today)
            
        Returns:
            Dictionary containing market hours for each market
        """
        if isinstance(markets, list):
            markets = ','.join(markets)
            
        url = f"/marketdata/v1/markets?markets={markets}"
        if date:
            url += f"&date={date.strftime('%Y-%m-%d')}"
            
        return self._make_request("GET", url) if hasattr(self, '_make_request') else self._get(url)
    
    def get_single_market_hours(self, market_id: str, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get market hours for a specific market.
        
        Args:
            market_id: The market ID (equity, option, bond, future, forex)
            date: Optional date to get market hours for (default: today)
            
        Returns:
            Dictionary containing market hours information
        """
        url = f"/marketdata/v1/markets/{market_id}"
        if date:
            url += f"?date={date.strftime('%Y-%m-%d')}"
            
        return self._make_request("GET", url) if hasattr(self, '_make_request') else self._get(url)
    
    # Movers Methods
    def get_movers(self, symbol_id: str, sort: str = "VOLUME", frequency: int = 5) -> Dict[str, Any]:
        """Get market movers for a specific index.
        
        Args:
            symbol_id: The index symbol ($DJI, $COMPX, $SPX)
            sort: Sort by VOLUME, TRADES, PERCENT_CHANGE_UP, PERCENT_CHANGE_DOWN
            frequency: The frequency to return movers (0, 1, 5, 10, 30, 60)
            
        Returns:
            Dictionary containing top gainers and losers
        """
        url = f"/marketdata/v1/movers/{symbol_id}?sort={sort}&frequency={frequency}"
        return self._make_request("GET", url) if hasattr(self, '_make_request') else self._get(url)
    
    # Instruments Methods
    def search_instruments(
        self,
        symbol: str,
        projection: str = "symbol-search"
    ) -> Dict[str, Any]:
        """Search for instruments by symbol or name.
        
        Args:
            symbol: Symbol or partial symbol to search for
            projection: Search type (symbol-search, symbol-regex, desc-search, desc-regex, search, fundamental)
            
        Returns:
            Dictionary containing matching instruments
        """
        url = f"/marketdata/v1/instruments?symbol={symbol}&projection={projection}"
        return self._make_request("GET", url) if hasattr(self, '_make_request') else self._get(url)
    
    def get_instrument_by_cusip(self, cusip_id: str) -> Dict[str, Any]:
        """Get instrument details by CUSIP.
        
        Args:
            cusip_id: The CUSIP identifier
            
        Returns:
            Dictionary containing instrument details
        """
        url = f"/marketdata/v1/instruments/{cusip_id}"
        return self._make_request("GET", url) if hasattr(self, '_make_request') else self._get(url)