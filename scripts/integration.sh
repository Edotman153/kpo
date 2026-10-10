#!/usr/bin/env bash
# Запуск интеграционного теста (использует PostgreSQL). Нужен предварительный scripts/build.sh.
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
require_db

docker run --rm \
    --network "container:${DB_CONTAINER}" \
    -e DB_URL="$DB_URL_IN_DOCKER" \
    -e TELEGRAM_TOKEN="$TEST_TOKEN" \
    -v "$PWD":/app \
    book-bot-integration
