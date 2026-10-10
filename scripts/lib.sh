#!/usr/bin/env bash
# shellcheck disable=SC2034  # переменные используются скриптами, которые подключают этот файл
# Общие настройки для всех скриптов (подключается через source, напрямую не запускается).
set -euo pipefail

# Скрипты можно запускать из любой папки: всегда работаем из корня репозитория
cd "$(dirname "${BASH_SOURCE[0]}")/.."

DB_CONTAINER="book-bot-db"
DB_VOLUME="postgres_data"
IMAGES=(book-bot-app book-bot-units book-bot-integration book-bot-load)

# Контейнеры с приложением/тестами делят сетевое пространство с контейнером БД,
# поэтому для них Postgres доступен как localhost:5432 (а не 5434, как с хоста).
DB_URL_IN_DOCKER="postgresql+psycopg2://user:pass@localhost:5432/books"

# Для тестов настоящий токен не нужен, но библиотека требует непустую строку
TEST_TOKEN="123456:test-token"

require_docker() {
    command -v docker >/dev/null || { echo "Docker не найден. Установи Docker: https://docs.docker.com/engine/install/" >&2; exit 1; }
}

require_db() {
    require_docker
    if [ -z "$(docker ps -q -f "name=^${DB_CONTAINER}$")" ]; then
        echo "Контейнер БД ${DB_CONTAINER} не запущен. Сначала выполни scripts/build.sh" >&2
        exit 1
    fi
}
