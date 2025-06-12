import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from google_books import GoogleBooksAPI
from open_lib import OpenLibraryAPI
from db import Database
from dotenv import load_dotenv
import os

load_dotenv()

class BookBot:
    def __init__(self):
        self.google_api = GoogleBooksAPI()
        self.open_lib_api = OpenLibraryAPI()
        self.db = Database()
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
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.search_books))
        self.application.add_handler(CallbackQueryHandler(self.handle_button_click))

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
                
                msg = f"📖 <b>{book['title']}</b>\n👤 {book['authors']}\n\n{book.get('description', 'Описание отсутствует')[:500]}..."
                
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
                msg = f"⭐ <b>{book['title']}</b>\n👤 {book['authors']}\n\n{book.get('description', '')[:300]}..."
                
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
                    book_data["user_id"] = user_id
                    await self.db.save_book(book_data)
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
            logger.error(f"Ошибка обработки кнопки: {e}")
            await query.answer("Произошла ошибка", show_alert=True)
    async def _get_book_data(self, book_id):
        """Получение данных книги по ID (заглушка)"""
        # В реальной реализации нужно или:
        # 1. Хранить последние найденные книги в временном хранилище
        # 2. Делать запрос к API по book_id
        for book in getattr(self, 'last_search_results', []):
            if book.get('id') == book_id:
                return book
        return None
    def run(self):
        self.application.run_polling()

if __name__ == "__main__":
    bot = BookBot()
    bot.run()
