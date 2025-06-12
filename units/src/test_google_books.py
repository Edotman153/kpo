import pytest
from ...app.src.google_books import GoogleBooksAPI
from unittest.mock import patch

class TestGoogleBooksAPI:
    @patch("requests.get")  # Мокаем запросы к API
    def test_search_books_success(self, mock_get):
        # Подготовка мок-ответа
        mock_response = {
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
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        # Вызов тестируемого метода
        api = GoogleBooksAPI()
        books = api.search_books("Test")

        # Проверки
        assert len(books) == 1
        assert books[0]["title"] == "Test Book"
        assert books[0]["authors"] == "Author 1"

    def test_search_books_empty(self):
        api = GoogleBooksAPI()
        books = api.search_books("")  # Пустой запрос
        assert books == []
