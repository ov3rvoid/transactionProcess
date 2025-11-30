# app/api/routes.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta, timezone

from app.schemas.payout import (
    PayoutIn,
    PayoutStatusUpdate,
    PayoutCreateResponse,
    PayoutStatusResponse,
    PayoutInfoResponse,
    ErrorResponse,
)
from app.models.payout import Payout
from app.db.database import get_session

router = APIRouter(tags=["Payouts"])


@router.post(
    "/payouts",
    response_model=PayoutCreateResponse,
    summary="Создать заявку на выплату",
    description=(
        "Партнёр отправляет заявку с уникальным `id`, суммой в USDT и реквизитами получателя. "
        "Сервис рассчитывает курс и сумму в фиате, создаёт запись в базе и возвращает расчётный курс и сумму. "
        "Если заявка с таким `id` уже существует, возвращается ошибка 409 для поддержки идемпотентности."
    ),
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Неверный метод выплаты или валюта",
        },
        409: {
            "model": ErrorResponse,
            "description": "Заявка с таким ID уже существует",
        },
    },
)
async def create_payout(
    payout: PayoutIn,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Payout).where(Payout.id == payout.id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "PAYOUT_ALREADY_EXISTS",
                "message": "Payout with this id already exists",
                "details": {"id": payout.id},
            },
        )

    if payout.method not in ["bank", "crypto", "paypal"]:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_METHOD",
                "message": "Invalid payout method",
                "details": {"allowed": ["bank", "crypto", "paypal"]},
            },
        )
    
    if payout.currency not in ["USD", "EUR", "CNY", "USDT"]:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_CURRENCY",
                "message": "Invalid currency",
                "details": {"allowed": ["USD", "EUR", "CNY", "USDT"]},
            },
        )
    
    xrate = 7
    amount_fiat = xrate * payout.amount

    new_payout = Payout(
        id=payout.id, 
        amount=payout.amount,
        currency=payout.currency,
        method=payout.method,
        destination=payout.destination.model_dump(),
        meta=payout.meta or {},
        status="processing",
        expires_at=datetime.now(timezone.utc).replace(microsecond=0)
                    + timedelta(minutes=5),
        callback_url=payout.callback_url,
        amount_fiat=amount_fiat,
        xrate=xrate,
    )

    session.add(new_payout)
    await session.commit()
    await session.refresh(new_payout)

    return PayoutCreateResponse(
        xrate=new_payout.xrate,
        amount_fiat=new_payout.amount_fiat,
    )


@router.post(
    "/update-payout-status",
    response_model=PayoutStatusResponse,
    summary="Обновить статус заявки",
    description=(
        "Внутренний сервис или оператор обновляет статус заявки: флаг `approved` и новое время истечения `expires_at`. "
        "Если заявка с указанным `id` не найдена, возвращается 404."
    ),
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Заявка с таким ID не найдена",
        },
    },
)
async def update_payout_status(
    payout_status: PayoutStatusUpdate,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Payout).filter(Payout.id == payout_status.id)
    )
    payout = result.scalar_one_or_none()

    if not payout:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PAYOUT_NOT_FOUND",
                "message": "Payout not found",
                "details": {"id": payout_status.id},
            },
        )

    payout.approved = payout_status.approved
    payout.expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=payout_status.ttl_minutes
    )
    payout.updated_at = datetime.now(timezone.utc)

    session.add(payout)
    await session.commit()
    await session.refresh(payout)

    return PayoutStatusResponse(
        id=payout.id,
        approved=payout.approved,
        expires_at=payout.expires_at,
    )


@router.get(
    "/payout-info/{id}",
    response_model=PayoutInfoResponse,
    summary="Получить информацию о заявке",
    description=(
        "Возвращает полную информацию о заявке по её `id`: сумму в фиате, метод, валюту, реквизиты, ссылки на чеки, "
        "курс, статусы и временные метки. Если заявка не найдена, возвращает 404."
    ),
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Заявка с таким ID не найдена",
        },
    },
)
async def get_payout_info(
    id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Payout).filter(Payout.id == id)
    )
    payout = result.scalar_one_or_none()

    if not payout:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PAYOUT_NOT_FOUND",
                "message": "Payout not found",
                "details": {"id": id},
            },
        )

    return PayoutInfoResponse(
        id=payout.id,
        amount_fiat=payout.amount_fiat,
        method=payout.method,
        currency=payout.currency,
        destination=payout.destination,
        receipt=payout.receipt,
        extra_receipt=payout.extra_receipt,
        xrate=payout.xrate,
        status=payout.status,
        created_at=payout.created_at,
        paid_at=payout.paid_at,
        updated_at=payout.updated_at,
    )
