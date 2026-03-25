'''Module for keayboard creation'''
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData


from database.orm_queries import (
    get_all_districts,
    get_places_by_district,
    get_place,
    get_all_suggestions
    )
from utils.pagination import Paginator, pagination_btns


class LevelCallBack(CallbackData, prefix="lvl"):
    '''
    Class for orienting with pages
    '''
    # в переменной translit_district транслит имя района
    level: int
    translit_district: Optional[str] = None
    place_id: Optional[int] = None
    page: Optional[int] = None



async def get_user_main_btns(level: int, session: AsyncSession, sizes: tuple[int] = (2,)):
    '''
    function for getting buttons for main page (e.g. page after command /start)
    '''
    keyboard = InlineKeyboardBuilder()
    districts = await get_all_districts(session)
    for district in districts:
        if not district.translit_name:
            district.translit_name = 'unknown'

        keyboard.button(text=district.name, callback_data=LevelCallBack(
            level=level+1,
            translit_district=district.translit_name,
            page=1
        ))
    return keyboard.adjust(*sizes).as_markup()


async def get_places_level_btns(
    level: int,
    translit_district: str,
    session: AsyncSession,
    page: int,
    sizes: tuple[int] = (1,)
):
    '''
    function for getting buttons with places
    '''
    keyboard = InlineKeyboardBuilder()

    places = await get_places_by_district(translit_name=translit_district, session=session)

    paginator = Paginator(array=places, page=page if page else 1, per_page=5)
    page = paginator.get_page()

    for place in page:
        keyboard.button(
            text=place.name, callback_data=LevelCallBack(place_id=place.id, level=level+1)
        )
    
    keyboard.adjust(*sizes)
    keyboard.button(text="назад ↩️",
                    callback_data=LevelCallBack(
                        level=level-1,
                        # translit_district=page[0].district_translit_name if page else None
                    )
    )

    row = []
    for text, menu_name in pagination_btns(paginator).items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text,
                    callback_data=LevelCallBack(
                        level=level,
                        page=page+1)).pack()
            )

        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                    callback_data=LevelCallBack(
                        level=level,
                        page=page-1)).pack()
            )

    return keyboard.row(*row).as_markup()




async def get_place_kbds(
    session: AsyncSession,
    level: int,
    place_id: int,
    sizes: tuple[int] = (1,)
    ):
    '''
    function for getting buttons for particular place
    '''
    keyboard = InlineKeyboardBuilder()
    place = await get_place(session=session, place_id=place_id)

    keyboard.button(text='Ссылка в 2GIS 🗺️', url=place.TwoGisURL)
    keyboard.button(text='Назад ↩️', callback_data=LevelCallBack(
        level=level-1, translit_district=place.district_translit_name)
    )
    keyboard.button(text='В главное меню 🌿', callback_data=LevelCallBack(level=0))
    return keyboard.adjust(*sizes).as_markup()



async def get_suggestions_view_btns(
    place_id: int,
    paginator: Paginator,
    pagination_btns: dict,
    sizes: tuple[int] = (1,),
    page_id: int = 1
    ):
    '''
    Функция которая возвращает инлайн-кнопки ...
    '''
    keyboard = InlineKeyboardBuilder()

    keyboard.button(text="Одобрить", callback_data=f'approved_{place_id}')
    keyboard.button(text='Отклонить', callback_data=f'rejected_{place_id}')

    keyboard.adjust(*sizes)

    row = []
    for text, menu_name in pagination_btns.items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text,
                    callback_data=f"pageId_{page_id+1}").pack())

        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                    callback_data=f"pageId_{page_id-1}").pack())

    return keyboard.row(*row).as_markup()



async def get_del_places_btns(
    district_name: str, 
    session: AsyncSession, 
    sizes: tuple[int] = (1,),
    page: int = 1
):
    '''
    function for getting buttons with places
    '''
    keyboard = InlineKeyboardBuilder()

    places = await get_places_by_district(district_name=district_name, session=session)
    paginator = Paginator(places, page=page, per_page=5)
    page = paginator.get_page()

    for place in page:
        keyboard.button(
            text=place.name, callback_data=f"delete_{place.id}"
        )
    keyboard.adjust(*sizes)

    row = []

    for text, menu_name in pagination_btns(paginator).items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text,
                    callback_data=f"page_{page+1}").pack())

        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                    callback_data=f"page_{page-1}").pack())

    return keyboard.row(*row).as_markup()