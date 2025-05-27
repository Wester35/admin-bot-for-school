import os
import uuid
from pathlib import Path

from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InputFile, FSInputFile, InputMediaPhoto
from aiogram.types import ReplyKeyboardRemove
from config import config
from app.keyboards import get_news_menu, get_schedule_menu, get_main_menu
from aiogram import F, Router

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


class NewsStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_content = State()
    waiting_for_photos = State()

class ScheduleStates(StatesGroup):
    waiting_for_schedule_photo = State()

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


#===========НОВОСТИ=============
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
    # photos = data.get("photos", [])
    # photos.append(message.photo[-1].file_id)
    # await state.update_data(photos=photos)
    # await message.answer(f"Фото сохранено. Отправьте ещё или введите 'Готово'.")


# Завершение
@router.message(NewsStates.waiting_for_photos, F.text.lower() == "готово")
async def finish_news_creation(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data.get("title")
    content = data.get("content")
    photos = data.get("photos", [])

    folder = Path("news")
    folder.mkdir(exist_ok=True)

    # Файлы фотографий
    photo_filenames = []
    for idx, file_id in enumerate(photos, 1):
        file = await message.bot.get_file(file_id)
        file_path = file.file_path
        dest_filename = folder / f"{title} - photo_{idx}.jpg"
        await message.bot.download_file(file_path, destination=dest_filename)
        photo_filenames.append(dest_filename.name)

    # .txt
    txt_path = folder / f"{title}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"{content}\n\nФайлы изображений:\n")
        for name in photo_filenames:
            f.write(f"{name}\n")

    await message.answer(f"Новость сохранена в файлы.", reply_markup=get_main_menu())
    await state.clear()

@router.message(F.text == "/cancel")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=get_main_menu())

#===========РАСПИСАНИЕ==========
@router.callback_query(F.data == 'update_schedule')
async def update_schedule(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен")
        return
    await callback.message.edit_text("Отправьте фотографию расписания:")
    await state.set_state(ScheduleStates.waiting_for_schedule_photo)
    await callback.answer()

#функцию ниже требуется переделать чтобы она отправляла расписание с сайта + убрать потерю качества
@router.message(ScheduleStates.waiting_for_schedule_photo, F.photo | F.document)
async def save_schedule(message: Message, state: FSMContext):
    try:
        os.makedirs("schedules", exist_ok=True)
        file_id = None
        filename = None

        if message.photo:
            photo = message.photo[-1]
            file_id = photo.file_id
            file_ext = "jpg"
            filename = f"schedules/schedule_{uuid.uuid4()}.{file_ext}"

        elif message.document:
            allowed_extensions = ['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx']
            file_ext = message.document.file_name.split('.')[-1].lower()

            if file_ext not in allowed_extensions:
                await message.answer(
                    "❌ Недопустимый формат файла. Разрешены: " +
                    ", ".join(allowed_extensions)
                )
                return

            file_id = message.document.file_id
            filename = f"schedules/schedule_{uuid.uuid4()}.{file_ext}"

        if file_id and filename:
            file = await message.bot.get_file(file_id)
            await message.bot.download_file(file.file_path, filename)

            await message.answer(
                "✅ Расписание успешно обновлено!\n"
                f"Файл сохранен как: {os.path.basename(filename)}",
                reply_markup=get_main_menu()
            )
        else:
            await message.answer("❌ Не удалось обработать файл")

    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении: {str(e)}")
    finally:
        await state.clear()

#функцию ниже требуется переделать чтобы она получала расписание с сайта + убрать потерю качества
@router.callback_query(F.data == 'view_schedule')
async def view_schedule(callback: CallbackQuery):
    try:
        if not os.path.exists("schedules"):
            await callback.message.edit_text("Расписание еще не добавлено")
            await callback.answer()
            return
        schedule_files = sorted(
            [f for f in os.listdir("schedules") if f.startswith("schedule_")],
            key=lambda x: os.path.getmtime(os.path.join("schedules", x)),
            reverse=True
        )

        if not schedule_files:
            await callback.message.edit_text("Расписание еще не добавлено")
            await callback.answer()
            return

        latest_file = os.path.join("schedules", schedule_files[0])
        file_ext = latest_file.split('.')[-1].lower()

        if file_ext in ['jpg', 'jpeg', 'png']:
            await callback.message.answer_photo(
                FSInputFile(latest_file),
                caption="📅 Текущее расписание"
            )
        else:
            await callback.message.answer_document(
                FSInputFile(latest_file),
                caption="📅 Текущее расписание (файл)"
            )

    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при загрузке расписания: {str(e)}")
    finally:
        await callback.answer()