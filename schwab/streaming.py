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
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
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
    NEWS_HEADLINE = "NEWS_HEADLINE"
    NEWS_STORY = "NEWS_STORY"
    NEWS_HEADLINE_SEARCH = "NEWS_HEADLINE_SEARCH"
    OPTION = "OPTION"
    QUOTE = "QUOTE"
    TIMESALE_EQUITY = "TIMESALE_EQUITY"
    TIMESALE_OPTIONS = "TIMESALE_OPTIONS"


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
        login_request = {
            "requests": [
                {
                    "service": StreamerService.ADMIN.value,
                    "requestid": str(self._get_request_id()),
                    "command": StreamerCommand.LOGIN.value,
                    "account": self.streamer_info.schwab_client_customer_id,
                    "source": self.streamer_info.schwab_client_correl_id,
                    "parameters": {
                        "token": self.auth.access_token,
                        "version": "1.0",
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
                            "appid": "",
                            "acl": ""
                        })
                    }
                }
            ]
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
            self.streamer = SchwabStreamer(self.auth, self.streamer_info)
            await self.streamer.connect()
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    async def _reconnect_loop(self):
        """Monitor connection and reconnect if needed."""
        while self._running:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                if not self.streamer or not self.streamer.is_connected:
                    logger.info("Connection lost, attempting to reconnect...")
                    await self._connect()
                    
                    # Re-establish subscriptions
                    await self._restore_subscriptions()
                    
            except Exception as e:
                logger.error(f"Error in reconnect loop: {e}")
                await asyncio.sleep(30)  # Wait longer on error
    
    async def _restore_subscriptions(self):
        """Restore subscriptions after reconnection."""
        if not self.streamer:
            return
            
        # Re-subscribe to all previous subscriptions
        for service, sub_info in self.streamer.subscriptions.copy().items():
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
            # Add other services as needed
    
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
    
    async def unsubscribe(self, service: StreamerService, symbols: Optional[List[str]] = None):
        """Unsubscribe from service."""
        if self.streamer:
            await self.streamer.unsubscribe(service, symbols)
    
    async def set_qos(self, level: QOSLevel = QOSLevel.FAST):
        """Set QOS level."""
        if self.streamer:
            await self.streamer.set_qos(level)