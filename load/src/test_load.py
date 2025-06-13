import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from telegram import Update, Message, CallbackQuery, User, Chat, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from app.src.bot import BookBot
import os

# Фикстуры для тестов
@pytest.fixture
def mock_engine():
    return MagicMock()

@pytest.fixture
def mock_session(mock_engine):
    return MagicMock()

@pytest.fixture
def bot(mock_engine, mock_session):
    with patch.dict('os.environ', {"TELEGRAM_TOKEN": "test_token", "DB_URL": "sqlite:///:memory:"}):
        return BookBot(engine=mock_engine, session=mock_session)

@pytest.fixture
def mock_context():
    context = MagicMock(spec=CallbackContext)
    context.bot = MagicMock()
    return context

@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123
    update.effective_user.first_name = "Test"
    update.effective_user.is_bot = False
    
    # Мокаем message отдельно, так как он будет переопределяться
    update.message = None
    
    # Мокаем callback_query
    update.callback_query = MagicMock(spec=CallbackQuery)
    update.callback_query.id = 1
    update.callback_query.from_user = update.effective_user
    update.callback_query.chat_instance = "test_chat_instance"
    update.callback_query.data = "add_test1"
    update.callback_query.message = MagicMock(spec=Message)
    update.callback_query.message.chat = MagicMock(spec=Chat)
    update.callback_query.message.chat.id = 123
    update.callback_query.message._bot = MagicMock()  # Важно для работы reply_text
    
    return update

@pytest.fixture
def mock_context():
    context = MagicMock(spec=CallbackContext)
    context.bot = MagicMock()
    return context

@pytest.mark.asyncio
async def test_multiple_search_requests(bot, mock_update, mock_context):
    """Тестирование обработки множественных одновременных поисковых запросов"""
    # Мокируем API
    bot.google_api.search_books = AsyncMock(return_value=[{
        "id": "test1",
        "title": "Test Book",
        "authors": "Test Author",
        "description": "Test Description",
        "thumbnail": None
    }])
    
    bot.open_lib_api.search_books = AsyncMock(return_value=[])
    
    # Мокируем методы бота
    mock_bot = MagicMock()
    mock_context.bot = mock_bot
    
    # Создаем мок для сообщения с установленным ботом
    def create_mock_message(text):
        message = MagicMock(spec=Message)
        message.text = text
        message.chat = MagicMock()
        message.chat.id = 123
        message.reply_text = AsyncMock()
        message.reply_photo = AsyncMock()
        message._bot = mock_bot  # Устанавливаем бота для сообщения
        return message
    
    # Создаем 10 одновременных запросов
    tasks = []
    for i in range(10):
        mock_update.message = create_mock_message(f"Test Query {i}")
        task = asyncio.create_task(bot.search_books(mock_update, mock_context))
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    
    # Проверяем, что все запросы были обработаны
    assert bot.google_api.search_books.await_count == 10
    
    # Проверяем, что для каждого запроса был вызван reply_text (так как thumbnail=None)
    assert mock_update.message.reply_text.await_count == 10
    
    # Проверяем, что reply_photo не вызывался
    assert mock_update.message.reply_photo.await_count == 0
    
    # Проверяем содержимое ответов
    for call in mock_update.message.reply_text.call_args_list:
        args, kwargs = call
        assert "Test Book" in args[0]  # Проверяем, что в ответе есть название книги
        assert kwargs.get("parse_mode") == "HTML"
        assert isinstance(kwargs.get("reply_markup"), InlineKeyboardMarkup)
