from sqlalchemy import create_engine, Column, String, Integer, Text, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()
Base = declarative_base()

class Book(Base):
    __tablename__ = "favorite_book"
    id = Column(String, primary_key=True)  # ID из Google Books
    title = Column(String)
    authors = Column(String)
    description = Column(Text)
    thumbnail_url = Column(String)
    user_id = Column(BigInteger)

class Database:
    def __init__(self):
        self.engine = create_engine(os.getenv("DB_URL"))
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
    
    def save_book(self, book_data):
        session = self.Session()
        book = Book(
            id=book_data["id"],
            title=book_data["title"],
            authors=book_data["authors"],
            description=book_data["description"],
            thumbnail_url=book_data.get("thumbnail"),
            user_id=book_data["user_id"]
        )
        session.merge(book)
        session.commit()
        session.close()

    def get_books(self, user_id):
        """
        Возвращает список книг для указанного пользователя
        
        Args:
            user_id (int): ID пользователя Telegram
            
        Returns:
            list: Список словарей с информацией о книгах
                  [{"id": "...", "title": "...", ...}, ...]
        """
        session = self.Session()
        try:
            books = session.query(Book).filter_by(user_id=user_id).all()
            return [{
                "id": book.id,
                "title": book.title,
                "authors": book.authors,
                "description": book.description,
                "thumbnail": book.thumbnail_url,
                "user_id": book.user_id
            } for book in books]
        finally:
            session.close()

# Пример использования
if __name__ == "__main__":
    db = Database()
    
    # Тестовые данные
    test_books = [
        {
            "id": "book1",
            "title": "Тестовая книга 1",
            "authors": "Автор 1",
            "description": "Описание 1",
            "thumbnail": "http://example.com/cover1.jpg",
            "user_id": 12345
        },
        {
            "id": "book2",
            "title": "Тестовая книга 2",
            "authors": "Автор 2",
            "description": "Описание 2",
            "thumbnail": None,
            "user_id": 12345
        }
    ]
    
    # Сохраняем книги
    for book in test_books:
        db.save_book(book)
    
    # Получаем книги пользователя
    user_books = db.get_books(12345)
    print("Найденные книги:")
    for book in user_books:
        print(f"{book['title']} by {book['authors']}")
