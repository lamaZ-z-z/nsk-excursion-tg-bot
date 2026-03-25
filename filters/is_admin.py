from aiogram.filters import Filter
from aiogram import types, Bot


class IsAdmin(Filter):
    '''класс определяет пришло ли сообщение от админа или нет'''
    def __init__(self) -> None:
        pass
    
    async def __call__(self, message: types.Message, bot: Bot) -> bool:
        return message.from_user.id in bot.my_admins_list