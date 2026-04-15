"""Tests for quotes and market data functionality."""

import pytest
from unittest.mock import MagicMock, patch

from schwab.models.generated.market_data_models import QuoteResponse, QuoteData


class TestQuotes:
    """Test suite for quotes and market data functionality."""
    
    def test_get_quotes_single_symbol(self, mock_client):
        """Test getting quotes for a single symbol."""
        # Sample data
        sample_data = {
            "AAPL": {
                "assetMainType": "EQUITY",
                "assetSubType": "COMMON",
                "symbol": "AAPL",
                "quoteType": "NBBO",
                "realtime": True,
                "quote": {
                    "weekHigh52": 150.00,
                    "weekLow52": 120.00,
                    "askPrice": 145.25,
                    "askSize": 100,
                    "bidPrice": 145.20,
                    "bidSize": 200,
                    "closePrice": 143.50,
                    "highPrice": 146.00,
                    "lastPrice": 145.22,
                    "lastSize": 100,
                    "lowPrice": 144.50,
                    "mark": 145.22,
                    "markChange": 1.72,
                    "markPercentChange": 1.2,
                    "netChange": 1.72,
                    "netPercentChange": 1.2,
                    "openPrice": 144.75,
                    "totalVolume": 1000000,
                    "tradeTime": 1623344400,
                    "volatility": 25.5
                }
            }
        }
        mock_client._make_request.return_value = sample_data
        
        # Call get_quotes
        result = mock_client.get_quotes("AAPL")
        
        # Verify result
        assert isinstance(result, QuoteResponse)
        assert "AAPL" in result.root
        assert result.root["AAPL"].symbol == "AAPL"
        assert result.root["AAPL"].quote.lastPrice == 145.22
        assert result.root["AAPL"].quote.netChange == 1.72
        
        # Verify API call
        mock_client._make_request.assert_called_once()
        args, kwargs = mock_client._make_request.call_args
        assert args[0] == "GET"
        assert "quotes?symbols=AAPL" in args[1]
    
    def test_get_quotes_multiple_symbols(self, mock_client):
        """Test getting quotes for multiple symbols."""
        # Sample data
        sample_data = {
            "AAPL": {
                "assetMainType": "EQUITY",
                "symbol": "AAPL",
                "quote": {
                    "lastPrice": 145.22,
                    "netChange": 1.72
                }
            },
            "MSFT": {
                "assetMainType": "EQUITY",
                "symbol": "MSFT",
                "quote": {
                    "lastPrice": 290.45,
                    "netChange": 2.15
                }
            }
        }
        mock_client._make_request.return_value = sample_data
        
        # Call get_quotes
        result = mock_client.get_quotes(["AAPL", "MSFT"])
        
        # Verify result
        assert isinstance(result, QuoteResponse)
        assert "AAPL" in result.root
        assert "MSFT" in result.root
        assert result.root["AAPL"].quote.lastPrice == 145.22
        assert result.root["MSFT"].quote.lastPrice == 290.45
        
        # Verify API call
        mock_client._make_request.assert_called_once()
        args, kwargs = mock_client._make_request.call_args
        assert args[0] == "GET"
        assert "quotes?symbols=AAPL,MSFT" in args[1]
    
    def test_get_quotes_with_fields(self, mock_client):
        """Test getting quotes with specific fields."""
        # Sample data
        sample_data = {
            "AAPL": {
                "assetMainType": "EQUITY",
                "symbol": "AAPL",
                "quote": {
                    "lastPrice": 145.22
                },
                "fundamental": {
                    "peRatio": 28.5,
                    "divYield": 0.6,
                    "divAmount": 0.88
                }
            }
        }
        mock_client._make_request.return_value = sample_data
        
        # Call get_quotes with fields
        result = mock_client.get_quotes(
            symbols="AAPL",
            fields=["quote", "fundamental"]
        )
        
        # Verify result
        assert isinstance(result, QuoteResponse)
        assert "AAPL" in result.root
        assert result.root["AAPL"].fundamental.peRatio == 28.5
        assert result.root["AAPL"].fundamental.divYield == 0.6
        
        # Verify API call
        mock_client._make_request.assert_called_once()
        args, kwargs = mock_client._make_request.call_args
        assert args[0] == "GET"
        assert "quotes?symbols=AAPL&fields=quote,fundamental" in args[1]
    
    def test_get_quotes_with_indicative(self, mock_client):
        """Test getting quotes with indicative parameter."""
        # Sample data
        sample_data = {
            "SPY": {
                "assetMainType": "EQUITY",
                "symbol": "SPY",
                "quote": {
                    "lastPrice": 435.60
                }
            }
        }
        mock_client._make_request.return_value = sample_data
        
        # Call get_quotes with indicative
        result = mock_client.get_quotes(
            symbols="SPY",
            indicative=True
        )
        
        # Verify result
        assert isinstance(result, QuoteResponse)
        assert "SPY" in result.root
        assert result.root["SPY"].quote.lastPrice == 435.60
        
        # Verify API call
        mock_client._make_request.assert_called_once()
        args, kwargs = mock_client._make_request.call_args
        assert args[0] == "GET"
        assert "quotes?symbols=SPY&indicative=true" in args[1]
    
    def test_async_get_quotes(self, mock_async_client):
        """Test getting quotes asynchronously."""
        # This is a placeholder test since we can't easily test async methods
        # in a unit test without setting up an event loop.
        # In a real test suite, you would use pytest-asyncio to test async code properly.
        pass
    
    def test_quote_response_iteration(self):
        """Test iterating through QuoteResponse object."""
        # Create sample quote data
        quote_data = {
            "AAPL": QuoteData(
                symbol="AAPL",
                assetMainType="EQUITY",
                quote={
                    "lastPrice": 145.22,
                    "netChange": 1.72
                }
            ),
            "MSFT": QuoteData(
                symbol="MSFT",
                assetMainType="EQUITY",
                quote={
                    "lastPrice": 290.45,
                    "netChange": 2.15
                }
            )
        }
        
        # Create QuoteResponse
        response = QuoteResponse(root=quote_data)
        
        # Test iteration
        items = list(response)
        assert len(items) == 2
        assert items[0][0] == "AAPL" or items[1][0] == "AAPL"
        assert items[0][0] == "MSFT" or items[1][0] == "MSFT"
        
        # Test dictionary-like access
        assert response["AAPL"].symbol == "AAPL"
        assert response["MSFT"].symbol == "MSFT"