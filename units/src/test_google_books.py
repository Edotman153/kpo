import pytest
from unittest.mock import patch, MagicMock
from app.src.google_books import GoogleBooksAPI
import asyncio
import requests

@pytest.mark.asyncio
class TestGoogleBooksAPI:
    @patch('app.src.google_books.requests.get')
    async def test_search_books_success(self, mock_get):
        # Настраиваем мок для requests.get
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {
                    "id": "test123",
                    "volumeInfo": {
                        "title": "Test Book",
                        "authors": ["Author 1"],
                        "description": "Test description",
                        "imageLinks": {"thumbnail": "http://test.com/cover.jpg"}
                    }
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Вызываем асинхронный метод
        api = GoogleBooksAPI()
        books = await api.search_books("Test")

        # Проверяем результаты
        assert len(books) == 1
        assert books[0]["title"] == "Test Book"
        assert books[0]["authors"] == "Author 1"
        assert books[0]["description"] == "Test description"
        assert books[0]["thumbnail"] == "http://test.com/cover.jpg"

    @patch('app.src.google_books.requests.get')
    async def test_search_books_empty_response(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        api = GoogleBooksAPI()
        books = await api.search_books("Unknown")

        assert books == []

    @patch('app.src.google_books.requests.get')
    async def test_search_books_error_handling(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        api = GoogleBooksAPI()
        books = await api.search_books("Error Test")

        assert books == []
