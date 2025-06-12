import pytest
from unittest.mock import patch, MagicMock
from app.src.open_lib import OpenLibraryAPI
import json
import requests

@pytest.fixture
def mock_book_data():
    return {
        "title": "Test Book",
        "author_name": ["Test Author"],
        "cover_i": 123456,
        "key": "/works/OL123W"
    }

@pytest.fixture
def mock_book_details():
    return {
        "description": "Test description",
        "title": "Test Book"
    }

@pytest.mark.asyncio
class TestOpenLibraryAPI:
    @patch('app.src.open_lib.requests.Session')
    async def test_search_books_success(self, mock_session, mock_book_data, mock_book_details):
        # Setup mock responses
        mock_search_response = MagicMock()
        mock_search_response.json.return_value = {
            "docs": [mock_book_data]
        }
        mock_search_response.raise_for_status.return_value = None

        mock_details_response = MagicMock()
        mock_details_response.json.return_value = mock_book_details
        mock_details_response.raise_for_status.return_value = None

        # Configure mock session
        mock_session_instance = MagicMock()
        mock_session_instance.get.side_effect = [
            mock_search_response,  # First call for search
            mock_details_response  # Second call for details
        ]
        mock_session.return_value = mock_session_instance

        # Test the method
        api = OpenLibraryAPI()
        books = await api.search_books("Test")

        # Assertions
        assert len(books) == 1
        assert books[0]["title"] == "Test Book"
        assert books[0]["authors"] == "Test Author"
        assert books[0]["description"] == "Test description"
        assert books[0]["thumbnail"] == "https://covers.openlibrary.org/b/id/123456-M.jpg"
        assert books[0]["id"] == "OL123W"

    @patch('app.src.open_lib.requests.Session')
    async def test_search_books_empty_result(self, mock_session):
        # Setup empty response
        mock_response = MagicMock()
        mock_response.json.return_value = {"docs": []}
        mock_response.raise_for_status.return_value = None

        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        # Test the method
        api = OpenLibraryAPI()
        books = await api.search_books("Unknown")

        # Assertions
        assert books == []

    @patch('app.src.open_lib.requests.Session')
    async def test_search_books_error_handling(self, mock_session):
        # Setup error response
        mock_session_instance = MagicMock()
        mock_session_instance.get.side_effect = requests.exceptions.RequestException("API Error")
        mock_session.return_value = mock_session_instance

        # Test the method
        api = OpenLibraryAPI()
        books = await api.search_books("Error Test")

        # Assertions
        assert books == []

    def test_parse_results(self, mock_book_data):
        api = OpenLibraryAPI()
        
        test_data = {
            "docs": [mock_book_data]
        }
        
        books = api._parse_results(test_data)
        
        assert len(books) == 1
        assert books[0]["title"] == "Test Book"
        assert books[0]["authors"] == "Test Author"

    def test_get_cover_url(self):
        api = OpenLibraryAPI()
        
        # Test with cover ID
        assert api._get_cover_url(123) == "https://covers.openlibrary.org/b/id/123-M.jpg"
        
        # Test without cover ID
        assert api._get_cover_url(None) is None

    def test_clean_description(self):
        api = OpenLibraryAPI()
        
        # Test with string description
        assert api._clean_description("Simple description") == "Simple description"
        
        # Test with dict description
        assert api._clean_description({"value": "Dict description"}) == "Dict description"
        
        # Test with invalid description
        assert api._clean_description(None) == "None"
