from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime

class Dest(BaseModel):
    account: str = Field(..., example="4111 1111 1111 1111")
    fullname: Optional[str] = Field(None, example="Zhang Wei")

class PayoutIn(BaseModel):
    id: str = Field(..., example="payout_2025_0001")
    amount: Decimal = Field(..., ge=Decimal("0.01"), example="100.50")
    currency: str = Field(..., example="USDT")
    method: str = Field(..., example="bank")
    destination: Dest
    meta: Optional[Dict[str, Any]] = Field(default=None, example={"order_id": "12345"})
    callback_url: Optional[str] = Field(
        default=None,
        example="https://partner.com/payout-callback",
        description="Опциональный URL для обратного запроса. Если не указан — callback не используется."
    )

class PayoutStatusUpdate(BaseModel):
    id: str = Field(..., example="payout_2025_0001")
    approved: bool = Field(..., example=True)
    ttl_minutes: int = Field(..., example=30)

class PayoutCreateResponse(BaseModel):
    xrate: Decimal = Field(..., example="7.10")
    amount_fiat: Decimal = Field(..., example="710.55")

class PayoutStatusResponse(BaseModel):
    id: str
    approved: bool
    expires_at: datetime

class PayoutInfoResponse(BaseModel):
    id: str
    amount_fiat: Decimal
    method: str
    currency: str
    destination: Dict[str, Any]
    receipt: str | None
    extra_receipt: str | None
    xrate: Decimal
    status: str
    created_at: datetime
    paid_at: datetime | None
    updated_at: datetime | None

class ErrorResponse(BaseModel):
    code: str = Field(..., example="PAYOUT_ALREADY_EXISTS")
    message: str = Field(..., example="Payout with this id already exists")
    details: Dict[str, Any] | None = Field(default=None)
