#!/usr/bin/env bash
# Запускает бота. Нужен заполненный .env (cp .env.template .env) и предварительный scripts/build.sh.
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
require_db

if [ ! -f .env ]; then
    echo "Нет файла .env. Создай его: cp .env.template .env, и впиши TELEGRAM_TOKEN" >&2
    exit 1
fi
if ! grep -Eq '^TELEGRAM_TOKEN=.+' .env; then
    echo "В .env не заполнен TELEGRAM_TOKEN (получить токен: @BotFather в Telegram)" >&2
    exit 1
fi

# -e имеет приоритет над --env-file, поэтому DB_URL из .env здесь не мешает
docker run --rm \
    --network "container:${DB_CONTAINER}" \
    --env-file .env \
    -e DB_URL="$DB_URL_IN_DOCKER" \
    -v "$PWD/app":/app \
    book-bot-app
