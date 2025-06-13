import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from telegram import Update, Message, CallbackQuery, User, Chat, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from app.src.bot import BookBot
import os

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
    
    update.message = None
    
    update.callback_query = MagicMock(spec=CallbackQuery)
    update.callback_query.id = 1
    update.callback_query.from_user = update.effective_user
    update.callback_query.chat_instance = "test_chat_instance"
    update.callback_query.data = "add_test1"
    update.callback_query.message = MagicMock(spec=Message)
    update.callback_query.message.chat = MagicMock(spec=Chat)
    update.callback_query.message.chat.id = 123
    update.callback_query.message._bot = MagicMock()
    
    return update

@pytest.fixture
def mock_context():
    context = MagicMock(spec=CallbackContext)
    context.bot = MagicMock()
    return context

@pytest.mark.asyncio
async def test_multiple_search_requests(bot, mock_update, mock_context):
    """Тестирование обработки множественных одновременных поисковых запросов"""
    bot.google_api.search_books = AsyncMock(return_value=[{
        "id": "test1",
        "title": "Test Book",
        "authors": "Test Author",
        "description": "Test Description",
        "thumbnail": None
    }])
    
    bot.open_lib_api.search_books = AsyncMock(return_value=[])
    
    mock_bot = MagicMock()
    mock_context.bot = mock_bot
    
    def create_mock_message(text):
        message = MagicMock(spec=Message)
        message.text = text
        message.chat = MagicMock()
        message.chat.id = 123
        message.reply_text = AsyncMock()
        message.reply_photo = AsyncMock()
        message._bot = mock_bot
        return message
    
    tasks = []
    num = 1000
    for i in range(num):
        mock_update.message = create_mock_message(f"Test Query {i}")
        task = asyncio.create_task(bot.search_books(mock_update, mock_context))
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    
    assert bot.google_api.search_books.await_count == num
    
    assert mock_update.message.reply_text.await_count == num
    
    assert mock_update.message.reply_photo.await_count == 0
    
    for call in mock_update.message.reply_text.call_args_list:
        args, kwargs = call
        assert "Test Book" in args[0]  # Проверяем, что в ответе есть название книги
        assert kwargs.get("parse_mode") == "HTML"
        assert isinstance(kwargs.get("reply_markup"), InlineKeyboardMarkup)

@pytest.mark.asyncio
async def test_high_load_favorites(bot, mock_update, mock_context):
    """Тестирование загрузки избранного при большом количестве книг"""
    # Создаем мок для 100 книг в избранном
    num = 1000
    mock_favorites = [{
        "id": f"test{i}",
        "title": f"Test Book {i}",
        "authors": f"Test Author {i}",
        "description": f"Test Description {i}",
        "thumbnail": None if i % 2 else f"http://example.com/cover_{i}.jpg"
    } for i in range(num)]
    
    bot.db.get_favorites = AsyncMock(return_value=mock_favorites)
    
    # Мокаем методы сообщения
    mock_update.message = MagicMock(spec=Message)
    mock_update.message.chat = MagicMock(spec=Chat)
    mock_update.message.chat.id = 123
    mock_update.message.reply_text = AsyncMock()
    mock_update.message.reply_photo = AsyncMock()
    mock_update.message._bot = mock_context.bot
    
    # Вызываем показ избранного
    await bot.show_favorites(mock_update, mock_context)
    
    # Проверяем, что все книги были обработаны
    assert bot.db.get_favorites.await_count == 1
    assert mock_update.message.reply_text.await_count == num / 2  # Для книг без thumbnail
    assert mock_update.message.reply_photo.await_count == num / 2  # Для книг с thumbnail

@pytest.mark.asyncio
async def test_error_handling_under_load(bot, mock_update, mock_context):
    """Тестирование обработки ошибок при нагрузке"""
    # Мокируем ошибку API
    bot.google_api.search_books = AsyncMock(side_effect=Exception("API Error"))
    bot.open_lib_api.search_books = AsyncMock(side_effect=Exception("API Error"))
    
    # Мокаем методы сообщения
    mock_update.message = MagicMock(spec=Message)
    mock_update.message.chat = MagicMock(spec=Chat)
    mock_update.message.chat.id = 123
    mock_update.message.reply_text = AsyncMock()
    mock_update.message._bot = mock_context.bot

    num = 1000
    tasks = []
    for i in range(num):
        mock_update.message.text = f"Failing Query {i}"
        task = asyncio.create_task(bot.search_books(mock_update, mock_context))
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    
    # Проверяем, что все запросы вернули сообщение об ошибке
    assert mock_update.message.reply_text.await_count == num
    for call in mock_update.message.reply_text.call_args_list:
        assert "ошибка" in call[0][0].lower() or "error" in call[0][0].lower()
