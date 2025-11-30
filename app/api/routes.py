from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.payout import PayoutIn, PayoutStatusUpdate
from app.models.payout import Payout
from app.db.database import get_session
from datetime import datetime, timedelta, timezone

router = APIRouter()

@router.post("/payouts")
async def create_payout(payout: PayoutIn, session: AsyncSession = Depends(get_session)):
    # Проверка валидности метода и валюты
    result = await session.execute(
        select(Payout).where(Payout.id == payout.id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=409, detail="Id is already exists")

    if payout.method not in ["bank", "crypto", "paypal"]:
        raise HTTPException(status_code=400, detail="Invalid method")
    
    if payout.currency not in ["USD", "EUR", "CNY", "USDT"]:
        raise HTTPException(status_code=400, detail="Invalid currency")
    
    xrate = 7
    amount_fiat = xrate * payout.amount

    # Создание записи в таблице Payout
    new_payout = Payout(
        id=payout.id, 
        amount=payout.amount,
        currency=payout.currency,
        method=payout.method,
        destination=payout.destination.model_dump(),  # Преобразуем destination в dict
        meta=payout.meta or {},
        status="processing",
        expires_at=datetime.now(timezone.utc).replace(microsecond=0) + timedelta(minutes=payout.timeout),
        callback_url=payout.callback_url,
        amount_fiat=amount_fiat,
        xrate=xrate
    )

    session.add(new_payout)
    await session.commit()
    await session.refresh(new_payout)

    return {
        "xrate": xrate,
        "amount_fiat": new_payout.amount_fiat
    }


@router.post("/update-payout-status")
async def update_payout_status(payout_status: PayoutStatusUpdate, session: AsyncSession = Depends(get_session)):
    # Проверка существования операции по id
    result = await session.execute(
        select(Payout).filter(Payout.id == payout_status.id)
    )

    payout = result.scalar_one_or_none()

    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")

    # Обновляем статус и время выполнения операции
    payout.approved = payout_status.approved
    payout.expires_at = datetime.now(timezone.utc) + timedelta(minutes=payout_status.ttl_minutes)

    # Сохраняем изменения в базе данных
    session.add(payout)
    await session.commit()
    await session.refresh(payout)

    return {
        "id": payout.id,
        "approved": payout.approved,
        "expires_at": payout.expires_at,
    }

# id, amount_fiat, method, currency, destination, reciept, extra_reciept, xrate, status, created_at, paid_at, updated_at
@router.get("/payout-info/{id}")
async def get_payout_info(id: str, session: AsyncSession = Depends(get_session)):
    # Запрос в базу данных для получения данных о выплате
    result = await session.execute(
        select(Payout).filter(Payout.id == id)
    )
    payout = result.scalar_one_or_none()

    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")

    return {
        "id": payout.id,
        "amount_fiat": payout.amount_fiat,  # Пример конверсии (по фиксированному курсу)
        "method": payout.method,
        "currency": payout.currency,
        "destination": payout.destination,
        "receipt": payout.receipt or "",  # Если receipt нет, возвращаем пустое значение
        "extra_receipt": payout.extra_receipt or "",  # То же для extra_receipt
        "xrate": payout.xrate,  # Примерный курс, можно заменить на реальный
        "status": payout.status,
        "created_at": payout.created_at,
        "paid_at": payout.paid_at or None,  # Если paid_at нет, возвращаем None
        "updated_at": payout.updated_at or None,  # Если updated_at нет, возвращаем None
    }