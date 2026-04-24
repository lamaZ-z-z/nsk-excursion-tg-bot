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
    get_place,
    update_district
)
from common import cmds, districts
from utils.pagination import Paginator, pagination_btns
from kbds.inline import get_suggestion_view_btns, get_del_places_btns
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
async def suggestions_review(message: types.Message, session: AsyncSession):
    '''Функция для просматривания и одобрения мест из предложки'''
    suggestions = await get_all_suggestions(session)
    if not suggestions:
        await message.answer("Кажется в предложке ещё нет предложений")
        return
    paginator = Paginator(array=suggestions)
    paging_btns = pagination_btns(paginator)
    place = paginator.get_page()[0]
    kbd = get_suggestion_view_btns(place_id=place.id, paging_btns=paging_btns, page_id=1)
    image = types.InputMediaPhoto(
        media=place.photo_url,
        caption=f"Предложение \"{place.place_name}\" в район {place.district_name}\n\n\
{place.description}\n{place.location_url}\n--------\nStatus - {place.status}"
    )
    await message.answer_photo(
        photo=image.media,
        caption=image.caption,
        reply_markup=kbd
    )

@admin_router.callback_query(F.data.startswith("pageId_"))
async def suggestion_view(callback: types.CallbackQuery, session: AsyncSession):
    page_id = int(callback.data.split('_')[-1])
    paginator = Paginator(array=await get_all_suggestions(session), page=page_id)
    paging_btns = pagination_btns(paginator)
    place = paginator.get_page()[0]
    kbd = get_suggestion_view_btns(place_id=place.id, paging_btns=paging_btns, page_id=page_id)
    image = types.InputMediaPhoto(
        media=place.photo_url,
        caption=f"Предложение \"{place.place_name}\" в район {place.district_name}\n\n\
{place.description}\n{place.location_url}\n--------\nStatus - {place.status}"
    ) 
    await callback.message.edit_media(
        media=image,
        reply_markup=kbd)


@admin_router.callback_query(or_f(F.data.startswith('approved_'), F.data.startswith('rejected_')))
async def status_change(callback_query: types.CallbackQuery, session: AsyncSession, ):
    status = callback_query.data.split('_')[0]
    suggestion_id = int(callback_query.data.split('_')[-1])
    suggestion = await get_suggestion_by_id(session=session, suggestion_id=suggestion_id)
    await suggestion_status_update(session=session, status=status, suggestion_id=suggestion_id)
    if status == 'approved':
        await add_place_from_suggestion(session=session, suggested_place=suggestion)
        await callback_query.answer(
            text=f'Место "{suggestion.place_name}" успешно добавлено в район {suggestion.district_name}',
            show_alert=True
        )
    else:
        await callback_query.answer(
            text=f'Статус места "{suggestion.place_name}" успешно изменён на rejected',
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

@admin_router.callback_query(DeletionStates.waiting_for_deletion, F.data.startswith("page_"))
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
        page_num=page
    )
    
    if reply_markup:
        await callback_query.message.edit_reply_markup(reply_markup=reply_markup)
    await callback_query.answer()

@admin_router.callback_query(DeletionStates.waiting_for_deletion, F.data.startswith("delete_"))
async def deleting_place(callback_query: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    try:
        place_id = int(callback_query.data.split('_')[-1])
        place = await get_place(session, place_id)
        
        await delete_place(session=session, place_id=place_id)
        await callback_query.message.answer(
            text=f'Место {place.name} успешно удалено, чтобы выйти из режима удаления напиши "отмена"',
            reply_markup=ReplyKeyboardRemove(),
        )
        data = await state.get_data()
        district = data.get('district')
            
        page = int(callback_query.data.split('_')[-1])
        reply_markup = await get_del_places_btns(
            district_name=district, 
            session=session, 
            page_num=1
        )
        
        if reply_markup:
            await callback_query.message.edit_reply_markup(reply_markup=reply_markup)
        await callback_query.answer()
    except Exception as E:
        await callback_query.message.answer(f"Возникла непредвиденная ошибка\n {E}")

# -------------------------------------
class ChangeBannerStates(StatesGroup):
    """Состояния для процесса предложки места"""
    waiting_for_district = State()
    waiting_for_photo = State()
    commiting = State()

@admin_router.message(StateFilter(ChangeBannerStates), F.text.lower() == 'отмена')
async def cancel(message: types.Message, state: FSMContext):
    '''Функция для отмены добавления места'''
    await message.answer("Действия отменены", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@admin_router.message(Command("change_banner"), StateFilter(None))
async def command_suggest(message: types.Message, state: FSMContext):
    '''функция которая отвечает на команду suggest'''
    await message.answer("Выбери у какого района хочешь изменить банер", reply_markup=get_districts_keyboard())
    await state.set_state(ChangeBannerStates.waiting_for_district)

@admin_router.message(ChangeBannerStates.waiting_for_district, F.text)
async def district_processing(message: types.Message, state: FSMContext):
    try:
        district = message.text
        translit_name = districts[district]['translit_name']
        await state.update_data(translit_name=translit_name)
        await message.answer("Теперь нужно отправить фотографию", reply_markup=ReplyKeyboardRemove())
        await state.set_state(ChangeBannerStates.waiting_for_photo)
    except Exception as e:
        await message.answer(f"Произошла ошибка, напиши \"отмена\" для возвращения к обычной работе бота: \n{e}")
        return

@admin_router.message(ChangeBannerStates.waiting_for_photo, or_f(F.photo, F.text))
async def process_photo(message: types.Message, state: FSMContext, session: AsyncSession):
    '''Функция для обработки фото места
    и запроса подтверждения на добавление'''
    # Сохраняем информацию о фото
    try:
        if message.photo:
            image = message.photo[-1]['file_id'] # Получаем самое большое качество фото
            data = await state.get_data()
            await update_district(session=session, translit_name=data['translit_name'], image=image)
            await message.answer("Фото успешно изменено :)")
            await state.clear()

        elif message.media_group_id:
            await message.answer("Нужна только одна фотография! Выбери самую лучшую и отправь снова 😁")
            return
        elif message.text:
            await message.answer("Отправь фотографию или напиши \"отмена\"(без кавычек), чтобы вернутся к обычной работе бота")
            return
    except Exception as e:
        await message.answer(f"Произошла ошибка, напиши \"отмена\" для возвращения к обычной работе бота: \n{e}")
        return
