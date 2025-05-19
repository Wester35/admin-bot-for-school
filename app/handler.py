from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.types import ReplyKeyboardRemove

from config import config
from app.keyboards import get_news_menu, get_schedule_menu, get_main_menu
from aiogram import F, Router

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


@router.message(CommandStart())
async def cmd_start(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(f"⛔ Доступ запрещен, твой ID:\n{message.from_user.id}",
                             reply_markup=ReplyKeyboardRemove())
        return

    await message.answer(
        "👋 Добро пожаловать в админ-панель!", reply_markup=get_main_menu()
    )

@router.message(Command("help"))
async def get_help(message: Message):
    help_text = """
        📚 Доступные команды:
        /start - Главное меню
        /help - Справка
        """
    await message.answer(help_text)


#===============МЕНЮ==================
@router.message(F.text == "Новости")
async def menu_news(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "📰 Управление новостями:", reply_markup=get_news_menu()
    )


@router.message(F.text == "Расписание")
async def menu_schedule(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "📅 Управление расписанием:", reply_markup=get_schedule_menu()
    )

#===========РАСПИСАНИЕ==========

@router.message(F.photo)
async def get_photo(message: Message):
    await message.answer(f'ID: {message.photo[-1].file_id}')