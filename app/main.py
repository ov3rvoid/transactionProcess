from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from app.models.payout import Base  # Импортируем Base из моделей
from app.db.database import engine  # Подключение к базе данных
from app.api.routes import router

tags_metadata = [
    {
        "name": "Payouts",
        "description": "Создание заявок на выплаты, обновление статуса и получение информации по заявке.",
    },
]

app = FastAPI(
    title="CNYXPay Payout API",
    description="Микросервис для создания и управления заявками на выплаты партнёров.",
    version="1.0.0",
    openapi_tags=tags_metadata,
)

# Асинхронная сессия
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def create_tables():
    # Создание всех таблиц, если они еще не существуют
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Запускаем создание таблиц при старте приложения
@app.on_event("startup")
async def startup():
    await create_tables()

# Регистрация маршрутов
app.include_router(router, prefix="/api/v1")
