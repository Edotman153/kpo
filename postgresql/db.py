from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

DB_URL = "postgresql://user:pass@localhost:5433/books"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class FavoriteBook(Base):
    __tablename__ = "favorite_books"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    book_id = Column(String)
    title = Column(String)
    author = Column(String)

Base.metadata.create_all(bind=engine)  # Создаёт таблицы
