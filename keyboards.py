from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('Новости'))
    keyboard.add(KeyboardButton('Расписание'))
    return keyboard

def get_news_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('Добавить новость', callback_data='add_news'))
    keyboard.add(InlineKeyboardButton('Список новостей', callback_data='list_news'))
    return keyboard

def get_schedule_menu():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('Обновить расписание', callback_data='update_schedule'))
    keyboard.add(InlineKeyboardButton('Просмотреть текущее', callback_data='view_schedule'))
    return keyboard