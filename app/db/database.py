from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True, pool_pre_ping=True)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

from sqlalchemy.exc import SQLAlchemyError

async def get_session():
    try:
        async with async_session() as session:
            yield session
    except SQLAlchemyError as e:
        print(f"Error while creating session: {e}")
        raise

