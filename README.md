Конструирование ПО
Чемодуров А.А. 	5130904/20104
Литвин С.Р. 	5130904/20104

Проблема:
В интернете бывает сложно найти какую-то книгу, например, по названию и обложке. Читатели часто вынуждены заходить на несколько сайтов, на многих из которых еще и куча рекламы. Это неудобно и порой раздражает.

Требования:
Бот позволяет пользователям искать книги через Google Books API и сохранять их в избранное.

Целевая аудитория - пользователи Telegram, которым удобно там искать книги и сохранять их в избранное.

Функционал:
Пользователь может ввести название книги, автора или ключевые слова.
Бот возвращает список книг с названием, автором, сокращенным описанием и обложкой(если есть).

Пользователь может добавлять книги в "Избранное".
Данные хранятся в PostgreSQL.

Пользователь может запросить список сохранённых книг.

Пользователь может удалять книги из списка.

Команды бота
Команда		Описание
/start			Приветствие и инструкция.
Поиск книг выполняется без команд, нужно просто написать название книги, автора, или ключевые слова.
Весь остальной функционал реализован через кнопки:
Избранное - Показывает избранное.
Добавить в избранное.
Удалить из избранного.
Помощь - Справка.

Предполагаемое число пользователей: 10к в сутки.

Характер нагрузки на сервис:
3:1 (Read/Write). Большая часть запросов — отображение избранного, поиск книг и получение информации о конкретной книге (Read), тогда как добавление и удаление из избранного, а также регистрация пользователей (Write) происходят реже.

Объемы трафика:
Запросов/сутки: 10000
Данные/запрос: 2-5 КВ
Месячный трафик: 700-1500 MB

Объемы дисковой системы:
PostgreSQL: 100-200 GB
Логи: 2 GB/мес

Первые две диаграммы С4:
Context Diagram:
![Снимок экрана от 2025-06-11 18-32-55](https://github.com/user-attachments/assets/23eea72c-0e29-4a59-8bb7-b6329fe2a871)

Container Diagram:
![Снимок экрана от 2025-06-11 18-33-10](https://github.com/user-attachments/assets/c26ccccc-b6d4-4d22-a698-ef637f21d526)

Контракты API:
Google Books API:
endpoint: GET https://www.googleapis.com/books/v1/volumes
params:
  q: string  # Поисковый запрос
  maxResults: integer
  key: string  # API-ключ
response:
  items: 
    - id: string
      volumeInfo:
        title: string
        authors: string[]
        description: string
        imageLinks: {thumbnail: string}
OpenLibrary API:
endpoint: GET https://openlibrary.org/search.json
params:
{
  q: string      	// Поисковый запрос
  limit?: number 	// Лимит результатов (по умолчанию 10)
  language?: string  // Язык (например "rus" для русского)
  fields?: string	// Дополнительные поля (через запятую)
}

Нефункциональные требования:
Время ответа бота: <1 сек
Доступность: 99%
Лимиты API: 1000 запросов/день у Google Books

Схема базы данных:
![Снимок экрана от 2025-06-11 18-58-12](https://github.com/user-attachments/assets/f98d8295-b769-459b-ae9d-e06cf57d1e62)

База данных должна соответствовать нефункциональным требованиям, потому что мы в ней создали следующие индексы для ускорения:
CREATE INDEX idx_user_books ON favorite_book(user_id);
CREATE INDEX idx_book_id ON favorite_book(book_id);

Масштабирование при 10x нагрузке
Вертикальное:
Увеличение CPU/RAM для PostgreSQL (2 vCPU → 4 vCPU)
Кэширование Redis для популярных поисковых запросов

Горизонтальное
![Снимок экрана от 2025-06-11 19-30-07](https://github.com/user-attachments/assets/9093d28c-5d42-46fe-82b3-260115113895)

Оптимизации
Асинхронные запросы: Использование aiohttp вместо requests
Батчинг: Группировка запросов к БД
CDN: Для кэширования обложек книг
Как пользоваться ботом:
1. Создать в корневой папке репозитория файл .env и заполнить его по шаблону .env.template
2. Запустить нужные скрипты в зависимости от цели:
  Для запуска самого бота запустить скрипты scripts/build.sh, затем scripts/run.sh.
  Для запуска юнит тестов запустить скрипты scripts/build.sh, затем scripts/units.sh.
  Для запуска интеграционного теста запустить скрипты scripts/build.sh, затем scripts/integration.sh.
