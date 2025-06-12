from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Новости")],
            [KeyboardButton(text="Расписание")]
        ],
        resize_keyboard=True
    )

def get_news_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить новость", callback_data="add_news")],
            [InlineKeyboardButton(text="Список новостей", callback_data="list_news")]
        ]
    )

def get_schedule_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Обновить расписание", callback_data="update_schedule")],
            [InlineKeyboardButton(text="Просмотреть текущее", callback_data="view_schedule")]
        ]
    )