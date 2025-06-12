import pytest
from unittest.mock import MagicMock, patch
from app.src.db import Database, FavoriteBook, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import asyncio

@pytest.fixture
def test_db():
    # Используем SQLite в памяти для тестов
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    
    db = Database()
    db.engine = engine  # Переопределяем engine на тестовый
    db.Session = Session
    
    yield db
    
    # Очистка после тестов
    Base.metadata.drop_all(engine)

@pytest.fixture
def sample_book():
    return {
        "id": "test123",
        "title": "Test Book",
        "authors": "Test Author",
        "description": "Test Description",
        "thumbnail": "http://test.com/cover.jpg",
        "user_id": 12345
    }

@pytest.mark.asyncio
class TestDatabase:
    async def test_add_favorite_success(self, test_db, sample_book):
        # Добавляем книгу
        result = await test_db.add_favorite(sample_book)
        assert result is True
        
        # Проверяем, что книга добавилась
        session = test_db.Session()
        book = session.query(FavoriteBook).first()
        assert book is not None
        assert book.id == "test123"
        assert book.title == "Test Book"
        session.close()

    async def test_add_favorite_duplicate(self, test_db, sample_book):
        # Первое добавление
        await test_db.add_favorite(sample_book)
        
        # Пробуем добавить снова (должно сработать merge)
        sample_book["description"] = "Updated Description"
        result = await test_db.add_favorite(sample_book)
        assert result is True
        
        # Проверяем, что запись обновилась
        session = test_db.Session()
        books = session.query(FavoriteBook).all()
        assert len(books) == 1
        assert books[0].description == "Updated Description"
        session.close()

    async def test_get_favorites_empty(self, test_db):
        books = await test_db.get_favorites(12345)
        assert books == []

    async def test_get_favorites_with_data(self, test_db, sample_book):
        # Добавляем две книги
        await test_db.add_favorite(sample_book)
        await test_db.add_favorite({
            **sample_book,
            "id": "test456",
            "title": "Another Book"
        })
        
        # Получаем избранное
        books = await test_db.get_favorites(12345)
        assert len(books) == 2
        assert books[0]["title"] == "Test Book"
        assert books[1]["title"] == "Another Book"

    async def test_get_favorites_filter_by_user(self, test_db, sample_book):
        # Добавляем книги для двух пользователей
        await test_db.add_favorite(sample_book)
        await test_db.add_favorite({
            **sample_book,
            "id": "test456",
            "user_id": 54321
        })
        
        # Проверяем фильтрацию
        books = await test_db.get_favorites(12345)
        assert len(books) == 1
        assert books[0]["id"] == "test123"

    async def test_remove_favorite_success(self, test_db, sample_book):
        # Добавляем книгу
        await test_db.add_favorite(sample_book)
        
        # Удаляем
        result = await test_db.remove_favorite(12345, "test123")
        assert result is True
        
        # Проверяем
        books = await test_db.get_favorites(12345)
        assert books == []

    async def test_remove_favorite_not_found(self, test_db, sample_book):
        # Пробуем удалить несуществующую книгу
        result = await test_db.remove_favorite(12345, "nonexistent")
        assert result is False

    async def test_remove_favorite_wrong_user(self, test_db, sample_book):
        # Добавляем книгу для одного пользователя
        await test_db.add_favorite(sample_book)
        
        # Пробуем удалить от другого пользователя
        result = await test_db.remove_favorite(54321, "test123")
        assert result is False
        
        # Проверяем, что книга осталась
        books = await test_db.get_favorites(12345)
        assert len(books) == 1
