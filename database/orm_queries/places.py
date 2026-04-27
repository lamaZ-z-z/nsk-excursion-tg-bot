'''Module providing orm fucntions to get info about districts'''
from typing import Optional, List, Dict, Any
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.districts import districts
from database import orm_queries #type:ignore
from database.models import Place, PlaceSuggestion


async def add_place(
    session: AsyncSession,
    district: str,
    description: Optional[str] = None,
    image: Optional[str] = None,
    two_gis_url: Optional[str] = None
) -> Place:
    """Добавление нового места"""
    place = Place(
        district=district,
        description=description,
        image=image,
        TwoGisURL=two_gis_url
    )
    session.add(place)
    await session.commit()
    await session.refresh(place)
    return place

async def get_place(
    session: AsyncSession,
    place_id: int
) -> Optional[Place]:
    """Получение места по ID"""
    result = await session.execute(
        select(Place).where(Place.id == place_id)
    )
    return result.scalar_one_or_none()

async def get_places_by_district(
    session: AsyncSession,
    *,
    district_name: Optional[str] = None,
    translit_name: Optional[str] = None,
) -> Optional[List[Place]]:
    """Получение всех мест в районе"""
    if district_name:
        result = await session.execute(
            select(Place)
            .where(Place.district_name == district_name)
            .order_by(Place.id)
        )
    elif translit_name:
        result = await session.execute(
            select(Place)
            .where(Place.district_translit_name == translit_name)
            .order_by(Place.id)
        )
    else:
        result = None
    return result.scalars().all()

async def get_all_places(
    session: AsyncSession
) -> List[Place]:
    """Получение всех мест"""
    result = await session.execute(
        select(Place).order_by(Place.id)
    )
    return result.scalars().all()

async def update_place(
    session: AsyncSession,
    place_id: int,
    **kwargs
) -> Optional[Place]:
    """Обновление места"""
    await session.execute(
        update(Place)
        .where(Place.id == place_id)
        .values(**kwargs)
    )
    await session.commit()
    return await get_place(session, place_id)

async def delete_place(
    session: AsyncSession,
    place_id: int
) -> bool:
    """Удаление места"""
    result = await session.execute(
        delete(Place).where(Place.id == place_id)
    )
    await session.commit()
    return result.rowcount > 0



async def get_places_with_district_info(
    session: AsyncSession,
    district_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Получение мест с информацией о районе"""
    query = select(Place)
    if district_name:
        query = query.where(Place.district_name == district_name)
    
    result = await session.execute(query)
    places = result.scalars().all()
    
    places_with_district = []
    for place in places:
        district = await orm_queries.get_district(session, name=place.district)
        places_with_district.append({
            'place': place,
            'district_info': district
        })
    return places_with_district


async def add_place_from_suggestion(
    session: AsyncSession,
    suggested_place: PlaceSuggestion
):
    '''Функция для добавления места используя предложенное место
    из предложки'''
    place = Place(
        district_name = suggested_place.district_name,
        district_translit_name = districts[suggested_place.district_name]['translit_name'],
        name = suggested_place.place_name,
        description = suggested_place.description,
        image = suggested_place.photo_url,
        TwoGisURL = suggested_place.location_url
    )
    session.add(place)
    await session.commit()
    await session.refresh(place)
    return place
