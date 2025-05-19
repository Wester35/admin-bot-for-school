# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Новости")],
            [KeyboardButton(text="📅 Расписание")]
        ],
        resize_keyboard=True
    )

def get_news_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить новость")],
            [KeyboardButton(text="📋 Список новостей")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def get_schedule_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить расписание")],
            [KeyboardButton(text="📋 Список расписаний")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
