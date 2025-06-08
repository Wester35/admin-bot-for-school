import os
import uuid

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, BufferedInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.keyboards import get_main_menu, get_news_menu
from app.services.schedule_api import upload_schedule_to_api, fetch_schedule
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

@router.message(ScheduleStates.waiting_for_schedule_photo, F.photo | F.document)
async def save_schedule(message: Message, state: FSMContext):
    try:
        file_id = None
        filename = None

        if message.photo:
            photo = message.photo[-1]
            file_id = photo.file_id
            file_ext = "jpg"
            filename = f"schedule_{uuid.uuid4()}.{file_ext}"

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
            filename = f"schedule_{uuid.uuid4()}.{file_ext}"

        if file_id:
            tmp_path = Path("tmp") / filename
            tmp_path.parent.mkdir(exist_ok=True)
            file = await message.bot.get_file(file_id)
            await message.bot.download_file(file.file_path, destination=str(tmp_path))

            status, resp_text = await upload_schedule_to_api(tmp_path)
            tmp_path.unlink(missing_ok=True)

            if status in (200, 201):
                await message.answer("✅ Расписание успешно загружено на сервер!", reply_markup=get_main_menu())
            else:
                await message.answer(f"❌ Ошибка при отправке: {resp_text}")
        else:
            await message.answer("❌ Не удалось получить файл")

    except Exception as e:
        await message.answer(f"❌ Ошибка при загрузке: {str(e)}")
    finally:
        await state.clear()


@router.callback_query(F.data == 'view_schedule')
async def view_schedule(callback: CallbackQuery):
    try:
        content, content_type = await fetch_schedule()
        if content is None:
            await callback.message.edit_text("Расписание еще не добавлено")
            return

        ext = 'jpg' if 'jpeg' in content_type else 'png'
        filename = f"schedule.{ext}"

        file = BufferedInputFile(content, filename=filename)

        if content_type in ['image/jpeg', 'image/png']:
            await callback.message.answer_photo(file, caption="📅 Текущее расписание")
        else:
            await callback.message.answer_document(file, caption="📅 Текущее расписание (файл)")

    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при загрузке расписания: {str(e)}")
    finally:
        await callback.answer()
