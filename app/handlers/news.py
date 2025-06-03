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


class EditNewsStates(StatesGroup):
    waiting_for_new_title = State()
    waiting_for_new_content = State()
    waiting_for_new_photos = State()


@router.callback_query(F.data == "list_news")
async def list_news(callback: CallbackQuery):
    try:
        data = await fetch_news_list()
        if not data:
            await callback.message.answer("🔍 Новостей пока нет.")
            return

        buttons = [
            [InlineKeyboardButton(text=news.get("title", "Без названия"), callback_data=f"news_{news.get('id')}")]
            for news in data
        ]

        kb = InlineKeyboardMarkup(inline_keyboard=buttons, row_width=1)

        await callback.message.edit_text("📰 Список новостей:", reply_markup=kb)

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {e}")


@router.callback_query(F.data.startswith("news_"))
async def show_single_news(callback: CallbackQuery):
    news_id = callback.data.split("_")[1]

    try:
        news = await fetch_news_by_id(news_id)
        text = f"📰 <b>{news.get('title')}</b>\n\n{news.get('content')}"

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✏️ Изменить", callback_data=f"edit_news_{news_id}"),
                    InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"confirm_delete_{news_id}"),
                    InlineKeyboardButton(text="<-- Назад", callback_data=f"list_news")
                ]
            ],
            row_width=3
        )

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {e}")

@router.callback_query(F.data.startswith("confirm_delete_"))
async def delete_news(callback: CallbackQuery):
    news_id = callback.data.split("_")[2]

    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    async with aiohttp.ClientSession() as session:
        async with session.delete(f"http://localhost:41235/news/delete/{news_id}") as resp:
            if resp.status == 200:
                await callback.message.edit_text("✅ Новость удалена.")
            else:
                text = await resp.text()
                await callback.message.edit_text(f"❌ Ошибка при удалении: {resp.status}\n{text}")

    await callback.answer()

@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    await callback.message.edit_text("Удаление отменено.", reply_markup=get_main_menu())
    await callback.answer()



@router.callback_query(F.data == 'add_news')
async def add_news(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен")
        return
    await callback.message.answer("Введите текст новости:")
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


@router.callback_query(F.data.startswith("edit_news_"))
async def start_edit_news(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен")
        return
    news_id = callback.data.split("_")[2]
    await state.update_data(news_id=news_id)
    await callback.message.answer("Введите новый заголовок новости:")
    await state.set_state(EditNewsStates.waiting_for_new_title)
    await callback.answer()


@router.message(EditNewsStates.waiting_for_new_title, F.text)
async def save_new_title(message: Message, state: FSMContext):
    await state.update_data(new_title=message.text)
    await message.answer("Введите новое содержание новости:")
    await state.set_state(EditNewsStates.waiting_for_new_content)


@router.message(EditNewsStates.waiting_for_new_content, F.text)
async def save_new_content(message: Message, state: FSMContext):
    await state.update_data(new_content=message.text)
    await message.answer("Отправьте новые фото для новости. Когда закончите — отправьте 'Готово' или 'Пропустить'.")
    await state.set_state(EditNewsStates.waiting_for_new_photos)
    await state.update_data(new_photos=[])


@router.message(EditNewsStates.waiting_for_new_photos, F.photo | F.document)
async def save_new_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("new_photos", [])

    if message.photo:
        file_id = message.photo[-1].file_id
        photos.append(file_id)
        await state.update_data(new_photos=photos)
        await message.answer("Фото добавлено. Отправьте ещё или напишите 'Готово' / 'Пропустить'.")

    elif message.document:
        if message.document.mime_type in ["image/jpeg", "image/jpg", "image/png"]:
            file_id = message.document.file_id
            photos.append(file_id)
            await state.update_data(new_photos=photos)
            await message.answer("Изображение-документ добавлено. Отправьте ещё или напишите 'Готово' / 'Пропустить'.")
        else:
            await message.answer("⛔ Поддерживаются только изображения JPEG, JPG, PNG.")
    else:
        await message.answer("Отправьте фото или изображение-документ, либо напишите 'Готово' / 'Пропустить'.")


@router.message(EditNewsStates.waiting_for_new_photos, F.text.lower().in_({"готово", "пропустить"}))
async def finish_edit_news(message: Message, state: FSMContext):
    data = await state.get_data()
    news_id = data.get("news_id")
    new_title = data.get("new_title")
    new_content = data.get("new_content")
    new_photos = data.get("new_photos", [])

    files = []
    try:
        temp_folder = Path("temp_news_upload")
        temp_folder.mkdir(exist_ok=True)

        for idx, file_id in enumerate(new_photos, 1):
            file = await message.bot.get_file(file_id)
            file_path = file.file_path
            local_path = temp_folder / f"photo_{idx}.jpg"
            await message.bot.download_file(file_path, destination=local_path)
            files.append(local_path)

        form = aiohttp.FormData()
        form.add_field('title', new_title)
        form.add_field('content', new_content)

        if files:
            for file_path in files:
                form.add_field(
                    'files',
                    open(file_path, 'rb'),
                    filename=file_path.name,
                    content_type='image/jpeg'
                )
        else:
            form.add_field('files', b'', filename='', content_type='application/octet-stream')

        async with aiohttp.ClientSession() as session:
            url = f"http://localhost:41235/news/update/{news_id}"
            async with session.patch(url, data=form) as resp:
                status = resp.status
                text = await resp.text()

        if status == 200:
            await message.answer("✅ Новость успешно обновлена!", reply_markup=get_main_menu())
        else:
            await message.answer(f"❌ Ошибка при обновлении: {status}\n{text}")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

    finally:
        await state.clear()
    for file_path in files:
        try:
            file_path.unlink()
        except Exception:
            pass
