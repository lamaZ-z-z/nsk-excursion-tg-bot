'''Module with engine of data base'''
import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base
from database.orm_queries import orm_districts_on_start
from common.districts import districts


engine = create_async_engine(os.getenv("DB_LITE"), echo=True)
session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_db():
    '''function that creates data base session'''
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def after_creation():
    '''function that adds districts from the start of 
    data base session'''
    async with session_maker() as session:
        await orm_districts_on_start(session, districts)

async def drop_db():
    '''function that deletes all data in data base'''
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
