'''module with function that controls all levels of bot
0 - main banner (level with districts)
1 - level with places
2 - level with info about place
'''
from typing import Optional
from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from kbds.inline import get_user_main_btns, get_places_level_btns, get_place_kbds
from database import orm_queries



async def districts_level(session: AsyncSession, level: int):
    main_banner = await orm_queries.get_main_banner(session)
    kbds = await get_user_main_btns(level=level, session=session)
    image = InputMediaPhoto(media=main_banner.image, caption=main_banner.description)
    return image, kbds


async def places_level(session: AsyncSession, level: int, translit_district: str, page_num: int):
    district = await orm_queries.get_district(session=session, translit_name=translit_district)
    kbds = await get_places_level_btns(level=level, session=session,
                                 translit_district=translit_district, page_num=page_num)
    image = InputMediaPhoto(media=district.image, caption=district.description)
    return image, kbds

async def place_level(session: AsyncSession, level: int, place_id: int):
    place = await orm_queries.get_place(session=session, place_id=place_id)
    kbds = await get_place_kbds(session=session, level=level, place_id=place_id)
    image = InputMediaPhoto(media=place.image, caption=f"{place.name}\n--------------\n{place.description}")
    return image, kbds


async def get_levels_content(
    session: AsyncSession,
    level: int,
    translit_district: Optional[str] = None,
    place_id: Optional[str] = None,
    page_num: int = 1
):
    if level == 0:
        return await districts_level(session=session, level=level)
    elif level == 1 and translit_district:
        return await places_level(session=session, level=level,
                             translit_district=translit_district, page_num=page_num)
    elif level == 2:
        return await place_level(session=session, level=level, place_id=place_id)
