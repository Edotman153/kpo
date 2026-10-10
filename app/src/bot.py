import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import html
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from app.src.google_books import GoogleBooksAPI
from app.src.open_lib import OpenLibraryAPI
from app.src.db import Database
from dotenv import load_dotenv
import logging
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


load_dotenv()

class BookBot:
    def __init__(self, engine=None, session=None):
        self.google_api = GoogleBooksAPI()
        self.open_lib_api = OpenLibraryAPI()
        if not engine:
            self.engine = create_engine(os.getenv("DB_URL"))
        else:
            self.engine = engine
        if not session:
            self.session = sessionmaker(bind=self.engine)
        else:
            self.session = session
        self.db = Database(self.engine, self.session)
        self.application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
        
        self.reply_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton("ℹ Помощь")],
                [KeyboardButton("⭐ Избранное")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Введите название книги"
        )
        
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(MessageHandler(filters.Regex(r'^ℹ Помощь$'), self.help))
        self.application.add_handler(MessageHandler(filters.Regex(r'^⭐ Избранное$'), self.show_favorites))
        self.application.add_handler(MessageHandler(filters.TEXT, self.search_books))
        self.application.add_handler(CallbackQueryHandler(self.handle_button_click))

    @staticmethod
    def _format_book(icon, book):
        """Текст карточки книги для Telegram (parse_mode=HTML, поэтому всё экранируем)"""
        description = str(book.get("description") or "Описание отсутствует")
        short = description[:500] + ("..." if len(description) > 500 else "")
        title = html.escape(str(book.get("title") or "Без названия"))
        authors = html.escape(str(book.get("authors") or "Неизвестен"))
        return f"{icon} <b>{title}</b>\n👤 {authors}\n\n{html.escape(short)}"

    async def start(self, update, context):
        await update.message.reply_text(
            "📚 Добро пожаловать в книжный бот!\n\n"
            "Просто введите название книги для поиска",
            reply_markup=self.reply_keyboard
        )

    async def help(self, update, context):
        await update.message.reply_text(
            "Вы можете:\n"
            "- Искать книги, просто введя название\n"
            "- Добавлять книги в избранное кнопкой под книгой\n"
            "- Просматривать избранное через меню\n"
            "- Удалять книги из избранного",
            reply_markup=self.reply_keyboard
        )

    async def search_books(self, update, context):
        query = update.message.text
        if not query:
            await update.message.reply_text("Пожалуйста, введите название книги")
            return
        
        try:
            books = await self.google_api.search_books(query)
            if not books:
                books = await self.open_lib_api.search_books(query)
                if not books:
                    await update.message.reply_text("Книги не найдены 😢\nПопробуйте другой запрос")
                    return
            
            for book in books:
                book["user_id"] = update.effective_user.id
                
                msg = self._format_book("📖", book)
                
                keyboard = [[
                    InlineKeyboardButton("⭐ Добавить в избранное", callback_data=f"add_{book['id']}")
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if book.get("thumbnail"):
                    await update.message.reply_photo(
                        photo=book["thumbnail"],
                        caption=msg,
                        parse_mode="HTML",
                        reply_markup=reply_markup
                    )
                else:
                    await update.message.reply_text(
                        msg,
                        parse_mode="HTML",
                        reply_markup=reply_markup
                    )
                    
        except Exception as e:
            logging.error(f"Ошибка поиска: {e}")
            await update.message.reply_text("Произошла ошибка при поиске")

    async def show_favorites(self, update, context):
        try:
            favorites = await self.db.get_favorites(update.effective_user.id)
            if not favorites:
                await update.message.reply_text("У вас пока нет избранных книг")
                return
            
            for book in favorites:
                msg = self._format_book("⭐", book)
                
                keyboard = [[
                    InlineKeyboardButton("❌ Удалить из избранного", callback_data=f"remove_{book['id']}")
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if book.get("thumbnail"):
                    await update.message.reply_photo(
                        photo=book["thumbnail"],
                        caption=msg,
                        parse_mode="HTML",
                        reply_markup=reply_markup
                    )
                else:
                    await update.message.reply_text(
                        msg,
                        parse_mode="HTML",
                        reply_markup=reply_markup
                    )
                    
        except Exception as e:
            logging.error(f"Ошибка получения избранного: {e}")
            await update.message.reply_text("Ошибка при загрузке избранного")
    async def handle_button_click(self, update, context):
        query = update.callback_query
        await query.answer()
    
        user_id = query.from_user.id
        data = query.data
    
        if data == "none":
            return
        try:
            action, book_id = data.split("_", 1)
        
            if action == "add":
                book_data = await self._get_book_data(book_id)
                if book_data:
                    #print("if")        

                    book_data["user_id"] = user_id
                    await self.db.add_favorite(book_data)
                    await query.edit_message_reply_markup(
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("✅ В избранном", callback_data="none")]
                        ])
                    )
                else:
                    await query.answer("Не удалось найти данные книги", show_alert=True)
                
            elif action == "remove":
                success = await self.db.remove_favorite(user_id, book_id)
                if success:
                    await query.message.delete()
                else:
                    await query.answer("Книга не найдена в избранном", show_alert=True)
                
        except Exception as e:
            logging.error(f"Ошибка: {e}")
    async def _get_book_data(self, book_id):
        """Получает полные данные книги по ID из доступных API"""
        try:
            # Пробуем получить из Google Books API
            if not book_id.startswith('OL'):  # Google Books ID обычно не начинается с OL
                response = requests.get(
                    f"{self.google_api.BASE_URL}/{book_id}",
                    params={"key": os.getenv("GOOGLE_BOOKS_API_KEY")},
                    timeout=10,
                )
                response.raise_for_status()
                item = response.json()
                if item.get('id'):
                    volume = item.get('volumeInfo', {})
                    return {
                        "id": item.get('id'),
                        "title": volume.get('title'),
                        "authors": ", ".join(volume.get('authors', ["Неизвестен"])),
                        "description": volume.get('description', "Нет описания"),
                        "thumbnail": volume.get('imageLinks', {}).get('thumbnail')
                    }
    
            # Если не нашли в Google Books, пробуем Open Library
            if book_id.startswith('OL') or not book_id:  # Open Library ID обычно начинается с OL
                with self.open_lib_api.session.get(
                    f"{self.open_lib_api.BASE_URL}/works/{book_id}.json"
                ) as response:
                    response.raise_for_status()
                    work_data = response.json()
                    description = work_data.get('description')
                    if isinstance(description, dict):
                        description = description.get('value', "Нет описания")
                    
                    # Получаем обложку отдельно
                    cover_id = work_data.get('covers', [None])[0]
                    thumbnail = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None
                    
                    # Получаем авторов
                    authors = []
                    if work_data.get('authors'):
                        for author in work_data['authors']:
                            if isinstance(author, dict) and author.get('author'):
                                author_key = author['author'].get('key')
                                if author_key:
                                    with self.open_lib_api.session.get(
                                        f"{self.open_lib_api.BASE_URL}{author_key}.json"
                                    ) as author_resp:
                                        author_resp.raise_for_status()
                                        author_data = author_resp.json()
                                        authors.append(author_data.get('name', 'Неизвестный автор'))
                    
                    return {
                        "id": book_id,
                        "title": work_data.get('title', 'Без названия'),
                        "authors": ", ".join(authors) if authors else "Неизвестен",
                        "description": description or "Нет описания",
                        "thumbnail": thumbnail
                    }
    
        except Exception as e:
            print(f"Ошибка добавления в избранное: {e}")
        return None
    def run(self):
        self.application.run_polling()

if __name__ == "__main__":
    bot = BookBot()
    bot.run()

