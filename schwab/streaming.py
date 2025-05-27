"""
WebSocket streaming client for Schwab Market Data API.

This module provides real-time market data streaming capabilities using WebSocket
connections to Schwab's Streamer API.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any, Union
from enum import Enum
from dataclasses import dataclass
import websockets
from websockets.client import WebSocketClientProtocol

from .auth import SchwabAuth
from .models.user_preference import StreamerInfo

logger = logging.getLogger(__name__)


class StreamerService(str, Enum):
    """Available streamer services."""
    ADMIN = "ADMIN"
    ACTIVES_NASDAQ = "ACTIVES_NASDAQ"
    ACTIVES_NYSE = "ACTIVES_NYSE"
    ACTIVES_OPTIONS = "ACTIVES_OPTIONS"
    CHART_EQUITY = "CHART_EQUITY"
    CHART_FUTURES = "CHART_FUTURES"
    LEVELONE_EQUITIES = "LEVELONE_EQUITIES"
    LEVELONE_OPTIONS = "LEVELONE_OPTIONS"
    LEVELONE_FUTURES = "LEVELONE_FUTURES"
    LEVELONE_FOREX = "LEVELONE_FOREX"
    LEVELONE_FUTURES_OPTIONS = "LEVELONE_FUTURES_OPTIONS"
    LEVELTWO_EQUITIES = "LEVELTWO_EQUITIES"
    LEVELTWO_OPTIONS = "LEVELTWO_OPTIONS"
    LEVELTWO_FUTURES = "LEVELTWO_FUTURES"
    LEVELTWO_FOREX = "LEVELTWO_FOREX"
    NEWS_HEADLINE = "NEWS_HEADLINE"
    NEWS_STORY = "NEWS_STORY"
    NEWS_HEADLINE_SEARCH = "NEWS_HEADLINE_SEARCH"
    OPTION = "OPTION"
    QUOTE = "QUOTE"
    TIMESALE_EQUITY = "TIMESALE_EQUITY"
    TIMESALE_OPTIONS = "TIMESALE_OPTIONS"
    ACCT_ACTIVITY = "ACCT_ACTIVITY"
    CHART_HISTORY_FUTURES = "CHART_HISTORY_FUTURES"


class StreamerCommand(str, Enum):
    """Streamer commands."""
    ADMIN = "ADMIN"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    QOS = "QOS"
    SUBS = "SUBS"
    UNSUBS = "UNSUBS"
    ADD = "ADD"
    VIEW = "VIEW"


class QOSLevel(int, Enum):
    """Quality of Service levels."""
    EXPRESS = 0  # 500ms
    REAL_TIME = 1  # 750ms
    FAST = 2  # 1000ms (default)
    MODERATE = 3  # 1500ms
    SLOW = 4  # 3000ms
    DELAYED = 5  # 5000ms


class LevelOneEquityFields(int, Enum):
    """Level 1 equity data fields."""
    SYMBOL = 0
    BID_PRICE = 1
    ASK_PRICE = 2
    LAST_PRICE = 3
    BID_SIZE = 4
    ASK_SIZE = 5
    ASK_ID = 6
    BID_ID = 7
    TOTAL_VOLUME = 8
    LAST_SIZE = 9
    TRADE_TIME = 10
    QUOTE_TIME = 11
    HIGH_PRICE = 12
    LOW_PRICE = 13
    BID_TICK = 14
    CLOSE_PRICE = 15
    EXCHANGE_ID = 16
    MARGINABLE = 17
    SHORTABLE = 18
    ISLAND_BID = 19
    ISLAND_ASK = 20
    ISLAND_VOLUME = 21
    QUOTE_DAY = 22
    TRADE_DAY = 23
    VOLATILITY = 24
    DESCRIPTION = 25
    LAST_ID = 26
    DIGITS = 27
    OPEN_PRICE = 28
    NET_CHANGE = 29
    HIGH_52_WEEK = 30
    LOW_52_WEEK = 31
    PE_RATIO = 32
    DIVIDEND_AMOUNT = 33
    DIVIDEND_YIELD = 34
    ISLAND_BID_SIZE = 35
    ISLAND_ASK_SIZE = 36
    NAV = 37
    FUND_PRICE = 38
    EXCHANGE_NAME = 39
    DIVIDEND_DATE = 40
    REGULAR_MARKET_QUOTE = 41
    REGULAR_MARKET_TRADE = 42
    REGULAR_MARKET_LAST_PRICE = 43
    REGULAR_MARKET_LAST_SIZE = 44
    REGULAR_MARKET_TRADE_TIME = 45
    REGULAR_MARKET_NET_CHANGE = 46
    SECURITY_STATUS = 47
    MARK = 48
    QUOTE_TIME_IN_LONG = 49
    TRADE_TIME_IN_LONG = 50
    REGULAR_MARKET_TRADE_TIME_IN_LONG = 51


class LevelOneOptionFields(int, Enum):
    """Level 1 option data fields."""
    SYMBOL = 0
    DESCRIPTION = 1
    BID_PRICE = 2
    ASK_PRICE = 3
    LAST_PRICE = 4
    HIGH_PRICE = 5
    LOW_PRICE = 6
    CLOSE_PRICE = 7
    TOTAL_VOLUME = 8
    OPEN_INTEREST = 9
    VOLATILITY = 10
    QUOTE_TIME = 11
    TRADE_TIME = 12
    MONEY_INTRINSIC_VALUE = 13
    QUOTE_DAY = 14
    TRADE_DAY = 15
    EXPIRATION_YEAR = 16
    MULTIPLIER = 17
    DIGITS = 18
    OPEN_PRICE = 19
    BID_SIZE = 20
    ASK_SIZE = 21
    LAST_SIZE = 22
    NET_CHANGE = 23
    STRIKE_PRICE = 24
    CONTRACT_TYPE = 25
    UNDERLYING = 26
    EXPIRATION_MONTH = 27
    DELIVERABLES = 28
    TIME_VALUE = 29
    EXPIRATION_DAY = 30
    DAYS_TO_EXPIRATION = 31
    DELTA = 32
    GAMMA = 33
    THETA = 34
    VEGA = 35
    RHO = 36
    SECURITY_STATUS = 37
    THEORETICAL_OPTION_VALUE = 38
    UNDERLYING_PRICE = 39
    UV_EXPIRATION_TYPE = 40
    MARK = 41


class LevelTwoFields(int, Enum):
    """Level 2 (order book) data fields."""
    SYMBOL = 0
    BOOK_TIME = 1
    BID_PRICE = 2
    BID_SIZE = 3
    ASK_PRICE = 4
    ASK_SIZE = 5
    MARKET_MAKER = 6
    BID_ID = 7
    ASK_ID = 8
    BID_TIME = 9
    ASK_TIME = 10
    QUOTE_TIME = 11


class NewsFields(int, Enum):
    """News data fields."""
    SYMBOL = 0
    ERROR_CODE = 1
    STORY_DATETIME = 2
    HEADLINE_ID = 3
    STATUS = 4
    HEADLINE = 5
    STORY_ID = 6
    COUNT_FOR_KEYWORD = 7
    KEYWORD_ARRAY = 8
    IS_HOT = 9
    STORY_SOURCE = 10


class ChartEquityFields(int, Enum):
    """Chart equity data fields."""
    SYMBOL = 0
    OPEN_PRICE = 1
    HIGH_PRICE = 2
    LOW_PRICE = 3
    CLOSE_PRICE = 4
    VOLUME = 5
    SEQUENCE = 6
    CHART_TIME = 7
    CHART_DAY = 8


class AcctActivityFields(int, Enum):
    """Account activity data fields."""
    ACCOUNT = 0
    MESSAGE_TYPE = 1
    MESSAGE_DATA = 2
    SUBSCRIPTION_KEY = 3


class SchwabStreamer:
    """WebSocket streaming client for Schwab market data."""
    
    def __init__(self, auth: SchwabAuth, streamer_info: StreamerInfo):
        """
        Initialize the streamer client.
        
        Args:
            auth: SchwabAuth instance for authentication
            streamer_info: StreamerInfo from user preferences
        """
        self.auth = auth
        self.streamer_info = streamer_info
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.request_id = 0
        self.is_connected = False
        self.subscriptions: Dict[str, Dict] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        
    async def connect(self):
        """Establish WebSocket connection and authenticate."""
        if self.is_connected:
            logger.warning("Already connected to streamer")
            return
            
        try:
            # Connect to WebSocket
            logger.info(f"Connecting to {self.streamer_info.streamer_socket_url}")
            self.websocket = await websockets.connect(self.streamer_info.streamer_socket_url)
            
            # Send login request
            await self._login()
            
            # Start heartbeat
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # Start receiving messages
            self._receive_task = asyncio.create_task(self._receive_loop())
            
            self.is_connected = True
            logger.info("Successfully connected to Schwab streamer")
            
        except Exception as e:
            logger.error(f"Failed to connect to streamer: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from WebSocket."""
        if not self.is_connected:
            return
            
        self.is_connected = False
        
        # Cancel tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._receive_task:
            self._receive_task.cancel()
            
        # Send logout
        try:
            await self._logout()
        except:
            pass
            
        # Close WebSocket
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            
        logger.info("Disconnected from Schwab streamer")
    
    async def _login(self):
        """Send login request."""
        # Try TD Ameritrade style format (Schwab acquired TDA)
        login_request = {
            "requests": [{
                "service": "ADMIN",
                "command": "LOGIN",
                "requestid": "1",
                "account": self.streamer_info.schwab_client_customer_id,
                "source": self.streamer_info.schwab_client_correl_id,
                "parameters": {
                    "credential": json.dumps({
                        "userid": self.streamer_info.schwab_client_customer_id,
                        "token": self.auth.access_token,
                        "company": self.streamer_info.schwab_client_channel,
                        "segment": self.streamer_info.schwab_client_function_id,
                        "cddomain": self.streamer_info.schwab_client_correl_id,
                        "usergroup": "",
                        "accesslevel": "",
                        "authorized": "Y",
                        "timestamp": int(time.time() * 1000),
                        "appid": self.streamer_info.schwab_client_correl_id,
                        "acl": ""
                    }),
                    "token": self.auth.access_token,
                    "version": "1.0"
                }
            }]
        }
        await self._send_request(login_request)
    
    async def _logout(self):
        """Send logout request."""
        logout_request = {
            "requests": [
                {
                    "service": StreamerService.ADMIN.value,
                    "requestid": str(self._get_request_id()),
                    "command": StreamerCommand.LOGOUT.value,
                    "account": self.streamer_info.schwab_client_customer_id,
                    "source": self.streamer_info.schwab_client_correl_id,
                    "parameters": {}
                }
            ]
        }
        
        await self._send_request(logout_request)
    
    async def subscribe_quote(self, symbols: List[str], fields: Optional[List[int]] = None,
                            callback: Optional[Callable] = None):
        """
        Subscribe to real-time quotes.
        
        Args:
            symbols: List of symbols to subscribe to
            fields: List of field numbers (default: all fields)
            callback: Function to call with quote updates
        """
        if not fields:
            # Default quote fields
            fields = list(range(52))  # Fields 0-51 for quotes
            
        service = StreamerService.QUOTE.value
        
        # Register callback
        if callback:
            self.add_callback(service, callback)
            
        # Build subscription request
        sub_request = self._build_subscription_request(service, symbols, fields)
        
        await self._send_request(sub_request)
        
        # Track subscription
        self.subscriptions[service] = {
            "symbols": symbols,
            "fields": fields
        }
    
    async def subscribe_option(self, symbols: List[str], fields: Optional[List[int]] = None,
                             callback: Optional[Callable] = None):
        """
        Subscribe to real-time option quotes.
        
        Args:
            symbols: List of option symbols to subscribe to
            fields: List of field numbers (default: all fields)
            callback: Function to call with option updates
        """
        if not fields:
            # Default option fields
            fields = list(range(41))  # Fields 0-40 for options
            
        service = StreamerService.OPTION.value
        
        # Register callback
        if callback:
            self.add_callback(service, callback)
            
        # Build subscription request
        sub_request = {
            "requests": [
                {
                    "service": service,
                    "requestid": str(self._get_request_id()),
                    "command": StreamerCommand.SUBS.value,
                    "account": self.streamer_info.schwab_client_customer_id,
                    "source": self.streamer_info.schwab_client_correl_id,
                    "parameters": {
                        "keys": ",".join(symbols),
                        "fields": ",".join(str(f) for f in fields)
                    }
                }
            ]
        }
        
        await self._send_request(sub_request)
        
        # Track subscription
        self.subscriptions[service] = {
            "symbols": symbols,
            "fields": fields
        }
    
    async def subscribe_level_one_equity(self, symbols: List[str], fields: Optional[List[int]] = None,
                                       callback: Optional[Callable] = None):
        """
        Subscribe to Level 1 equity data.
        
        Args:
            symbols: List of symbols to subscribe to
            fields: List of field numbers
            callback: Function to call with updates
        """
        if not fields:
            fields = list(range(30))  # Common Level 1 fields
            
        service = StreamerService.LEVELONE_EQUITIES.value
        
        if callback:
            self.add_callback(service, callback)
            
        sub_request = {
            "requests": [
                {
                    "service": service,
                    "requestid": str(self._get_request_id()),
                    "command": StreamerCommand.SUBS.value,
                    "account": self.streamer_info.schwab_client_customer_id,
                    "source": self.streamer_info.schwab_client_correl_id,
                    "parameters": {
                        "keys": ",".join(symbols),
                        "fields": ",".join(str(f) for f in fields)
                    }
                }
            ]
        }
        
        await self._send_request(sub_request)
        
        self.subscriptions[service] = {
            "symbols": symbols,
            "fields": fields
        }
    
    async def subscribe_level_two_equity(self, symbols: List[str], fields: Optional[List[int]] = None,
                                       callback: Optional[Callable] = None):
        """
        Subscribe to Level 2 (order book) equity data.
        
        Args:
            symbols: List of symbols to subscribe to
            fields: List of field numbers (default: all Level 2 fields)
            callback: Function to call with order book updates
        """
        if not fields:
            # All Level 2 fields
            fields = [f.value for f in LevelTwoFields]
            
        service = StreamerService.LEVELTWO_EQUITIES.value
        
        if callback:
            self.add_callback(service, callback)
            
        sub_request = {
            "requests": [
                {
                    "service": service,
                    "requestid": str(self._get_request_id()),
                    "command": StreamerCommand.SUBS.value,
                    "account": self.streamer_info.schwab_client_customer_id,
                    "source": self.streamer_info.schwab_client_correl_id,
                    "parameters": {
                        "keys": ",".join(symbols),
                        "fields": ",".join(str(f) for f in fields)
                    }
                }
            ]
        }
        
        await self._send_request(sub_request)
        
        self.subscriptions[service] = {
            "symbols": symbols,
            "fields": fields
        }
    
    async def subscribe_level_one_option(self, symbols: List[str], fields: Optional[List[int]] = None,
                                       callback: Optional[Callable] = None):
        """
        Subscribe to Level 1 option data with Greeks.
        
        Args:
            symbols: List of option symbols to subscribe to
            fields: List of field numbers (default: all option fields including Greeks)
            callback: Function to call with option updates including Greeks
        """
        if not fields:
            # All option fields including Greeks
            fields = [f.value for f in LevelOneOptionFields]
            
        service = StreamerService.LEVELONE_OPTIONS.value
        
        if callback:
            self.add_callback(service, callback)
            
        sub_request = {
            "requests": [
                {
                    "service": service,
                    "requestid": str(self._get_request_id()),
                    "command": StreamerCommand.SUBS.value,
                    "account": self.streamer_info.schwab_client_customer_id,
                    "source": self.streamer_info.schwab_client_correl_id,
                    "parameters": {
                        "keys": ",".join(symbols),
                        "fields": ",".join(str(f) for f in fields)
                    }
                }
            ]
        }
        
        await self._send_request(sub_request)
        
        self.subscriptions[service] = {
            "symbols": symbols,
            "fields": fields
        }
    
    async def subscribe_news(self, symbols: List[str], fields: Optional[List[int]] = None,
                           callback: Optional[Callable] = None):
        """
        Subscribe to real-time news headlines.
        
        Args:
            symbols: List of symbols to get news for
            fields: List of field numbers (default: all news fields)
            callback: Function to call with news updates
        """
        if not fields:
            fields = [f.value for f in NewsFields]
            
        service = StreamerService.NEWS_HEADLINE.value
        
        if callback:
            self.add_callback(service, callback)
            
        sub_request = {
            "requests": [
                {
                    "service": service,
                    "requestid": str(self._get_request_id()),
                    "command": StreamerCommand.SUBS.value,
                    "account": self.streamer_info.schwab_client_customer_id,
                    "source": self.streamer_info.schwab_client_correl_id,
                    "parameters": {
                        "keys": ",".join(symbols),
                        "fields": ",".join(str(f) for f in fields)
                    }
                }
            ]
        }
        
        await self._send_request(sub_request)
        
        self.subscriptions[service] = {
            "symbols": symbols,
            "fields": fields
        }
    
    async def subscribe_account_activity(self, callback: Optional[Callable] = None):
        """
        Subscribe to real-time account activity (fills, orders, etc).
        
        Args:
            callback: Function to call with account activity updates
        """
        service = StreamerService.ACCT_ACTIVITY.value
        
        if callback:
            self.add_callback(service, callback)
            
        sub_request = {
            "requests": [
                {
                    "service": service,
                    "requestid": str(self._get_request_id()),
                    "command": StreamerCommand.SUBS.value,
                    "account": self.streamer_info.schwab_client_customer_id,
                    "source": self.streamer_info.schwab_client_correl_id,
                    "parameters": {
                        "keys": self.streamer_info.schwab_client_customer_id,
                        "fields": "0-3"  # All account activity fields
                    }
                }
            ]
        }
        
        await self._send_request(sub_request)
        
        self.subscriptions[service] = {
            "symbols": [self.streamer_info.schwab_client_customer_id],
            "fields": [0, 1, 2, 3]
        }
    
    async def subscribe_chart_equity(self, symbols: List[str], fields: Optional[List[int]] = None,
                                   callback: Optional[Callable] = None):
        """
        Subscribe to real-time chart data (OHLCV).
        
        Args:
            symbols: List of symbols to get chart data for
            fields: List of field numbers (default: all chart fields)
            callback: Function to call with chart updates
        """
        if not fields:
            fields = [f.value for f in ChartEquityFields]
            
        service = StreamerService.CHART_EQUITY.value
        
        if callback:
            self.add_callback(service, callback)
            
        sub_request = {
            "requests": [
                {
                    "service": service,
                    "requestid": str(self._get_request_id()),
                    "command": StreamerCommand.SUBS.value,
                    "account": self.streamer_info.schwab_client_customer_id,
                    "source": self.streamer_info.schwab_client_correl_id,
                    "parameters": {
                        "keys": ",".join(symbols),
                        "fields": ",".join(str(f) for f in fields)
                    }
                }
            ]
        }
        
        await self._send_request(sub_request)
        
        self.subscriptions[service] = {
            "symbols": symbols,
            "fields": fields
        }
    
    async def unsubscribe(self, service: StreamerService, symbols: Optional[List[str]] = None):
        """
        Unsubscribe from a service.
        
        Args:
            service: Service to unsubscribe from
            symbols: Specific symbols to unsubscribe (None = all)
        """
        if service.value not in self.subscriptions:
            return
            
        if symbols is None:
            # Unsubscribe all
            symbols = self.subscriptions[service.value]["symbols"]
            
        unsub_request = {
            "requests": [
                {
                    "service": service.value,
                    "requestid": str(self._get_request_id()),
                    "command": StreamerCommand.UNSUBS.value,
                    "account": self.streamer_info.schwab_client_customer_id,
                    "source": self.streamer_info.schwab_client_correl_id,
                    "parameters": {
                        "keys": ",".join(symbols)
                    }
                }
            ]
        }
        
        await self._send_request(unsub_request)
        
        # Update subscriptions
        remaining = [s for s in self.subscriptions[service.value]["symbols"] if s not in symbols]
        if remaining:
            self.subscriptions[service.value]["symbols"] = remaining
        else:
            del self.subscriptions[service.value]
    
    async def set_qos(self, level: QOSLevel = QOSLevel.FAST):
        """
        Set Quality of Service level.
        
        Args:
            level: QOS level (0=Express, 1=Real-time, 2=Fast, 3=Moderate, 4=Slow, 5=Delayed)
        """
        qos_request = {
            "requests": [
                {
                    "service": StreamerCommand.QOS.value,
                    "requestid": str(self._get_request_id()),
                    "command": StreamerCommand.QOS.value,
                    "account": self.streamer_info.schwab_client_customer_id,
                    "source": self.streamer_info.schwab_client_correl_id,
                    "parameters": {
                        "qoslevel": str(level.value)
                    }
                }
            ]
        }
        
        await self._send_request(qos_request)
    
    def add_callback(self, service: str, callback: Callable):
        """Add a callback for a service."""
        if service not in self.callbacks:
            self.callbacks[service] = []
        self.callbacks[service].append(callback)
    
    def remove_callback(self, service: str, callback: Callable):
        """Remove a callback for a service."""
        if service in self.callbacks:
            self.callbacks[service].remove(callback)
    
    async def _send_request(self, request: Dict):
        """Send a request to the WebSocket."""
        if not self.websocket:
            raise RuntimeError("Not connected to streamer")
            
        message = json.dumps(request)
        logger.debug(f"Sending: {message}")
        await self.websocket.send(message)
    
    async def _receive_loop(self):
        """Continuously receive and process messages."""
        while self.is_connected and self.websocket:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                # Handle different response types
                if "response" in data:
                    await self._handle_response(data["response"])
                elif "data" in data:
                    await self._handle_data(data["data"])
                elif "notify" in data:
                    await self._handle_notify(data["notify"])
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                self.is_connected = False
                break
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode message: {e}")
            except Exception as e:
                logger.error(f"Error in receive loop: {e}")
    
    async def _handle_response(self, responses: List[Dict]):
        """Handle response messages."""
        for response in responses:
            service = response.get("service")
            command = response.get("command")
            content = response.get("content", {})
            
            logger.info(f"Response: {service} {command} - {content.get('msg', 'OK')}")
    
    async def _handle_data(self, data_list: List[Dict]):
        """Handle streaming data messages."""
        for data in data_list:
            service = data.get("service")
            content = data.get("content", [])
            
            # Call registered callbacks
            if service in self.callbacks:
                for callback in self.callbacks[service]:
                    try:
                        callback(service, content)
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
    
    async def _handle_notify(self, notifications: List[Dict]):
        """Handle notification messages."""
        for notification in notifications:
            logger.debug(f"Notification: {notification}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats."""
        while self.is_connected:
            try:
                # Send heartbeat every 30 seconds
                await asyncio.sleep(30)
                
                heartbeat = {
                    "requests": [
                        {
                            "service": StreamerCommand.ADMIN.value,
                            "requestid": str(self._get_request_id()),
                            "command": StreamerCommand.QOS.value,
                            "account": self.streamer_info.schwab_client_customer_id,
                            "source": self.streamer_info.schwab_client_correl_id,
                            "parameters": {}
                        }
                    ]
                }
                
                await self._send_request(heartbeat)
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
    
    def _get_request_id(self) -> int:
        """Get next request ID."""
        self.request_id += 1
        return self.request_id
    
    def _build_subscription_request(self, service: str, symbols: List[str], fields: List[int]) -> Dict:
        """Build a subscription request in the correct format."""
        return {
            "requests": [{
                "service": service,
                "requestid": str(self._get_request_id()),
                "command": "SUBS",
                "account": self.streamer_info.schwab_client_customer_id,
                "source": self.streamer_info.schwab_client_correl_id,
                "parameters": {
                    "keys": ",".join(symbols),
                    "fields": ",".join(str(f) for f in fields)
                }
            }]
        }


class StreamerClient:
    """High-level streaming client with automatic reconnection."""
    
    def __init__(self, auth: SchwabAuth, streamer_info: StreamerInfo):
        """
        Initialize streaming client.
        
        Args:
            auth: SchwabAuth instance
            streamer_info: StreamerInfo from user preferences
        """
        self.auth = auth
        self.streamer_info = streamer_info
        self.streamer: Optional[SchwabStreamer] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._running = False
        self._subscriptions_backup: Dict[str, Dict] = {}
        self._callbacks_backup: Dict[str, List[Callable]] = {}
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10
        self._reconnect_delay = 5  # seconds
        self._max_reconnect_delay = 300  # 5 minutes
        
    async def start(self):
        """Start the streaming client."""
        self._running = True
        await self._connect()
        
        # Start reconnection monitor
        self._reconnect_task = asyncio.create_task(self._reconnect_loop())
    
    async def stop(self):
        """Stop the streaming client."""
        self._running = False
        
        if self._reconnect_task:
            self._reconnect_task.cancel()
            
        if self.streamer:
            await self.streamer.disconnect()
    
    async def _connect(self):
        """Connect to streamer."""
        try:
            # Backup subscriptions and callbacks before creating new streamer
            if self.streamer:
                self._subscriptions_backup = self.streamer.subscriptions.copy()
                self._callbacks_backup = self.streamer.callbacks.copy()
                
            self.streamer = SchwabStreamer(self.auth, self.streamer_info)
            await self.streamer.connect()
            
            # Reset reconnect attempts on successful connection
            self._reconnect_attempts = 0
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    async def _reconnect_loop(self):
        """Monitor connection and reconnect if needed with exponential backoff."""
        while self._running:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                if not self.streamer or not self.streamer.is_connected:
                    if self._reconnect_attempts >= self._max_reconnect_attempts:
                        logger.error(f"Max reconnection attempts ({self._max_reconnect_attempts}) reached. Stopping reconnection.")
                        self._running = False
                        break
                        
                    self._reconnect_attempts += 1
                    
                    # Calculate delay with exponential backoff
                    delay = min(self._reconnect_delay * (2 ** (self._reconnect_attempts - 1)), 
                              self._max_reconnect_delay)
                    
                    logger.info(f"Connection lost, attempting to reconnect (attempt {self._reconnect_attempts}/{self._max_reconnect_attempts}) in {delay} seconds...")
                    
                    await asyncio.sleep(delay)
                    
                    try:
                        await self._connect()
                        
                        # Re-establish subscriptions
                        await self._restore_subscriptions()
                        
                        logger.info("Successfully reconnected to streamer")
                        
                    except Exception as conn_error:
                        logger.error(f"Reconnection attempt {self._reconnect_attempts} failed: {conn_error}")
                    
            except Exception as e:
                logger.error(f"Error in reconnect loop: {e}")
    
    async def _restore_subscriptions(self):
        """Restore subscriptions after reconnection."""
        if not self.streamer:
            return
            
        # Restore callbacks first
        if self._callbacks_backup:
            self.streamer.callbacks = self._callbacks_backup.copy()
            
        # Use backed up subscriptions or current ones
        subscriptions_to_restore = self._subscriptions_backup if self._subscriptions_backup else self.streamer.subscriptions.copy()
            
        # Re-subscribe to all previous subscriptions
        for service, sub_info in subscriptions_to_restore.items():
            try:
                if service == StreamerService.QUOTE.value:
                    await self.streamer.subscribe_quote(
                        sub_info["symbols"],
                        sub_info["fields"]
                    )
                elif service == StreamerService.OPTION.value:
                    await self.streamer.subscribe_option(
                        sub_info["symbols"],
                        sub_info["fields"]
                    )
                elif service == StreamerService.LEVELONE_EQUITIES.value:
                    await self.streamer.subscribe_level_one_equity(
                        sub_info["symbols"],
                        sub_info["fields"]
                    )
                elif service == StreamerService.LEVELTWO_EQUITIES.value:
                    await self.streamer.subscribe_level_two_equity(
                        sub_info["symbols"],
                        sub_info["fields"]
                    )
                elif service == StreamerService.LEVELONE_OPTIONS.value:
                    await self.streamer.subscribe_level_one_option(
                        sub_info["symbols"],
                        sub_info["fields"]
                    )
                elif service == StreamerService.NEWS_HEADLINE.value:
                    await self.streamer.subscribe_news(
                        sub_info["symbols"],
                        sub_info["fields"]
                    )
                elif service == StreamerService.ACCT_ACTIVITY.value:
                    await self.streamer.subscribe_account_activity()
                elif service == StreamerService.CHART_EQUITY.value:
                    await self.streamer.subscribe_chart_equity(
                        sub_info["symbols"],
                        sub_info["fields"]
                    )
                    
                logger.info(f"Restored subscription for service: {service}")
                
            except Exception as e:
                logger.error(f"Failed to restore subscription for {service}: {e}")
    
    # Proxy methods to streamer
    async def subscribe_quote(self, symbols: List[str], fields: Optional[List[int]] = None,
                            callback: Optional[Callable] = None):
        """Subscribe to quotes."""
        if self.streamer:
            await self.streamer.subscribe_quote(symbols, fields, callback)
    
    async def subscribe_option(self, symbols: List[str], fields: Optional[List[int]] = None,
                             callback: Optional[Callable] = None):
        """Subscribe to option quotes."""
        if self.streamer:
            await self.streamer.subscribe_option(symbols, fields, callback)
            
    async def subscribe_level_one_equity(self, symbols: List[str], fields: Optional[List[int]] = None,
                                       callback: Optional[Callable] = None):
        """Subscribe to Level 1 equity data."""
        if self.streamer:
            await self.streamer.subscribe_level_one_equity(symbols, fields, callback)
            
    async def subscribe_level_two_equity(self, symbols: List[str], fields: Optional[List[int]] = None,
                                       callback: Optional[Callable] = None):
        """Subscribe to Level 2 (order book) equity data."""
        if self.streamer:
            await self.streamer.subscribe_level_two_equity(symbols, fields, callback)
            
    async def subscribe_level_one_option(self, symbols: List[str], fields: Optional[List[int]] = None,
                                       callback: Optional[Callable] = None):
        """Subscribe to Level 1 option data with Greeks."""
        if self.streamer:
            await self.streamer.subscribe_level_one_option(symbols, fields, callback)
            
    async def subscribe_news(self, symbols: List[str], fields: Optional[List[int]] = None,
                           callback: Optional[Callable] = None):
        """Subscribe to real-time news headlines."""
        if self.streamer:
            await self.streamer.subscribe_news(symbols, fields, callback)
            
    async def subscribe_account_activity(self, callback: Optional[Callable] = None):
        """Subscribe to real-time account activity."""
        if self.streamer:
            await self.streamer.subscribe_account_activity(callback)
            
    async def subscribe_chart_equity(self, symbols: List[str], fields: Optional[List[int]] = None,
                                   callback: Optional[Callable] = None):
        """Subscribe to real-time chart data."""
        if self.streamer:
            await self.streamer.subscribe_chart_equity(symbols, fields, callback)
    
    async def unsubscribe(self, service: StreamerService, symbols: Optional[List[str]] = None):
        """Unsubscribe from service."""
        if self.streamer:
            await self.streamer.unsubscribe(service, symbols)
    
    async def set_qos(self, level: QOSLevel = QOSLevel.FAST):
        """Set QOS level."""
        if self.streamer:
            await self.streamer.set_qos(level)
            
    def add_callback(self, service: str, callback: Callable):
        """Add a callback for a service."""
        if self.streamer:
            self.streamer.add_callback(service, callback)
            
    def remove_callback(self, service: str, callback: Callable):
        """Remove a callback for a service."""
        if self.streamer:
            self.streamer.remove_callback(service, callback)


@dataclass
class StreamingQuote:
    """Parsed streaming quote data."""
    symbol: str
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    last_price: Optional[float] = None
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    total_volume: Optional[int] = None
    last_size: Optional[int] = None
    trade_time: Optional[int] = None
    quote_time: Optional[int] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    close_price: Optional[float] = None
    net_change: Optional[float] = None
    
    @classmethod
    def from_data(cls, data: Dict[str, Any]) -> "StreamingQuote":
        """Create from streaming data."""
        return cls(
            symbol=data.get("key", ""),
            bid_price=data.get(str(LevelOneEquityFields.BID_PRICE.value)),
            ask_price=data.get(str(LevelOneEquityFields.ASK_PRICE.value)),
            last_price=data.get(str(LevelOneEquityFields.LAST_PRICE.value)),
            bid_size=data.get(str(LevelOneEquityFields.BID_SIZE.value)),
            ask_size=data.get(str(LevelOneEquityFields.ASK_SIZE.value)),
            total_volume=data.get(str(LevelOneEquityFields.TOTAL_VOLUME.value)),
            last_size=data.get(str(LevelOneEquityFields.LAST_SIZE.value)),
            trade_time=data.get(str(LevelOneEquityFields.TRADE_TIME.value)),
            quote_time=data.get(str(LevelOneEquityFields.QUOTE_TIME.value)),
            high_price=data.get(str(LevelOneEquityFields.HIGH_PRICE.value)),
            low_price=data.get(str(LevelOneEquityFields.LOW_PRICE.value)),
            close_price=data.get(str(LevelOneEquityFields.CLOSE_PRICE.value)),
            net_change=data.get(str(LevelOneEquityFields.NET_CHANGE.value))
        )


@dataclass
class StreamingOptionQuote:
    """Parsed streaming option quote data with Greeks."""
    symbol: str
    description: Optional[str] = None
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    last_price: Optional[float] = None
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    total_volume: Optional[int] = None
    open_interest: Optional[int] = None
    strike_price: Optional[float] = None
    underlying_price: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None
    implied_volatility: Optional[float] = None
    time_value: Optional[float] = None
    intrinsic_value: Optional[float] = None
    
    @classmethod
    def from_data(cls, data: Dict[str, Any]) -> "StreamingOptionQuote":
        """Create from streaming data."""
        return cls(
            symbol=data.get("key", ""),
            description=data.get(str(LevelOneOptionFields.DESCRIPTION.value)),
            bid_price=data.get(str(LevelOneOptionFields.BID_PRICE.value)),
            ask_price=data.get(str(LevelOneOptionFields.ASK_PRICE.value)),
            last_price=data.get(str(LevelOneOptionFields.LAST_PRICE.value)),
            bid_size=data.get(str(LevelOneOptionFields.BID_SIZE.value)),
            ask_size=data.get(str(LevelOneOptionFields.ASK_SIZE.value)),
            total_volume=data.get(str(LevelOneOptionFields.TOTAL_VOLUME.value)),
            open_interest=data.get(str(LevelOneOptionFields.OPEN_INTEREST.value)),
            strike_price=data.get(str(LevelOneOptionFields.STRIKE_PRICE.value)),
            underlying_price=data.get(str(LevelOneOptionFields.UNDERLYING_PRICE.value)),
            delta=data.get(str(LevelOneOptionFields.DELTA.value)),
            gamma=data.get(str(LevelOneOptionFields.GAMMA.value)),
            theta=data.get(str(LevelOneOptionFields.THETA.value)),
            vega=data.get(str(LevelOneOptionFields.VEGA.value)),
            rho=data.get(str(LevelOneOptionFields.RHO.value)),
            implied_volatility=data.get(str(LevelOneOptionFields.VOLATILITY.value)),
            time_value=data.get(str(LevelOneOptionFields.TIME_VALUE.value)),
            intrinsic_value=data.get(str(LevelOneOptionFields.MONEY_INTRINSIC_VALUE.value))
        )


@dataclass
class OrderBookEntry:
    """Single order book entry."""
    price: float
    size: int
    market_maker: Optional[str] = None
    time: Optional[int] = None
    

@dataclass
class StreamingOrderBook:
    """Level 2 order book data."""
    symbol: str
    bids: List[OrderBookEntry]
    asks: List[OrderBookEntry]
    book_time: Optional[int] = None
    
    @classmethod
    def from_data(cls, data: List[Dict[str, Any]]) -> Dict[str, "StreamingOrderBook"]:
        """Create order books from streaming data."""
        books = {}
        
        for item in data:
            symbol = item.get("key", "")
            if symbol not in books:
                books[symbol] = cls(symbol=symbol, bids=[], asks=[])
                
            book = books[symbol]
            book.book_time = item.get(str(LevelTwoFields.BOOK_TIME.value))
            
            # Parse bid
            bid_price = item.get(str(LevelTwoFields.BID_PRICE.value))
            bid_size = item.get(str(LevelTwoFields.BID_SIZE.value))
            if bid_price is not None and bid_size is not None:
                book.bids.append(OrderBookEntry(
                    price=bid_price,
                    size=bid_size,
                    market_maker=item.get(str(LevelTwoFields.MARKET_MAKER.value)),
                    time=item.get(str(LevelTwoFields.BID_TIME.value))
                ))
                
            # Parse ask
            ask_price = item.get(str(LevelTwoFields.ASK_PRICE.value))
            ask_size = item.get(str(LevelTwoFields.ASK_SIZE.value))
            if ask_price is not None and ask_size is not None:
                book.asks.append(OrderBookEntry(
                    price=ask_price,
                    size=ask_size,
                    market_maker=item.get(str(LevelTwoFields.MARKET_MAKER.value)),
                    time=item.get(str(LevelTwoFields.ASK_TIME.value))
                ))
                
        # Sort order books
        for book in books.values():
            book.bids.sort(key=lambda x: x.price, reverse=True)  # Highest bid first
            book.asks.sort(key=lambda x: x.price)  # Lowest ask first
            
        return books


@dataclass
class StreamingNews:
    """Streaming news data."""
    symbol: str
    headline: str
    story_id: str
    headline_id: str
    story_datetime: int
    is_hot: bool
    story_source: Optional[str] = None
    
    @classmethod
    def from_data(cls, data: Dict[str, Any]) -> "StreamingNews":
        """Create from streaming data."""
        return cls(
            symbol=data.get("key", ""),
            headline=data.get(str(NewsFields.HEADLINE.value), ""),
            story_id=data.get(str(NewsFields.STORY_ID.value), ""),
            headline_id=data.get(str(NewsFields.HEADLINE_ID.value), ""),
            story_datetime=data.get(str(NewsFields.STORY_DATETIME.value), 0),
            is_hot=bool(data.get(str(NewsFields.IS_HOT.value), False)),
            story_source=data.get(str(NewsFields.STORY_SOURCE.value))
        )


@dataclass
class StreamingChartBar:
    """Streaming chart bar data."""
    symbol: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    sequence: int
    chart_time: int
    
    @classmethod
    def from_data(cls, data: Dict[str, Any]) -> "StreamingChartBar":
        """Create from streaming data."""
        return cls(
            symbol=data.get("key", ""),
            open_price=data.get(str(ChartEquityFields.OPEN_PRICE.value), 0.0),
            high_price=data.get(str(ChartEquityFields.HIGH_PRICE.value), 0.0),
            low_price=data.get(str(ChartEquityFields.LOW_PRICE.value), 0.0),
            close_price=data.get(str(ChartEquityFields.CLOSE_PRICE.value), 0.0),
            volume=data.get(str(ChartEquityFields.VOLUME.value), 0),
            sequence=data.get(str(ChartEquityFields.SEQUENCE.value), 0),
            chart_time=data.get(str(ChartEquityFields.CHART_TIME.value), 0)
        )


@dataclass
class StreamingAccountActivity:
    """Streaming account activity data."""
    account: str
    message_type: str
    message_data: Dict[str, Any]
    
    @classmethod
    def from_data(cls, data: Dict[str, Any]) -> "StreamingAccountActivity":
        """Create from streaming data."""
        message_data_str = data.get(str(AcctActivityFields.MESSAGE_DATA.value), "{}")
        try:
            message_data = json.loads(message_data_str) if isinstance(message_data_str, str) else message_data_str
        except:
            message_data = {"raw": message_data_str}
            
        return cls(
            account=data.get(str(AcctActivityFields.ACCOUNT.value), ""),
            message_type=data.get(str(AcctActivityFields.MESSAGE_TYPE.value), ""),
            message_data=message_data
        )