import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, CallbackQuery, Chat, User, PhotoSize
from telegram.ext import CallbackContext
from ...app.src.bot import BookBot
import asyncio
pytestmark = pytest.mark.asyncio
@pytest.fixture
def bot():
    with patch('app.src.google_books.GoogleBooksAPI'), patch('app.src.open_lib.OpenLibraryAPI'), patch('app.src.db.Database'):
        return BookBot()

@pytest.fixture
def update():
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123
    update.message = MagicMock(spec=Message)
    update.message.text = "test"
    update.message.reply_text = AsyncMock()
    update.message.reply_photo = AsyncMock()
    return update

@pytest.fixture
def context():
    return MagicMock(spec=CallbackContext)

@pytest.fixture
def callback_query():
    query = MagicMock(spec=CallbackQuery)
    query.from_user.id = 123
    query.data = "add_test_id"
    query.answer = AsyncMock()
    query.edit_message_reply_markup = AsyncMock()
    query.message = MagicMock()
    query.message.delete = AsyncMock()
    return query

@pytest.mark.asyncio
async def test_start(bot, update, context):
    await bot.start(update, context)
    update.message.reply_text.assert_called_once()

@pytest.mark.asyncio
async def test_help(bot, update, context):
    await bot.help(update, context)
    update.message.reply_text.assert_called_once()

@pytest.mark.asyncio
async def test_search_books_no_query(bot, update, context):
    update.message.text = ""
    await bot.search_books(update, context)
    update.message.reply_text.assert_called_with("Пожалуйста, введите название книги")

@pytest.mark.asyncio
async def test_search_books_no_results(bot, update, context):
    bot.google_api.search_books = AsyncMock(return_value=[])
    bot.open_lib_api.search_books = AsyncMock(return_value=[])
    
    await bot.search_books(update, context)
    update.message.reply_text.assert_called_with("Книги не найдены 😢\nПопробуйте другой запрос")

@pytest.mark.asyncio
async def test_search_books_with_google_results(bot, update, context):
    test_book = {
        "title": "Test Book",
        "authors": "Test Author",
        "description": "Test Description",
        "id": "test_id",
        "thumbnail": "http://test.com/image.jpg"
    }
    bot.google_api.search_books = AsyncMock(return_value=[test_book])
    
    await bot.search_books(update, context)
    update.message.reply_photo.assert_called_once()

@pytest.mark.asyncio
async def test_search_books_with_openlib_results(bot, update, context):
    test_book = {
        "title": "Test Book",
        "authors": "Test Author",
        "description": "Test Description",
        "id": "test_id"
    }
    bot.google_api.search_books = AsyncMock(return_value=[])
    bot.open_lib_api.search_books = AsyncMock(return_value=[test_book])
    
    await bot.search_books(update, context)
    update.message.reply_text.assert_called_once()

@pytest.mark.asyncio
async def test_show_favorites_empty(bot, update, context):
    bot.db.get_favorites = AsyncMock(return_value=[])
    await bot.show_favorites(update, context)
    update.message.reply_text.assert_called_with("У вас пока нет избранных книг")

@pytest.mark.asyncio
async def test_show_favorites_with_books(bot, update, context):
    test_book = {
        "title": "Test Book",
        "authors": "Test Author",
        "description": "Test Description",
        "id": "test_id",
        "thumbnail": "http://test.com/image.jpg"
    }
    bot.db.get_favorites = AsyncMock(return_value=[test_book])
    await bot.show_favorites(update, context)
    update.message.reply_photo.assert_called_once()

@pytest.mark.asyncio
async def test_handle_button_click_add(bot, callback_query, context):
    update = MagicMock(spec=Update)
    update.callback_query = callback_query
    bot._get_book_data = AsyncMock(return_value={"id": "test_id", "title": "Test", "authors": "Author"})
    bot.db.add_favorite = AsyncMock()
    
    await bot.handle_button_click(update, context)
    callback_query.answer.assert_called_once()
    callback_query.edit_message_reply_markup.assert_called_once()

@pytest.mark.asyncio
async def test_handle_button_click_remove(bot, callback_query, context):
    callback_query.data = "remove_test_id"
    update = MagicMock(spec=Update)
    update.callback_query = callback_query
    bot.db.remove_favorite = AsyncMock(return_value=True)
    
    await bot.handle_button_click(update, context)
    callback_query.message.delete.assert_called_once()

@pytest.mark.asyncio
async def test_handle_button_click_remove_not_found(bot, callback_query, context):
    callback_query.data = "remove_test_id"
    update = MagicMock(spec=Update)
    update.callback_query = callback_query
    bot.db.remove_favorite = AsyncMock(return_value=False)
    
    await bot.handle_button_click(update, context)
    callback_query.answer.assert_called_with("Книга не найдена в избранном", show_alert=True)

@pytest.mark.asyncio
async def test_handle_button_click_invalid_data(bot, callback_query, context):
    callback_query.data = "invalid_data"
    update = MagicMock(spec=Update)
    update.callback_query = callback_query
    
    await bot.handle_button_click(update, context)
    callback_query.answer.assert_called_once()

@pytest.mark.asyncio
async def test_get_book_data_google(bot):
    test_data = {
        "items": [{
            "id": "test_id",
            "volumeInfo": {
                "title": "Test Book",
                "authors": ["Test Author"],
                "description": "Test Description",
                "imageLinks": {"thumbnail": "http://test.com/image.jpg"}
            }
        }]
    }
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = test_data
        mock_get.return_value.raise_for_status.return_value = None
        
        result = await bot._get_book_data("test_id")
        assert result["title"] == "Test Book"
        assert result["id"] == "test_id"

@pytest.mark.asyncio
async def test_get_book_data_openlib(bot):
    # Тестовые данные
    book_id = "OL123"
    work_data = {
        "title": "Test Book",
        "description": {"value": "Test Description"},
        "covers": [123],
        "authors": [{"author": {"key": "/authors/OL123A"}}]
    }
    author_data = {"name": "Test Author"}

    # Мокируем session.get для OpenLibraryAPI
    mock_session = MagicMock()
    
    # Первый вызов - получение данных книги
    mock_book_response = MagicMock()
    mock_book_response.json.return_value = work_data
    mock_book_response.raise_for_status.return_value = None
    
    # Второй вызов - получение данных автора
    mock_author_response = MagicMock()
    mock_author_response.json.return_value = author_data
    mock_author_response.raise_for_status.return_value = None
    
    # Настраиваем side_effect для последовательных вызовов
    mock_session.get.side_effect = [
        MagicMock(__enter__=MagicMock(return_value=mock_book_response)),
        MagicMock(__enter__=MagicMock(return_value=mock_author_response))
    ]
    
    # Подменяем session в open_lib_api
    with patch.object(bot.open_lib_api, 'session', mock_session):
        result = await bot._get_book_data(book_id)
        
        # Проверяем результат
        assert result["title"] == "Test Book"
        assert result["authors"] == "Test Author"
        assert result["description"] == "Test Description"
        assert result["thumbnail"] == "https://covers.openlibrary.org/b/id/123-M.jpg"
        
        # Проверяем вызовы API
        assert mock_session.get.call_count == 2
        mock_session.get.assert_any_call(f"{bot.open_lib_api.BASE_URL}/works/{book_id}.json")
        mock_session.get.assert_any_call(f"{bot.open_lib_api.BASE_URL}/authors/OL123A.json")
