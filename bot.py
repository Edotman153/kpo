import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters as Filters
from google_books import GoogleBooksAPI
from db import Database
from dotenv import load_dotenv
import os

load_dotenv()

class BookBot:
    def __init__(self):
        self.api = GoogleBooksAPI()
        self.db = Database()
        self.application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
        # Регистрация обработчиков
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("search", self.search))
        self.application.add_handler(MessageHandler(Filters.Text, self.handle_message))
    
    async def start(self, update, context):
        await update.message.reply_text("Привет! Отправь мне название книги для поиска.")
    
    async def search(self, update, context):
        query = " ".join(context.args)
        if not query:
            await update.message.reply_text("Укажите запрос: /search Название книги")
            return
        
        books = self.api.search_books(query)
        if not books:
            await update.message.reply_text("Книги не найдены 😢")
            return
        
        for book in books:
            self.db.save_book(book)
            msg = f"📖 <b>{book['title']}</b>\n👤 {book['authors']}\n\n{book['description'][:300]}..."
            if book.get("thumbnail"):
                await update.message.reply_photo(book["thumbnail"], caption=msg, parse_mode="HTML")
            else:
                await update.message.reply_text(msg, parse_mode="HTML")
    
    async def handle_message(self, update, context):
        await self.search(update, context)
    
    def run(self):
        self.application.run_polling()

#if name == "__main__":
bot = BookBot()
bot.run()
