import os
import shutil
import uuid
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InputFile
from config import config
from api_client import ApiClient
from keyboards import get_main_menu, get_news_menu, get_schedule_menu
import asyncio
import logging

async def cleanup_downloads():
    """Очищает папку с временными загрузками"""
    if os.path.exists('downloads'):
        shutil.rmtree('downloads', ignore_errors=True)
    os.makedirs('downloads', exist_ok=True)

async def on_startup():
    await cleanup_downloads()
    logger.info("Очищены временные файлы")

async def on_shutdown():
    await cleanup_downloads()
    logger.info("Бот выключается, очистка файлов")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
api = ApiClient()

if not os.path.exists('uploaded_news'):
    os.makedirs('uploaded_news')


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
    await state.set_state(NewsStates.waiting_for_content)


@dp.message(NewsStates.waiting_for_content)
async def process_news_content(message: types.Message, state: FSMContext):
    await state.update_data(content=message.text)
    await message.answer(
        "📸 Отправьте одно или несколько фото (можно с подписью)\n"
        "Когда закончите, нажмите /done\n"
        "Для отмены /cancel",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="/done")],
                [KeyboardButton(text="/cancel")]
            ],
            resize_keyboard=True
        )
    )
    await state.update_data(photos=[])
    await state.set_state(NewsStates.waiting_for_media)


async def download_photo(photo: types.PhotoSize, path: str) -> str:
    file = await bot.get_file(photo.file_id)
    file_path = f"uploaded_news/{path}_{photo.file_id}.jpg"
    await bot.download_file(file.file_path, file_path)
    return file_path


@dp.message(NewsStates.waiting_for_media, F.media_group_id)
async def handle_album(message: types.Message, album: list[types.Message], state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])

    for msg in album:
        if msg.photo:
            photo = msg.photo[-1]  # Берем самое качественное фото
            file_path = await download_photo(photo, str(uuid.uuid4()))
            photos.append(file_path)

    await state.update_data(photos=photos)
    await message.answer(f"✅ Добавлено {len(album)} фото (всего: {len(photos)})")


@dp.message(NewsStates.waiting_for_media, F.photo)
async def handle_single_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])

    photo = message.photo[-1]
    file_path = await download_photo(photo, str(uuid.uuid4()))
    photos.append(file_path)

    await state.update_data(photos=photos)
    await message.answer(f"✅ Фото добавлено (всего: {len(photos)})")


@dp.message(NewsStates.waiting_for_media, Command("done"))
async def finish_news(message: types.Message, state: FSMContext):
    data = await state.get_data()

    result = api.add_news(
        title=data['title'],
        content=data['content'],
        photos=data.get('photos', [])
    )

    photo_count = len(data.get('photos', []))
    response = f"✅ Новость добавлена (ID: {result['id']})"
    if photo_count > 0:
        response += f"\n📸 Фото: {photo_count} шт."

    await message.answer(
        response,
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()


@dp.callback_query(F.data == "list_news")
async def list_news(callback: types.CallbackQuery):
    news = api.get_news()
    if not news['news']:
        await callback.message.answer("📭 Список новостей пуст")
        return

    response = "📋 Последние новости:\n\n"
    for item in reversed(news['news'][-5:]):  # Показываем новые сверху
        response += f"📅 <b>{item['created_at']}</b>\n"
        response += f"📌 <b>{item['title']}</b>\n"
        response += f"{item['content']}\n"

        if item['photos']:
            media_group = []
            for i, photo_path in enumerate(item['photos'], 1):
                if os.path.exists(photo_path):
                    photo = InputFile(photo_path)
                    if i == 1:
                        media_group.append(types.InputMediaPhoto(
                            media=photo,
                            caption=response
                        ))
                    else:
                        media_group.append(types.InputMediaPhoto(media=photo))

            try:
                await callback.message.answer_media_group(media_group)
                response = ""  # Очищаем, т.к. текст уже в медиагруппе
            except Exception as e:
                logger.error(f"Ошибка отправки фото: {e}")
                response += f"\n🖼 [Фото {len(item['photos'])} шт.]\n"

        if response.strip():  # Если остался текст для отправки
            await callback.message.answer(response)
            response = ""
            await callback.answer()


@dp.message(Command("media"))
async def cmd_media(message: types.Message):
    media = []
    for root, _, files in os.walk('uploaded_news'):
        for file in files[:10]:  # Первые 10 файлов
            media.append(InputFile(os.path.join(root, file)))

    if media:
        await message.answer_media_group([types.InputMediaPhoto(media=photo) for photo in media])
    else:
        await message.answer("Нет сохраненных фото")

@dp.message(Command("cancel"))
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Действие отменено", reply_markup=ReplyKeyboardRemove())
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
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    asyncio.run(main())