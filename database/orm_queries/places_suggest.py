'''Module with orm queries to get suggested places (PlaceSuggest model) from database'''
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from database.models import PlaceSuggestion


async def add_place_suggestion(
    session: AsyncSession,
    district_id: int,
    district_name: str,
    place_name: str,
    description: str,
    user_id: int,
    username: Optional[str] = None,
    full_name: Optional[str] = None,
    location_url: Optional[str] = None,
    has_photo: bool = False,
    photo_url: str = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSbKNeVHxSwGdiF7nCCIKZeGgDKh7aS3h9jDw&s',
    status: str = 'pending'
) -> PlaceSuggestion:
    """
    Добавляет новое предложение места в базу данных.
    Args:
        session: Асинхронная сессия SQLAlchemy
        district_id: ID района
        district_name: Название района
        place_name: Название места
        description: Описание места
        user_id: ID пользователя Telegram
        username: Username пользователя (опционально)
        full_name: Полное имя пользователя (опционально)
        location_url: Ссылка на местоположение в 2GIS (опционально)
        has_photo: Наличие фото (по умолчанию False)
        photo_url: URL фото (по умолчанию стандартная заглушка)
        status: Статус предложки (по умолчанию 'pending')
    
    Returns:
        PlaceSuggestion
    """
    try:
        # Создаем новый объект PlaceSuggestion
        new_suggestion = PlaceSuggestion(
            district_id=district_id,
            district_name=district_name,
            place_name=place_name,
            description=description,
            user_id=user_id,
            username=username,
            full_name=full_name,
            location_url=location_url,
            has_photo=has_photo,
            photo_url=photo_url,
            status=status
        )

        # Добавляем в сессию и сохраняем
        session.add(new_suggestion)
        await session.commit()
        await session.refresh(new_suggestion)
        return new_suggestion

    except Exception as e:
        await session.rollback()
        raise e


async def get_all_suggestions(session: AsyncSession) -> Optional[List[PlaceSuggestion]]:
    '''
    Функция которая возвращает все хранящиеся 
    в базе данных предложения со статусом "pending"
    (т.е. ожидающие рассмотрения)
    '''
    result = await session.execute(
        select(PlaceSuggestion).where(
            PlaceSuggestion.status == 'pending'
            ).order_by(PlaceSuggestion.id)
    )
    return result.scalars().all()

async def get_suggestion_by_id(
    session: AsyncSession,
    suggestion_id: int
) -> Optional[PlaceSuggestion]:
    result = await session.execute(
        select(PlaceSuggestion).where(
            PlaceSuggestion.id == suggestion_id
        )
    )
    return result.scalar_one_or_none()


async def suggestion_status_update(session: AsyncSession, status: str, suggestion_id: int) -> bool:
    try:
        await session.execute(
            update(PlaceSuggestion).where(
                PlaceSuggestion.id == suggestion_id
            ).values(status=status)
        )
        await session.commit()
        return True
    except Exception:
        return False