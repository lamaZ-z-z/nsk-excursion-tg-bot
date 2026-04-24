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
    district_id: Optional[int] = None,
    translit_name: Optional[str] = None,
    **kwargs
) -> Optional[District]:
    """Обновление района"""
    if district_id:
        await session.execute(
            update(District)
            .where(District.id == district_id)
            .values(**kwargs)
        )
    elif translit_name:
        await session.execute(
            update(District)
            .where(District.translit_name == translit_name)
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


async def orm_districts_on_start(session: AsyncSession, districts: dict):
    # 1. Получаем все существующие районы из БД одним запросом
    result = await session.execute(select(District))
    existing_districts = {d.name: d for d in result.scalars().all()}

    for name, data in districts.items():
        if name in existing_districts:
            # 2. Если район есть — проверяем изменения
            obj = existing_districts[name]
            if (obj.description != data['description'] or 
                obj.translit_name != data['translit_name']):
                obj.description = data['description']
                obj.translit_name = data['translit_name']
        else:
            # 3. Если района нет — создаем новый
            new_district = District(
                name=name,
                description=data['description'],
                translit_name=data['translit_name']
            )
            session.add(new_district)
            
            # Добавляем баннер только для новых районов
            new_banner = MainBanner(image=default_image, district=new_district)
            session.add(new_banner)

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