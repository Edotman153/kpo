import os
import requests
from dotenv import load_dotenv

load_dotenv()

class GoogleBooksAPI:
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_BOOKS_API_KEY")
    
    def search_books(self, query, max_results=5):
        params = {
            "q": query,
            "key": self.api_key,
            "maxResults": max_results,
            "langRestrict": "ru"  # Ограничение на русские книги (опционально)
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return self._parse_results(response.json())
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return []

    def _parse_results(self, data):
        books = []
        for item in data.get("items", []):
            volume = item.get("volumeInfo", {})
            books.append({
                "id": item.get("id"),
                "title": volume.get("title"),
                "authors": ", ".join(volume.get("authors", ["Неизвестен"])),
                "description": volume.get("description", "Нет описания"),
                "thumbnail": volume.get("imageLinks", {}).get("thumbnail")
            })
        return books

# Пример использования
if __name__ == "__main__":
    api = GoogleBooksAPI()
    books = api.search_books("Гарри Поттер")
    for book in books:
        print(f"{book['title']} by {book['authors']}")
