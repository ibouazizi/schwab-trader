from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

class ExecutionReport(BaseModel):
    """Model representing an order execution report."""
    
    order_id: int = Field(..., description="The ID of the order that was executed")
    execution_id: str = Field(..., description="Unique identifier for this execution")
    timestamp: datetime = Field(..., description="When the execution occurred")
    quantity: int = Field(..., description="Number of shares executed")
    price: Decimal = Field(..., description="Execution price")
    commission: Decimal = Field(..., description="Commission charged for this execution")
    exchange: str = Field(..., description="Exchange where the execution occurred")
    
    @property
    def value(self) -> Decimal:
        """Calculate the total value of the execution."""
        return self.quantity * self.price
    
    @property
    def total_cost(self) -> Decimal:
        """Calculate the total cost including commission."""
        return self.value + self.commission

class ExecutionReportList(BaseModel):
    """Model representing a list of execution reports."""
    
    executions: list[ExecutionReport] = Field(default_factory=list)
    next_page_token: Optional[str] = Field(None, description="Token for retrieving the next page of results")
    
    def __iter__(self):
        return iter(self.executions)
    
    def __len__(self):
        return len(self.executions)
    
    def __getitem__(self, idx):
        return self.executions[idx]