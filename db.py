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
        session.merge(book)  # Обновит существующую или добавит новую
        session.commit()
        session.close()

# Пример использования
if __name__ == "__main__":
    db = Database()
    test_book = {
        "id": "test123",
        "title": "Тестовая книга",
        "authors": "Автор Тест",
        "description": "Это тестовое описание",
        "user_id": 864730973
    }
    db.save_book(test_book)
