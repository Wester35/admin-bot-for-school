from mailbox import Message

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove
from config import config
from api_client import ApiClient
from keyboards import get_main_menu, get_news_menu, get_schedule_menu
import asyncio
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
api = ApiClient()


class NewsStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_content = State()
    waiting_for_media = State()


class ScheduleStates(StatesGroup):
    waiting_for_schedule = State()


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


# ================= ОБРАБОТЧИКИ КОМАНД =================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещен", reply_markup=ReplyKeyboardRemove())
        return

    await message.answer(
        "👋 Добро пожаловать в админ-панель!",
        reply_markup=get_main_menu()
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = """
    📚 Доступные команды:
    /start - Главное меню
    /help - Справка
    /clear - Очистить все данные (только для теста)
    """
    await message.answer(help_text)


@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    api.clear_all()
    await message.answer("🔄 Все данные очищены")


# ================= ОБРАБОТЧИКИ МЕНЮ =================
@dp.message(F.text == "Новости")
async def menu_news(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "📰 Управление новостями:",
        reply_markup=get_news_menu()
    )


@dp.message(F.text == "Расписание")
async def menu_schedule(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "📅 Управление расписанием:",
        reply_markup=get_schedule_menu()
    )


# ================= НОВОСТИ =================
@dp.callback_query(F.data == "add_news")
async def add_news_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("✏ Введите заголовок новости:")
    await state.set_state(NewsStates.waiting_for_title)
    await callback.answer()


@dp.message(NewsStates.waiting_for_title)
async def process_news_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📝 Теперь введите содержание новости:")
    await state.set_state(NewsStates.waiting_for_media)

@dp.message(F.photo)
async def photo_handler(message: Message) -> None:


@dp.message(NewsStates.waiting_for_media)
async def process_news_title(message: types.Message, state: FSMContext):
    photo_data = message.photo[-1]
    await state.update_data(title=message.photo)
    await message.answer("📝 Теперь отправьте фото:")
    await state.set_state(NewsStates.waiting_for_content)

@dp.message(NewsStates.waiting_for_content)
async def process_news_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    result = api.add_news(data['title'], message.text)

    await message.answer(f"✅ Новость добавлена (ID: {result['id']})")
    await state.clear()


@dp.callback_query(F.data == "list_news")
async def list_news(callback: types.CallbackQuery):
    news = api.get_news()
    if not news['news']:
        await callback.message.answer("📭 Список новостей пуст")
        return

    response = "📋 Последние новости:\n\n"
    for item in news['news'][-5:]:  # Показываем 5 последних
        response += f"📌 <b>{item['title']}</b>\n{item['content']}\n\n"

    await callback.message.answer(response)
    await callback.answer()


# ================= РАСПИСАНИЕ =================
@dp.callback_query(F.data == "update_schedule")
async def update_schedule_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("✏ Введите новое расписание:")
    await state.set_state(ScheduleStates.waiting_for_schedule)
    await callback.answer()


@dp.message(ScheduleStates.waiting_for_schedule)
async def process_schedule_update(message: types.Message, state: FSMContext):
    result = api.update_schedule(message.text)
    await message.answer("✅ Расписание обновлено")
    await state.clear()


@dp.callback_query(F.data == "view_schedule")
async def view_schedule(callback: types.CallbackQuery):
    schedule = api.get_schedule()
    response = f"📅 Текущее расписание:\n\n{schedule['data']}"

    if schedule['last_updated']:
        response += f"\n\n🔄 Обновлено: {schedule['last_updated']}"

    await callback.message.answer(response)
    await callback.answer()


# ================= ЗАПУСК БОТА =================
async def main():
    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())