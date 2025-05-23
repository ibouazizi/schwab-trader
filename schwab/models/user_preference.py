"""User preference models for Schwab API."""
from typing import List, Optional
from pydantic import BaseModel, Field
from .base import SchwabBaseModel

class UserPreferenceAccount(SchwabBaseModel):
    """User preference account model."""
    account_number: str = Field(..., alias="accountNumber")
    primary_account: bool = Field(False, alias="primaryAccount")
    type: Optional[str] = None
    nick_name: Optional[str] = Field(None, alias="nickName")
    account_color: Optional[str] = Field(None, alias="accountColor")
    display_acct_id: Optional[str] = Field(None, alias="displayAcctId")
    auto_position_effect: bool = Field(False, alias="autoPositionEffect")

class StreamerInfo(SchwabBaseModel):
    """Streamer information model."""
    streamer_socket_url: Optional[str] = Field(None, alias="streamerSocketUrl")
    schwab_client_customer_id: Optional[str] = Field(None, alias="schwabClientCustomerId")
    schwab_client_correl_id: Optional[str] = Field(None, alias="schwabClientCorrelId")
    schwab_client_channel: Optional[str] = Field(None, alias="schwabClientChannel")
    schwab_client_function_id: Optional[str] = Field(None, alias="schwabClientFunctionId")

class Offer(SchwabBaseModel):
    """Offer model."""
    level2_permissions: bool = Field(False, alias="level2Permissions")
    mkt_data_permission: Optional[str] = Field(None, alias="mktDataPermission")

class UserPreference(SchwabBaseModel):
    """User preference model."""
    accounts: Optional[List[UserPreferenceAccount]] = None
    streamer_info: Optional[List[StreamerInfo]] = Field(None, alias="streamerInfo")
    offers: Optional[List[Offer]] = None