'''Module for handling admin's messages'''
from typing import Optional
from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardRemove
from aiogram.filters import Command, or_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums.parse_mode import ParseMode
from sqlalchemy.ext.asyncio import AsyncSession

from filters import ChatTypeFilter, IsAdmin
from database.orm_queries import (
    get_all_suggestions,
    suggestion_status_update,
    add_place_from_suggestion,
    get_suggestion_by_id,
    delete_place,
    get_place
)
from common import cmds, districts
from utils.pagination import Paginator, pagination_btns
from kbds.inline import get_suggestions_view_btns, get_del_places_btns
from kbds.reply import get_districts_keyboard
from utils.btns_check import has_buttons


admin_router = Router()
admin_router.message.filter(ChatTypeFilter("private"), IsAdmin())


@admin_router.message(Command("admin"))
async def admin_features(message: types.Message):
    '''Функция отправляет доступные админу команды'''
    await message.answer(text=("Доступные команды:" +
     "\n".join((f"\n/{k}: {v}" for k, v in cmds.items())))
    )



@admin_router.message(Command("suggestions"))
@admin_router.callback_query(F.data.startswith("placeId_"))
async def suggestions_review(
    *,
    session: AsyncSession,
    message: Optional[types.Message] = None,
    callback: Optional[types.CallbackQuery] = None,
    ):
    '''Функция для просматривания и одобрения мест из предложки'''
    place_id = int(callback.data.split('_')[-1])

    paginator = Paginator(array=await get_all_suggestions(session), page=place_id)
    paging_btns = pagination_btns(paginator)
    place = paginator.get_page()

    kbd = get_suggestions_view_btns(pagination_btns=paging_btns,
                                place_id=place_id, paginator=paginator
    )
    image = types.InputMediaPhoto(
        media=place.image,
        caption=f"{place.description}\n--------\nStatus - {place.status}"
    )

    if message:
        await message.answer_photo(
            photo=image.media,
            caption=image.caption,
            reply_markup=kbd
        )
    else:
        await callback.message.edit_photo(
            photo=image.media,
            caption=image.caption,
            reply_markup=kbd
        )
@admin_router.callback_query(or_f(F.data.startswith == 'approved', F.data.startswith == 'rejected'))
async def status_change(callback_query: types.CallbackQuery, session: AsyncSession, ):
    status = callback_query.data.split('_')[0]
    suggestion_id = int(callback_query.data.split('_')[-1])
    await suggestion_status_update(session=session, status=status, suggestion_id=suggestion_id)
    if status == 'approved':
        suggestion = await get_suggestion_by_id(session=session, suggestion_id=suggestion_id)
        await add_place_from_suggestion(session=session,
        suggested_place=suggestion)
        await callback_query.answer(
            text=f'Место "{suggestion.palce_name}" успешно добавлено в район {suggestion.district_name}',
            show_alert=True
        )
    else:
        await callback_query.answer(
            text=f'Статус места "{suggestion.palce_name}" успешно изменён на rejected',
            show_alert=True
        )

# ------------------------------
class DeletionStates(StatesGroup):
    """Состояния для процесса предложки места"""
    waiting_for_district = State()
    waiting_for_deletion = State()


@admin_router.message(StateFilter(DeletionStates), F.text.lower() == 'отмена')
async def handle_cancel(message: types.Message, state: FSMContext):
    await message.answer(text="действия отменены", reply_markup=ReplyKeyboardRemove())
    await state.clear()


@admin_router.message(Command("delete_place"))
async def del_place(message: types.Message, state: FSMContext):
    await message.answer(
        "Выбери на клавиатуре или напиши район, в котором хочешь удалить место",
         reply_markup=get_districts_keyboard()
    )
    await state.set_state(DeletionStates.waiting_for_district)


@admin_router.message(DeletionStates.waiting_for_district, F.text)
async def send_places_to_del(
    message: types.Message,
    session: AsyncSession,
    state: FSMContext,
):
    district = message.text
    if district not in districts:
        await message.answer(
            "Кажется выбранного района нет в списке, попробуй ещё раз или напиши 'отмена'"
        )
    else:
        await state.update_data(district=district)

        reply_markup = await get_del_places_btns(district_name=district, session=session)
        if not has_buttons(reply_markup):
            await message.answer(
                text="Кажется в этом районе нет никаких мест для удаления, был совершён выход из состояния удаления",
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()
            return
        else:
            await message.answer(
                text="ОСТОРОЖНО!!!\nместо, на кнопку которого ты нажмёшь будет безвозвратно удалено,\
    чтобы выйти из режима удаления напиши \"отмена\"",
                reply_markup=reply_markup
            )
            await state.set_state(DeletionStates.waiting_for_deletion)

@admin_router.callback_query(DeletionStates.waiting_for_district, F.data.startswith("page_"))
async def handle_deletion_pagination(
    callback_query: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    data = await state.get_data()
    district = data.get('district')
        
    page = int(callback_query.data.split('_')[-1])
    reply_markup = await get_del_places_btns(
        district_name=district, 
        session=session, 
        page=page
    )
    
    if reply_markup:
        await callback_query.message.edit_reply_markup(reply_markup=reply_markup)
    await callback_query.answer()

@admin_router.callback_query(DeletionStates.waiting_for_deletion, F.data.startswith("delete_"))
async def deleting_place(callback_query: types.CallbackQuery, session: AsyncSession):
    try:
        place_id = int(callback_query.data.split('_')[-1])
        place = await get_place(session, place_id)
        
        await delete_place(session=session, place_id=place_id)
        await callback_query.message.answer(
            text='Место успешно удалено, чтобы выйти из режима удаления напиши "отмена"',
            reply_markup=ReplyKeyboardRemove(),
        )
    except Exception as E:
        await callback_query.message.answer(f"Возникла непредвиденная ошибка\n {E}")
        