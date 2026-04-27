'''module for handling suggestions of places from users'''
import time
from aiogram import types, Router
from aiogram.filters import Command, or_f, StateFilter
from aiogram.types import ReplyKeyboardRemove
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession


from database.orm_queries import (
    add_place_suggestion,
    add_place_from_suggestion,
    get_district_id
)
from kbds.reply import get_districts_keyboard, get_keyboard
from filters.chat_types import ChatTypeFilter
from common import districts
from common.suggestion_texts import (
    CANCEL,
    FIR_ANS, SEC_ANS, TH_ANS,
     FOUR_ANS, FIF_ANS, SIX_ANS,
      SEV_ANS
    )
from utils.twogislink import find_2gis_link



suggestion_router = Router()
suggestion_router.message.filter(ChatTypeFilter(['private']))

class SuggestionStates(StatesGroup):
    """Состояния для процесса предложки места"""
    waiting_for_district = State()
    waiting_for_place_name = State()
    waiting_for_description = State()
    waiting_for_location_url = State()
    waiting_for_photo = State()


@suggestion_router.message(StateFilter(SuggestionStates), F.text.lower() == 'отмена')
async def cancel(message: types.Message, state: FSMContext):
    '''Функция для отмены добавления места'''
    await message.answer(CANCEL)
    await state.clear()

@suggestion_router.message(Command("suggest"), StateFilter(None))
async def command_suggest(message: types.Message, state: FSMContext):
    '''функция которая отвечает на команду suggest'''
    await message.answer(FIR_ANS, reply_markup=get_districts_keyboard())
    await state.set_state(SuggestionStates.waiting_for_district)




@suggestion_router.message(SuggestionStates.waiting_for_district)
async def handle_district(message: types.Message, state: FSMContext, session: AsyncSession):
    '''Функция для обработки id выбранного района
    и запроса названия места для добавления'''
    if message.text:
        district_name = message.text
        if district_name not in districts:
            await message.answer("Кажется выбранного района нет в списке, попробуй ещё раз")
        else:
            await state.update_data(
                district_id=(await get_district_id(session, district_name)).id['id'],
                district_name=district_name,
                user_id=message.from_user.id
            )
            await message.answer(SEC_ANS, reply_markup=ReplyKeyboardRemove())
            await state.set_state(SuggestionStates.waiting_for_place_name)
    else:
        await message.answer("Нужно выбрать один из предложенных районов! (или напиши \"отмена\" без кавычек)")

@suggestion_router.message(SuggestionStates.waiting_for_place_name)
async def handle_place_name(message: types.Message, state: FSMContext):
    '''Функция для обработки отправленного названия места
    и запроса описания для добавления'''
    if message.text:
        place_name = message.text
        await state.update_data(place_name=place_name)
        await message.answer(TH_ANS)
        await state.set_state(SuggestionStates.waiting_for_description)
    else:
        await message.answer("Нужно отправить название! (или напиши \"отмена\" без кавычек)")


@suggestion_router.message(SuggestionStates.waiting_for_description)
async def handle_description(message: types.Message, state: FSMContext):
    '''Функция для обработки отправленного описания места
    и запроса 2ГИС url для добавления'''
    if message.text:
        description = message.text
        await state.update_data(description=description)
        await message.answer(FOUR_ANS)
        await state.set_state(SuggestionStates.waiting_for_location_url)
    else:
        await message.answer("Нужно отправить описание! (или напиши \"отмена\" без кавычек)")


@suggestion_router.message(SuggestionStates.waiting_for_location_url)
async def handle_url(message: types.Message, state: FSMContext):
    '''Функция для обработки отправленного 2GIS url места
    и фото для добавления'''
    if message.text:
        url = find_2gis_link(message.text)
        if not url:
            await message.answer("Неверный формат ссылки \nПопробуй другую ссылку или напиши \"отмена\",\
    чтобы завершить добавление места")
            return
        await state.update_data(location_url=url)
        await message.answer(FIF_ANS, reply_markup=get_keyboard("Нет фотографии"))
        await state.set_state(SuggestionStates.waiting_for_photo)
    else:
        await message.answer("Нужно отправить ссылку! (или напиши \"отмена\" без кавычек)")


@suggestion_router.message(SuggestionStates.waiting_for_photo)
async def process_photo(message: types.Message, state: FSMContext, session: AsyncSession):
    '''Функция для обработки фото места
    и запроса подтверждения на добавление'''
    # Сохраняем информацию о фото
    if message.photo:
        photo = message.photo[-1] # Получаем самое большое качество фото
        await state.update_data(
            has_photo=True,
            photo_url=photo.file_id
        )
        await message.answer(SIX_ANS, reply_markup=ReplyKeyboardRemove())
    elif message.media_group_id:
        await message.answer("Нужна только одна фотография! Выбери самую лучшую и отправь снова 😁")
        return
    elif message.text:
        if "нет фото" in message.text.lower():
            await message.answer("Принято, без фотографии",
             reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer("Нужно отправить фото или написать \"нет фото\"",
             reply_markup=ReplyKeyboardRemove())
            return
    else:
        await message.answer("Нужно отправить фото! (или напиши \"отмена\" без кавычек)")
    
    data = await state.get_data()
    if (message.from_user.id == 5256135255
        or message.from_user.id == 5060090557
    ):
        new_suggestion = await add_place_suggestion(session=session, status='approved', **cleaned_data)
        await add_place_from_suggestion(session=session, suggested_place=new_suggestion)
        await message.answer(f"Место \"{new_suggestion.place_name}\"\
 теперь доступно в районе {new_suggestion.district_name}")
    else:
        new_suggestion = await add_place_suggestion(session=session, **cleaned_data)
        await message.answer(SEV_ANS)
    await state.clear()
 