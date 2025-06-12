import os
import requests
from dotenv import load_dotenv

load_dotenv()

class OpenLibraryAPI:
    BASE_URL = "https://openlibrary.org"
    
    def __init__(self):
        # OpenLibrary не требует API ключа, но можно добавить кастомные настройки
        self.session = requests.Session()
    
    def search_books(self, query, max_results=5):
        params = {
            "q": query,
            "limit": max_results,
            "language": "rus"  # Фильтр по русским книгам
        }
        
        try:
            response = self.session.get(
                f"{self.BASE_URL}/search.json",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return self._parse_results(response.json())
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return []

    def _parse_results(self, data):
        books = []
        for doc in data.get("docs", []):
            # Получаем полные данные о книге (включая описание)
            book_data = self._get_book_details(doc.get("key")) if doc.get("key") else {}
            
            books.append({
                "id": doc.get("key", "").split("/")[-1],  # Извлекаем ID из ключа
                "title": doc.get("title", "Без названия"),
                "authors": ", ".join(doc.get("author_name", ["Неизвестен"])[:200]),
                "description": book_data.get("description", "Нет описания"),
                "thumbnail": self._get_cover_url(doc.get("cover_i"))
            })
        return books

    def _get_book_details(self, book_key):
        """Получает детализированную информацию о книге"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}{book_key}.json",
                timeout=5
            )
            return response.json()
        except:
            return {}

    def _get_cover_url(self, cover_id):
        """Генерирует URL обложки"""
        if not cover_id:
            return None
        return f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"

    def _clean_description(self, desc):
        """Очищает описание от HTML/спецсимволов"""
        if isinstance(desc, dict):
            return desc.get("value", "Нет описания")
        return str(desc)[:500]  # Обрезаем слишком длинные описания

# Пример использования (аналогично GoogleBooksAPI)
if __name__ == "__main__":
    api = OpenLibraryAPI()
    books = api.search_books("Гарри Поттер")
    for book in books:
        print(f"{book['title']} by {book['authors']}")
        print(f"Cover: {book['thumbnail']}")
        print("---")
