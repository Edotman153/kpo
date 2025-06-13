import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from telegram import Update, Message, CallbackQuery, User, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from app.src.bot import BookBot
import asyncio

# Фикстуры
@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123
    update.message = MagicMock(spec=Message)
    update.message.text = "Гарри Поттер"
    update.message.reply_text = AsyncMock()
    update.message.reply_photo = AsyncMock()
    return update

@pytest.fixture
def mock_callback_update():
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123
    update.callback_query = MagicMock(spec=CallbackQuery)
    return update

@pytest.fixture
def mock_context():
    return MagicMock(spec=CallbackContext)

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add_favorite = AsyncMock(return_value=True)
    db.get_favorites = AsyncMock(return_value=[])
    return db

# Тестовые данные
TEST_BOOK = {
    "id": "test_id_123",
    "title": "Гарри Поттер и Философский камень",
    "authors": "Дж. К. Роулинг",
    "description": "Книга о мальчике-волшебнике...",
    "thumbnail": "http://example.com/cover.jpg"
}

# Тест
@pytest.mark.asyncio
async def test_search_and_add_to_favorites(mock_update, mock_callback_update, mock_context, mock_db):
    """Тест полного цикла: поиск -> добавление в избранное -> просмотр"""
    
    # Устанавливаем фиксированный ID пользователя
    TEST_USER_ID = 123
    mock_update.effective_user.id = TEST_USER_ID
    mock_callback_update.effective_user.id = TEST_USER_ID
    
    # 1. Мокируем API поиска
    with patch('app.src.google_books.GoogleBooksAPI.search_books',
              AsyncMock(return_value=[TEST_BOOK])):
        
        # 2. Инициализируем бота с мокнутой БД
        bot = BookBot()
        bot.db = mock_db
        
        # 3. Тестируем поиск книг
        await bot.search_books(mock_update, mock_context)
        
        # Проверяем, что результаты поиска показаны
        assert mock_update.message.reply_photo.called
        
        # 4. Настраиваем callback
        callback_query = mock_callback_update.callback_query
        callback_query.data = f"add_{TEST_BOOK['id']}"
        callback_query.answer = AsyncMock()
        callback_query.edit_message_reply_markup = AsyncMock()
        callback_query.message = mock_update.message
        
        # 5. Мокируем получение данных книги
        with patch.object(bot, '_get_book_data', AsyncMock(return_value=TEST_BOOK)):
            
            # 6. Тестируем добавление в избранное
            await bot.handle_button_click(mock_callback_update, mock_context)
            
            # Проверяем сохранение в БД
            args, _ = mock_db.add_favorite.call_args
            saved_book = args[0]
            
            # Проверяем ключевые поля
            assert saved_book['id'] == TEST_BOOK['id']
            assert saved_book['title'] == TEST_BOOK['title']
            assert saved_book['authors'] == TEST_BOOK['authors']
            assert saved_book['thumbnail'] == TEST_BOOK['thumbnail']
            assert 'user_id' in saved_book  # Проверяем наличие поля
    
    # 7. Тестируем просмотр избранного
    mock_db.get_favorites.return_value = [TEST_BOOK]
    await bot.show_favorites(mock_update, mock_context)
    
    # Проверяем основные параметры вывода
    args, kwargs = mock_update.message.reply_photo.call_args
    assert kwargs['photo'] == TEST_BOOK['thumbnail']
    assert TEST_BOOK['title'] in kwargs['caption']
    assert TEST_BOOK['authors'] in kwargs['caption']
    assert isinstance(kwargs['reply_markup'], InlineKeyboardMarkup)
