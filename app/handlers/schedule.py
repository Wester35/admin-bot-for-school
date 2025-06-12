import uuid
from io import BytesIO
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from app.keyboards import get_main_menu
from app.services.schedule_api import upload_schedule_to_api, fetch_schedule
from app.services.utils import is_admin


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
        elif message.document:
            allowed_extensions = ['jpg', 'jpeg', 'png']
            file_ext = message.document.file_name.split('.')[-1].lower()

            if file_ext not in allowed_extensions:
                await message.answer(
                    "❌ Недопустимый формат файла. Разрешены: " +
                    ", ".join(allowed_extensions)
                )
                return

            file_id = message.document.file_id
        else:
            await message.answer("❌ Не удалось получить файл")
            return

        filename = f"schedule_{uuid.uuid4()}.{file_ext}"
        tg_file = await message.bot.get_file(file_id)
        file_bytes = await message.bot.download_file(tg_file.file_path)

        bio = BytesIO(file_bytes.read())
        status, resp_text = await upload_schedule_to_api(bio, filename)

        if status in (200, 201):
            await message.answer(f"✅ {resp_text.strip()}", reply_markup=get_main_menu())
        else:
            await message.answer(f"❌ Ошибка при отправке: {resp_text}")

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
