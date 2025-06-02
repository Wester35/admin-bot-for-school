import os
import uuid

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.keyboards import get_main_menu, get_news_menu
from app.services.utils import is_admin
import aiohttp
from pathlib import Path


router = Router()

class ScheduleStates(StatesGroup):
    waiting_for_schedule_photo = State()


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