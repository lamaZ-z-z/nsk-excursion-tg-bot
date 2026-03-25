from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

def has_buttons(reply_markup):
    """Проверяет, есть ли кнопки в reply_markup"""
    if reply_markup is None:
        return False
    
    # Для Inline клавиатур
    if isinstance(reply_markup, InlineKeyboardMarkup):
        if reply_markup.inline_keyboard:
            # Проверяем, что есть хотя бы одна непустая строка с кнопками
            return any(len(row) > 0 for row in reply_markup.inline_keyboard)
    
    # Для обычных клавиатур
    elif isinstance(reply_markup, ReplyKeyboardMarkup):
        if reply_markup.keyboard:
            return any(len(row) > 0 for row in reply_markup.keyboard)
    
    return False