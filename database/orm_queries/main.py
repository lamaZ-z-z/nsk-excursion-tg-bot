'''Module providing orm fucntions to get info about districts'''
from typing import Optional, List

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import MainBanner
from database import orm_queries



async def add_main_banner(
    session: AsyncSession,
    image: str,
    description: Optional[str] = None
) -> MainBanner:
    """Добавление нового баннера"""
    banner = MainBanner(
        image=image,
        description=description
    )
    session.add(banner)
    await session.commit()
    await session.refresh(banner)
    return banner


async def get_main_banner(
    session: AsyncSession,
    *,
    banner_id: Optional[int] = None
) -> Optional[MainBanner]:
    """Получение баннера по ID"""
    if banner_id:
        result = await session.execute(
            select(MainBanner).where(MainBanner.id == banner_id)
        )
    else:
        result = await session.execute(
            select(MainBanner)
        )
    return result.scalar_one_or_none()


async def get_all_main_banners(
    session: AsyncSession
) -> List[MainBanner]:
    """Получение всех баннеров"""
    result = await session.execute(
        select(MainBanner).order_by(MainBanner.id)
    )
    return result.scalars().all()


async def update_main_banner(
    session: AsyncSession,
    banner_id: int,
    **kwargs
) -> Optional[MainBanner]:
    """Обновление баннера"""
    await session.execute(
        update(MainBanner)
        .where(MainBanner.id == banner_id)
        .values(**kwargs)
    )
    await session.commit()
    return await orm_queries.get_main_banner(session, banner_id=banner_id)


async def delete_main_banner(
    session: AsyncSession,
    banner_id: int
) -> bool:
    """Удаление баннера"""
    result = await session.execute(
        delete(MainBanner).where(MainBanner.id == banner_id)
    )
    await session.commit()
    return result.rowcount > 0