import asyncio
from open_lib import OpenLibraryAPI
from telegram.ext import Application, CommandHandler, MessageHandler, filters as Filters
from telegram import ReplyKeyboardMarkup, KeyboardButton
from google_books import GoogleBooksAPI
from db import Database
from dotenv import load_dotenv
import os

load_dotenv()

class BookBot:
    def __init__(self):
        self.google_api = GoogleBooksAPI()
        self.open_library_api = OpenLibraryAPI()
        self.db = Database()
        self.application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
        
        # Создаем клавиатуру, которая будет показываться всегда
        self.reply_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton("🔍 Поиск книги"), KeyboardButton("ℹ Помощь")],
                [KeyboardButton("⭐ Избранное")]
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие или введите название книги"
        )
        
        # Регистрация обработчиков
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(MessageHandler(Filters.TEXT & ~Filters.COMMAND, self.handle_message))
        self.application.add_handler(MessageHandler(Filters.Regex(r'^🔍 Поиск книги$'), self.handle_search_button))
    
    async def start(self, update, context):
        """Обработчик команды /start - показывает клавиатуру"""
        await update.message.reply_text(
            "📚 Добро пожаловать в книжный бот!\n\n"
            "Вы можете:\n"
            "- Нажать кнопку '🔍 Поиск книги' и ввести название\n"
            "- Просто написать название книги в чат",
            reply_markup=self.reply_keyboard
        )
    
    async def handle_search_button(self, update, context):
        """Обработчик нажатия кнопки поиска"""
        await update.message.reply_text(
            "Введите название книги или автора:",
            reply_markup=self.reply_keyboard
        )
    
    async def handle_message(self, update, context):
        """Обработчик всех текстовых сообщений"""
        text = update.message.text
        
        if text.lower() in ["помощь", "ℹ помощь"]:
            await self.start(update, context)
        elif text.lower() in ["избранное", "⭐ избранное"]:
            await self.show_favorites(update, context)
        elif text.lower() == "🔍 поиск книги":
            await self.handle_search_button(update, context)
        else:
            # Если просто ввели текст - считаем это поиском книги
            await self.search_books(update, context, text)
    
    async def search_books(self, update, context, query):
        """Поиск книг и вывод результатов"""
        if not query:
            await update.message.reply_text("Пожалуйста, введите название книги")
            return
        
        books = await self.google_api.search_books(query)
        
        if not books:
            books = await self.open_library_api.search_books(query)
            if not books:
                await update.message.reply_text("Книги не найдены 😢 Попробуйте другой запрос")
                return
        for book in books:
            msg = f"📖 <b>{book['title']}</b>\n👤 {book['authors']}\n\n{book['description'][:500]}..."
        
            if book.get("thumbnail"):
                await update.message.reply_photo(
                    photo=book["thumbnail"],
                    caption=msg,
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text(
                    msg,
                    parse_mode="HTML"
               )
    
    async def show_favorites(self, update, context):
        """Показать избранные книги"""
        favorites = await self.db.get_favorites(update.effective_user.id)
        if not favorites:
            await update.message.reply_text("У вас пока нет избранных книг")
            return
        
        for book in favorites:
            msg = f"⭐ <b>{book['title']}</b>\n👤 {book['authors']}"
            await update.message.reply_text(msg, parse_mode="HTML")
    
    def run(self):
        self.application.run_polling()

if __name__ == "__main__":
    bot = BookBot()
    bot.run()
