from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from app.models.payout import Base  # Импортируем Base из моделей
from app.db.database import engine  # Подключение к базе данных

app = FastAPI()

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
from app.api.routes import router
app.include_router(router)
