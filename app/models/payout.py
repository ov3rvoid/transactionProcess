from sqlalchemy import Column, String, Numeric, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from decimal import Decimal

Base = declarative_base()

class Payout(Base):
    __tablename__ = "payouts"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    destination: Mapped[dict] = mapped_column(JSON, nullable=False)
    meta: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="processing")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    callback_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    amount_fiat: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    xrate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    receipt = Column(String(1024), nullable=True, default=None)  # Поле receipt
    extra_receipt = Column(String(1024), nullable=True, default=None)  # Поле extra_receipt
    paid_at = Column(DateTime(timezone=True), nullable=True, default=None)  # Поле paid_at
    updated_at = Column(DateTime(timezone=True), nullable=True, default=None)  # Поле updated_at