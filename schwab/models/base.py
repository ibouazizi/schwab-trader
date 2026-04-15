from typing import List, Optional, Any
from pydantic import BaseModel, Field

class SchwabBaseModel(BaseModel):
    """Base model for all Schwab API models."""
    class Config:
        populate_by_name = True  # Allow population by field name or alias

class ErrorResponse(SchwabBaseModel):
    """Error response model."""
    message: str
    errors: List[str]

class AccountNumber(SchwabBaseModel):
    """Account number and its encrypted hash value."""
    account_number: str = Field(..., alias="accountNumber", description="The plain text account number")
    hash_value: str = Field(..., alias="hashValue", description="The encrypted hash value of the account number")

class AccountNumbers(SchwabBaseModel):
    """List of account numbers."""
    accounts: List[Any]  # Will accept AccountNumber or AccountNumberHash
