#!/usr/bin/env bash
# Собирает образы (бот и тесты) и запускает PostgreSQL в контейнере book-bot-db.
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
require_docker

docker build -t book-bot-app ./app
docker build -t book-bot-units ./units
docker build -t book-bot-integration ./integration
docker build -t book-bot-load ./load

# БД перезапускается, данные сохраняются в томе postgres_data
docker rm -f "$DB_CONTAINER" >/dev/null 2>&1 || true
docker run -d --name "$DB_CONTAINER" \
    -e POSTGRES_USER=user \
    -e POSTGRES_PASSWORD=pass \
    -e POSTGRES_DB=books \
    -p 5434:5432 \
    -v "$DB_VOLUME":/var/lib/postgresql/data \
    postgres:15 >/dev/null

echo -n "Жду готовности PostgreSQL"
for _ in $(seq 1 30); do
    if docker exec "$DB_CONTAINER" pg_isready -U user -d books >/dev/null 2>&1; then
        echo
        echo "Готово: образы собраны, БД запущена (с хоста: localhost:5434)"
        exit 0
    fi
    echo -n "."
    sleep 1
done
echo
echo "PostgreSQL не поднялся за 30 секунд, смотри: docker logs $DB_CONTAINER" >&2
exit 1
