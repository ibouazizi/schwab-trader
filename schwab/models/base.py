from typing import List, Optional
from pydantic import BaseModel, Field

class SchwabBaseModel(BaseModel):
    """Base model for all Schwab API models."""
    pass

class ErrorResponse(SchwabBaseModel):
    """Error response model."""
    message: str
    errors: List[str]

class AccountNumber(SchwabBaseModel):
    """Account number and its encrypted hash value."""
    account_number: str = Field(..., description="The plain text account number")
    hash_value: str = Field(..., description="The encrypted hash value of the account number")

class AccountNumbers(SchwabBaseModel):
    """List of account numbers."""
    accounts: List[AccountNumber]
