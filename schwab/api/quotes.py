from typing import List, Optional, Union, Dict, Any
from datetime import datetime
import re
from ..models.quotes import QuoteResponse

class QuotesMixin:
    """Mixin class providing quote-related API methods"""
    
    def _clean_datetime_values(self, data: Any) -> Any:
        """Recursively clean datetime values in response data.
        
        Converts datetime objects and strings to the format expected by the models.
        """
        from datetime import datetime as dt
        
        if isinstance(data, dt):
            # Handle datetime objects at any level first
            # Convert to ISO format with Z suffix for UTC
            if data.tzinfo:
                # Remove timezone info and add Z
                iso_str = data.isoformat()
                # Handle different timezone formats
                if iso_str.endswith('+00:00'):
                    return iso_str[:-6] + 'Z'
                elif 'T' in iso_str and '+' in iso_str:
                    # Remove timezone offset
                    return iso_str.split('+')[0] + 'Z'
                elif 'T' in iso_str and '-' in iso_str.split('T')[1]:
                    # Handle negative timezone offset
                    return iso_str.split('T')[0] + 'T' + iso_str.split('T')[1].split('-')[0] + 'Z'
                else:
                    return iso_str.replace('+00:00', 'Z')
            else:
                return data.isoformat() + 'Z'
        elif isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                # Always clean the value recursively
                cleaned[key] = self._clean_datetime_values(value)
            return cleaned
        elif isinstance(data, list):
            return [self._clean_datetime_values(item) for item in data]
        else:
            return data
    
    def _build_quote_params(self, symbols: Union[str, List[str]], fields: Optional[List[str]] = None, 
                           indicative: Optional[bool] = None) -> Dict[str, Any]:
        """Build the parameters for the quotes endpoint"""
        if isinstance(symbols, list):
            symbols = ','.join(symbols)
            
        params = {"symbols": symbols}
        
        if fields:
            params["fields"] = ','.join(fields)
        if indicative is not None:
            params["indicative"] = indicative
            
        return params

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
        params = self._build_quote_params(symbols, fields, indicative)
        
        # We're in sync context (get_quotes is not async)
        response = self._get("/marketdata/v1/quotes", params=params)
        
        # Clean datetime values before parsing  
        cleaned_response = self._clean_datetime_values(response)
        
        # Use model_validate with a custom config to handle datetime fields
        try:
            return QuoteResponse.model_validate(cleaned_response)
        except Exception as e:
            # If validation fails due to datetime issues, try converting the response manually
            if "datetime" in str(e) and "pattern" in str(e):
                # For each quote in the response, ensure fundamental date fields are strings
                if isinstance(cleaned_response, dict):
                    for symbol, quote_data in cleaned_response.items():
                        if isinstance(quote_data, dict) and 'fundamental' in quote_data:
                            fundamental = quote_data['fundamental']
                            if isinstance(fundamental, dict):
                                # Convert any datetime fields to ISO format strings
                                date_fields = ['declarationDate', 'divPayDate', 'nextDivExDate', 'nextDivPayDate']
                                for field in date_fields:
                                    if field in fundamental:
                                        value = fundamental[field]
                                        if hasattr(value, 'isoformat'):
                                            fundamental[field] = value.isoformat() + 'Z'
                                        elif isinstance(value, str) and not value.endswith('Z'):
                                            fundamental[field] = value + 'Z'
                
                return QuoteResponse.model_validate(cleaned_response)
            else:
                raise

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
        params = self._build_quote_params(symbols, fields, indicative)
        response = await self._async_get("/marketdata/v1/quotes", params=params)
        # Clean datetime values before parsing
        cleaned_response = self._clean_datetime_values(response)
        
        # Use model_validate with a custom config to handle datetime fields
        try:
            return QuoteResponse.model_validate(cleaned_response)
        except Exception as e:
            # If validation fails due to datetime issues, try converting the response manually
            if "datetime" in str(e) and "pattern" in str(e):
                # For each quote in the response, ensure fundamental date fields are strings
                if isinstance(cleaned_response, dict):
                    for symbol, quote_data in cleaned_response.items():
                        if isinstance(quote_data, dict) and 'fundamental' in quote_data:
                            fundamental = quote_data['fundamental']
                            if isinstance(fundamental, dict):
                                # Convert any datetime fields to ISO format strings
                                date_fields = ['declarationDate', 'divPayDate', 'nextDivExDate', 'nextDivPayDate']
                                for field in date_fields:
                                    if field in fundamental:
                                        value = fundamental[field]
                                        if hasattr(value, 'isoformat'):
                                            fundamental[field] = value.isoformat() + 'Z'
                                        elif isinstance(value, str) and not value.endswith('Z'):
                                            fundamental[field] = value + 'Z'
                
                return QuoteResponse.model_validate(cleaned_response)
            else:
                raise
    
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
            "symbol": symbol,
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
            
        try:
            if hasattr(self, '_make_request'):
                response = self._make_request("GET", "/marketdata/v1/pricehistory", params=params)
            else:
                response = self._get("/marketdata/v1/pricehistory", params=params)
            return response
        except Exception as e:
            # Check if this is a datetime validation error
            if "datetime" in str(e) and "pattern" in str(e):
                # Re-raise with additional context
                import traceback
                raise Exception(f"Datetime format issue from API: {str(e)}") from e
            raise
    
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
            
        params = {"markets": markets}
        if date:
            params["date"] = date.strftime('%Y-%m-%d')
            
        if hasattr(self, '_make_request'):
            return self._make_request("GET", "/marketdata/v1/markets", params=params)
        else:
            return self._get("/marketdata/v1/markets", params=params)
    
    def get_single_market_hours(self, market_id: str, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get market hours for a specific market.
        
        Args:
            market_id: The market ID (equity, option, bond, future, forex)
            date: Optional date to get market hours for (default: today)
            
        Returns:
            Dictionary containing market hours information
        """
        params = {}
        if date:
            params["date"] = date.strftime('%Y-%m-%d')
            
        if hasattr(self, '_make_request'):
            return self._make_request("GET", f"/marketdata/v1/markets/{market_id}", params=params or None)
        else:
            return self._get(f"/marketdata/v1/markets/{market_id}", params=params or None)
    
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
        params = {"sort": sort, "frequency": frequency}
        
        if hasattr(self, '_make_request'):
            return self._make_request("GET", f"/marketdata/v1/movers/{symbol_id}", params=params)
        else:
            return self._get(f"/marketdata/v1/movers/{symbol_id}", params=params)
    
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
        params = {"symbol": symbol, "projection": projection}
        
        if hasattr(self, '_make_request'):
            return self._make_request("GET", "/marketdata/v1/instruments", params=params)
        else:
            return self._get("/marketdata/v1/instruments", params=params)
    
    def get_instrument_by_cusip(self, cusip_id: str) -> Dict[str, Any]:
        """Get instrument details by CUSIP.
        
        Args:
            cusip_id: The CUSIP identifier
            
        Returns:
            Dictionary containing instrument details
        """
        url = f"/marketdata/v1/instruments/{cusip_id}"
        return self._make_request("GET", url) if hasattr(self, '_make_request') else self._get(url)