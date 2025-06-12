import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram.types import Message, PhotoSize, CallbackQuery
from app.handlers.schedule import save_schedule, ScheduleStates, view_schedule


@pytest.mark.asyncio
@patch("os.makedirs")
@patch("app.handlers.schedule.get_main_menu")
@patch("aiogram.Bot.get_file", new_callable=AsyncMock)
@patch("aiogram.Bot.download_file", new_callable=AsyncMock)
@patch("aiogram.types.Message.answer", new_callable=AsyncMock)
async def test_save_schedule_photo(
    mock_answer, mock_download_file, mock_get_file,
    mock_get_main_menu, mock_makedirs
):
    mock_get_main_menu.return_value = "markup"
    mock_get_file.return_value.file_path = "fake/path.jpg"

    photo_mock = MagicMock(spec=PhotoSize)
    photo_mock.file_id = "123"
    message = Message(
        message_id=1,
        date=None,
        chat=None,
        from_user=None,
        text=None,
        photo=[photo_mock],
        document=None
    )
    message.photo[-1].file_id = "123"
    message.bot = AsyncMock()

    state = AsyncMock()
    await save_schedule(message, state)

    mock_download_file.assert_awaited_once()
    mock_answer.assert_any_call(
        pytest.helpers.matcher_contains("✅ Расписание успешно обновлено!"),
        reply_markup="markup"
    )
    state.clear.assert_awaited()


@pytest.mark.asyncio
@patch("os.path.exists", return_value=True)
@patch("os.listdir", return_value=["schedule_1.png"])
@patch("os.path.getmtime", return_value=1000)
@patch("app.handlers.schedule.FSInputFile")
@patch("aiogram.types.Message.answer_photo", new_callable=AsyncMock)
@patch("aiogram.types.CallbackQuery.answer", new_callable=AsyncMock)
async def test_view_schedule_photo(
    mock_answer_cb, mock_answer_photo,
    mock_fsinputfile, mock_getmtime,
    mock_listdir, mock_exists
):
    message = MagicMock(spec=Message)
    callback = MagicMock(spec=CallbackQuery)
    callback.message = message

    await view_schedule(callback)

    mock_answer_photo.assert_awaited()
    mock_fsinputfile.assert_called_once()
    mock_answer_cb.assert_awaited()