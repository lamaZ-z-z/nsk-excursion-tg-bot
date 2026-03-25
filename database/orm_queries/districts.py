'''Module providing orm fucntions to get info about districts'''
from typing import Optional, List

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from common.default_image import default_image
from common.default_descriptions import get_district_description
from database.models import District, MainBanner
from database import orm_queries

async def add_district(
    session: AsyncSession,
    name: str,
    translit_name: str,
    image: Optional[str] = None,
    description: Optional[str] = None
) -> District:
    """Добавление нового района"""
    district = District(
        name=name,
        translit_name=translit_name,
        image=image,
        description=description
    )
    session.add(district)
    await session.commit()
    await session.refresh(district)
    return district


async def get_district(
    session: AsyncSession,
    district_id: Optional[int] = None,
    name: Optional[str] = None,
    translit_name: Optional[str] = None
) -> Optional[District]:
    """Получение района по ID, имени или транслиту"""
    query = select(District)
    
    if district_id:
        query = query.where(District.id == district_id)
    elif name:
        query = query.where(District.name == name)
    elif translit_name:
        query = query.where(District.translit_name == translit_name)
    else:
        return None
    
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_all_districts(
    session: AsyncSession
) -> List[District]:
    """Получение всех районов"""
    result = await session.execute(
        select(District).order_by(District.name)
    )
    return result.scalars().all()


async def update_district(
    session: AsyncSession,
    district_id: int,
    **kwargs
) -> Optional[District]:
    """Обновление района"""
    await session.execute(
        update(District)
        .where(District.id == district_id)
        .values(**kwargs)
    )
    await session.commit()
    return await get_district(session, district_id=district_id)


async def delete_district(
    session: AsyncSession,
    district_id: int
) -> bool:
    """Удаление района"""
    result = await session.execute(
        delete(District).where(District.id == district_id)
    )
    await session.commit()
    return result.rowcount > 0


async def orm_districts_on_start(session: AsyncSession, districs: dict):
    '''function for adding basic 4 districts of Novosibirsk in db'''
    for k, v in districs.items():
        obj = District(
            name=k,
            translit_name=v,
            description=get_district_description(k)
        )
        session.add(obj)
    obj = MainBanner(image=default_image)
    session.add(obj)
    await session.commit()


async def get_district_id(session: AsyncSession, district_name: str) -> Optional[District]:
    '''Функция для получения id района '''
    result = await session.execute(
        select(District).where(District.name == district_name)
    )
    return result.scalar_one_or_none()
    

async def get_or_create_district(
    session: AsyncSession,
    name: str,
    translit_name: str,
    **kwargs
) -> District:
    """Получить существующий район или создать новый"""
    district = await orm_queries.get_district(session, name=name)
    if not district:
        district = await orm_queries.add_district(
            session,
            name=name,
            translit_name=translit_name,
            **kwargs
        )
    return district