from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.keyboards import get_main_menu, get_news_menu
from app.services.utils import is_admin
from app.services.news_api import upload_news_to_api, fetch_news_list, fetch_news_by_id
import aiohttp
from pathlib import Path



API_URL = "http://localhost:41235/news/add"
API_LIST_URL = "http://localhost:41235/news"


router = Router()


class NewsStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_content = State()
    waiting_for_photos = State()


@router.callback_query(F.data == "list_news")
async def list_news(callback: CallbackQuery):
    try:
        data = await fetch_news_list()
        if not data:
            await callback.message.answer("🔍 Новостей пока нет.")
            return

        kb = InlineKeyboardMarkup()
        for news in data:
            title = news.get("title", "Без названия")
            news_id = news.get("id")
            kb.add(InlineKeyboardButton(title, callback_data=f"news_{news_id}"))

        await callback.message.answer("📰 Список новостей:", reply_markup=kb)

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {e}")


@router.callback_query(F.data.startswith("news_"))
async def show_single_news(callback: CallbackQuery):
    news_id = callback.data.split("_")[1]

    try:
        news = await fetch_news_by_id(news_id)
        text = f"📰 <b>{news.get('title')}</b>\n\n{news.get('content')}"
        await callback.message.answer(text, parse_mode="HTML")

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {e}")



@router.callback_query(F.data == 'add_news')
async def add_news(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен")
        return
    await callback.message.edit_text("Введите текст новости:")
    await state.set_state(NewsStates.waiting_for_title)
    await callback.answer()

@router.message(NewsStates.waiting_for_title, F.text)
async def save_news_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите содержание новости:")
    await state.set_state(NewsStates.waiting_for_content)

@router.message(NewsStates.waiting_for_content, F.text)
async def save_news_content(message: Message, state: FSMContext):
    await state.update_data(content=message.text)
    await message.answer("Теперь отправьте все фото для новости. Когда закончите — отправьте 'Готово'.")
    await state.set_state(NewsStates.waiting_for_photos)
    await state.update_data(photos=[])

@router.message(NewsStates.waiting_for_photos, F.photo | F.document)
async def save_news_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])

    if message.photo:
        file_id = message.photo[-1].file_id
        photos.append(file_id)
        await state.update_data(photos=photos)
        await message.answer("Фото добавлено. Отправьте ещё или напишите 'Готово'.")

    elif message.document:
        if message.document.mime_type in ["image/jpeg", "image/jpg", "image/png"]:
            file_id = message.document.file_id
            photos.append(file_id)
            await state.update_data(photos=photos)
            await message.answer("Изображение-документ добавлено. Отправьте ещё или напишите 'Готово'.")
        else:
            await message.answer("⛔ Поддерживаются только изображения JPEG, JPG, PNG.")
    else:
        await message.answer("Отправьте фото или изображение-документ, либо напишите 'Готово'.")


@router.message(NewsStates.waiting_for_photos, F.text.lower() == "готово")
async def finish_news_creation(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data.get("title")
    content = data.get("content")
    photos = data.get("photos", [])

    if not title or not content:
        await message.answer("❌ Ошибка: отсутствуют заголовок или содержимое.")
        await state.clear()
        return

    files = []
    try:
        temp_folder = Path("temp_news_upload")
        temp_folder.mkdir(exist_ok=True)

        for idx, file_id in enumerate(photos, 1):
            file = await message.bot.get_file(file_id)
            file_path = file.file_path
            local_path = temp_folder / f"photo_{idx}.jpg"
            await message.bot.download_file(file_path, destination=local_path)
            files.append(local_path)

        status, response_text = await upload_news_to_api(title, content, files)

        if status == 200:
            await message.answer("✅ Новость успешно отправлена!", reply_markup=get_main_menu())
        else:
            await message.answer(f"❌ Ошибка при отправке: {status}\n{response_text}")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        await state.clear()
    for file_path in files:
        try:
            file_path.unlink()
        except Exception:
            pass

@router.message(F.text == "/cancel")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=get_main_menu())
