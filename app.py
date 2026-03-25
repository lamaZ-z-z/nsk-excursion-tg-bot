'''Main module from which the programm starts'''
import asyncio
import os
from dotenv import find_dotenv, load_dotenv 
load_dotenv(find_dotenv())   # так и должно быть

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.strategy import FSMStrategy
from aiogram.client.default import DefaultBotProperties
import logging

from database.engine import create_db, drop_db, after_creation, session_maker
from handlers import user_private_router, admin_router, suggestion_router
from middlewares.db import DataBaseSession



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



bot = Bot(
    token=os.getenv('TOKEN'),  
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML   
    )
)

bot.my_admins_list = [5060090557, 5256135255]



dp = Dispatcher(fsm_strategy=FSMStrategy.USER_IN_CHAT)

dp.include_router(user_private_router)
dp.include_router(suggestion_router)
dp.include_router(admin_router)


async def on_startup(bot: Bot):
    '''Функция, которая выполняется при запуске тг-бота. В ней 
    создаётся база данных, если dropping_db = True, то база данных 
    очищается и создаётся новая.'''
    dropping_db = False
    if dropping_db:
        await drop_db()
        await create_db()
        await after_creation()
    else:
        await create_db()


async def main():
    '''main function that starts bot'''


    dp.startup.register(on_startup)
    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    await bot.delete_webhook(drop_pending_updates=True, request_timeout=40)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == '__main__':
    print("Бот запущен...")
    asyncio.run(main())
