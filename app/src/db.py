from sqlalchemy import create_engine, Column, String, Text, BigInteger
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()
Base = declarative_base()

class FavoriteBook(Base):
    __tablename__ = "favorite_books"
    id = Column(String, primary_key=True)  # ID книги из API
    title = Column(String)
    authors = Column(String)
    description = Column(Text)
    thumbnail_url = Column(String)
    user_id = Column(BigInteger)  # ID пользователя Telegram

class Database:
    def __init__(self):
        self.engine = create_engine(os.getenv("DB_URL"))
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    async def add_favorite(self, book_data: dict):
        """Добавляет книгу в избранное"""
        session = self.Session()
        try:
            book = FavoriteBook(
                id=book_data["id"],
                title=book_data["title"],
                authors=book_data["authors"],
                description=book_data.get("description", ""),
                thumbnail_url=book_data.get("thumbnail"),
                user_id=book_data["user_id"]
            )
            session.merge(book)  # Используем merge вместо add для избежания дубликатов
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    async def get_favorites(self, user_id: int):
        """Получает все избранные книги пользователя"""
        session = self.Session()
        try:
            books = session.query(FavoriteBook).filter_by(user_id=user_id).all()
            return [{
                "id": book.id,
                "title": book.title,
                "authors": book.authors,
                "description": book.description,
                "thumbnail": book.thumbnail_url
            } for book in books]
        finally:
            session.close()

    async def remove_favorite(self, user_id: int, book_id: str):
        """Удаляет книгу из избранного"""
        session = self.Session()
        try:
            book = session.query(FavoriteBook).filter_by(id=book_id, user_id=user_id).first()
            if book:
                session.delete(book)
                session.commit()
                return True
            return False
        finally:
            session.close()
