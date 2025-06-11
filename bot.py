import asyncio
from telegram.ext import Updater, CommandHandler, MessageHandler, filters as Filters
from google_books import GoogleBooksAPI
from db import Database
from dotenv import load_dotenv
import os

load_dotenv()

class BookBot:
    def __init__(self):
        self.api = GoogleBooksAPI()
        self.db = Database()
        self.updater = Updater(os.getenv("TELEGRAM_TOKEN"), asyncio.Queue())
        
        # Регистрация обработчиков
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("search", self.search))
        dp.add_handler(MessageHandler(Filters.text, self.handle_message))
    
    def start(self, update, context):
        update.message.reply_text("Привет! Отправь мне название книги для поиска.")
    
    def search(self, update, context):
        query = " ".join(context.args)
        if not query:
            update.message.reply_text("Укажите запрос: /search Название книги")
            return
        
        books = self.api.search_books(query)
        if not books:
            update.message.reply_text("Книги не найдены 😢")
            return
        
        for book in books:
            self.db.save_book(book)
            msg = f"📖 <b>{book['title']}</b>\n👤 {book['authors']}\n\n{book['description'][:300]}..."
            if book.get("thumbnail"):
                update.message.reply_photo(book["thumbnail"], caption=msg, parse_mode="HTML")
            else:
                update.message.reply_text(msg, parse_mode="HTML")
    
    def handle_message(self, update, context):
        self.search(update, context)
    
    def run(self):
        self.updater.start_polling()
        self.updater.idle()

if __name__ == "__main__":
    bot = BookBot()
    bot.run()
