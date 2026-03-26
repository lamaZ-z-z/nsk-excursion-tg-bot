'''module for handling user private messages'''
from aiogram import types, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from kbds.inline import LevelCallBack
from filters.chat_types import ChatTypeFilter
from handlers.level_processing import get_levels_content



user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(['private']))


@user_private_router.message(CommandStart(), StateFilter(None))
async def start_cmd(message: types.Message, session: AsyncSession):
    '''
    answer on /start message from user
    '''
    image, reply_markup = await get_levels_content(session=session, level=0, translit_district=None)
    await message.answer_photo(image.media, caption=image.caption, reply_markup=reply_markup)



@user_private_router.callback_query(LevelCallBack.filter())
async def level_callback_handling(
    callback: types.CallbackQuery,
    callback_data: LevelCallBack,
    session: AsyncSession
):
    '''
    '''
    image, reply_markup = await get_levels_content(
        session=session,
        level=callback_data.level,
        translit_district=callback_data.translit_district,
        place_id=callback_data.place_id,
        page_num=callback_data.page
    )
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=image.media,
            caption=image.caption),
        reply_markup=reply_markup
    )
    await callback.answer()
