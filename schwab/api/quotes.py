from typing import List, Optional, Union
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