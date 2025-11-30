from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime

class Dest(BaseModel):
    account: str
    fullname: Optional[str] = None

class PayoutIn(BaseModel):
    id: str
    amount: Decimal = Field(..., ge=Decimal("0.01"))
    currency: str
    method: str
    destination: Dest
    meta: Optional[Dict[str, Any]] = None
    timeout: int = Field(60, ge=1, le=60*24*30)
    callback_url: Optional[str] = None

class PayoutStatusUpdate(BaseModel):
    id: str 
    approved: bool     
    ttl_minutes: int  