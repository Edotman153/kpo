# Book Bot

Telegram-бот для поиска книг. Пишешь название, автора или ключевые слова, и бот присылает подборку с обложками и описаниями. Понравившиеся книги можно сохранять в личное «Избранное».

Искать книги по названию и обложке на разных сайтах, пробираясь через рекламу, неудобно. Бот собирает результаты в одном чате.

## Возможности

- Поиск без команд: достаточно написать сообщение. Бот возвращает до 5 книг с названием, автором, коротким описанием и обложкой (если она есть).
- Источники: сначала [Google Books API](https://developers.google.com/books), а если там ничего не нашлось, [Open Library](https://openlibrary.org/developers/api). Поиск ограничен русскоязычными книгами.
- Избранное: добавить книгу, посмотреть список, удалить. У каждого пользователя свой список.
- Данные хранятся в PostgreSQL.

### Как пользоваться ботом

| Действие | Как |
|----------|-----|
| Начать | `/start` |
| Найти книгу | написать название, автора или ключевые слова |
| Добавить в избранное | кнопка «⭐ Добавить в избранное» под книгой |
| Посмотреть избранное | кнопка «⭐ Избранное» в меню |
| Удалить из избранного | кнопка «❌ Удалить из избранного» под книгой в избранном |
| Справка | кнопка «ℹ Помощь» |

## Запуск

Понадобится токен бота: напиши [@BotFather](https://t.me/BotFather) в Telegram, команда `/newbot`.

Сначала создай файл с настройками:

```bash
cp .env.template .env
```

и впиши в `.env` свой `TELEGRAM_TOKEN` (значения без кавычек). `GOOGLE_BOOKS_API_KEY` необязателен, но с ключом лимиты выше.

### Вариант 1: Docker (бот + PostgreSQL)

Нужны Docker и bash (Linux, macOS, на Windows подойдут WSL2 или Git Bash).

```bash
scripts/build.sh   # собирает образы и запускает PostgreSQL
scripts/run.sh     # запускает бота (остановка: Ctrl+C)
```

Скрипты можно запускать из любой папки. БД остаётся запущенной в контейнере `book-bot-db`, её данные хранятся в томе `postgres_data`, поэтому избранное не пропадает между запусками.

### Вариант 2: без Docker

Нужен Python 3.10+. Проект проверялся на 3.12.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r app/requirements.txt
```

В `.env` укажи БД. Для быстрого старта хватит SQLite, ставить PostgreSQL не нужно:

```
DB_URL=sqlite:///books.db
```

Запуск:

```bash
python app/src/bot.py
```

Для PostgreSQL используй строку вида `postgresql+psycopg2://user:pass@localhost:5432/books`. Таблицы создаются автоматически при старте.

## Скриншоты

<img width="880" height="486" alt="Снимок экрана от 2026-10-10 14-23-34" src="https://github.com/user-attachments/assets/1f0fd719-d6b3-428c-ab78-6fc89f45441e" />

<img width="801" height="766" alt="Снимок экрана от 2026-10-10 14-23-49" src="https://github.com/user-attachments/assets/a22b8934-903c-46b8-bf41-8a8bc1b16414" />

<img width="877" height="428" alt="Снимок экрана от 2026-10-10 14-24-07" src="https://github.com/user-attachments/assets/071c2384-a4b2-4036-b32f-7bc4ff59c867" />

<img width="855" height="967" alt="Снимок экрана от 2026-10-10 14-24-24" src="https://github.com/user-attachments/assets/a65ef35b-5a41-4ae5-850e-9259d22004e6" />

<img width="1237" height="197" alt="Снимок экрана от 2026-10-10 14-25-05" src="https://github.com/user-attachments/assets/f4440217-590f-4b3a-94e2-05db33e19276" />

<img width="846" height="310" alt="Снимок экрана от 2026-10-10 14-25-16" src="https://github.com/user-attachments/assets/7504e564-f4d5-4c43-a03f-843f82a30625" />

## Тесты

| Что | Docker | Без Docker |
|-----|--------|------------|
| Юнит-тесты | `scripts/units.sh` | `TELEGRAM_TOKEN=x PYTHONPATH=. pytest units/` |
| Нагрузочные тесты | `scripts/load.sh` | `TELEGRAM_TOKEN=x PYTHONPATH=. pytest load/` |
| Интеграционный тест (нужен PostgreSQL) | `scripts/integration.sh` | `TELEGRAM_TOKEN=x DB_URL=<postgres> PYTHONPATH=. pytest integration/` |

Перед запуском скриптов выполни `scripts/build.sh`. Настоящий токен для тестов не нужен: скрипты подставляют тестовый. Для запуска без Docker установи зависимости: `pip install -r units/requirements.txt`.

Чтобы убрать всё лишнее (контейнер БД, том с данными, образы), запусти `scripts/clean.sh`. Скрипт спросит подтверждение, потому что удаляется и избранное пользователей.

## Устройство проекта

```
app/            бот
  src/bot.py          обработчики Telegram: поиск, избранное, кнопки
  src/db.py           работа с БД (SQLAlchemy), таблица favorite_books
  src/google_books.py клиент Google Books API
  src/open_lib.py     клиент Open Library API
units/          юнит-тесты
integration/    интеграционный тест: поиск, добавление в избранное, просмотр
load/           нагрузочные тесты: 1000 одновременных запросов
scripts/        скрипты сборки, запуска и тестов
```

Избранное хранится в таблице `favorite_books`: `id` книги из API и `user_id` пользователя Telegram вместе образуют ключ, плюс название, авторы, описание и ссылка на обложку.
