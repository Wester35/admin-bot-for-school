# tests/test_news.py
import pytest
from unittest.mock import AsyncMock, patch
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User
from app.handlers import news as news_handler

@pytest.mark.asyncio
@patch("app.handlers.news.upload_news_to_api", new_callable=AsyncMock)
@patch("aiogram.types.Message.answer", new_callable=AsyncMock)
@patch("aiogram.types.Message.bot")
async def test_send_news_without_photos(mock_bot, mock_answer, mock_upload_news):
    # Настройка мока
    mock_upload_news.return_value = (200, "OK")

    # Имитируем message от Telegram
    message = Message(
        message_id=1,
        date=None,
        chat=None,
        from_user=User(id=123, is_bot=False, first_name="Test"),
        sender_chat=None,
        text="готово"
    )
    message.bot = mock_bot

    # Мокаем FSM-состояние
    state = AsyncMock(spec=FSMContext)
    state.get_data.return_value = {
        "title": "Test Title",
        "content": "Test Content",
        "photos": []
    }

    await news_handler.finish_news_creation(message, state)

    mock_upload_news.assert_called_once()
    mock_answer.assert_called_with("✅ Новость успешно отправлена!", reply_markup=...)
