#!/usr/bin/env bash
# Удаляет контейнер БД, том с данными и собранные образы.
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
require_docker

read -r -p "Будет удалена БД вместе со всеми данными (избранное пользователей). Продолжить? [y/N] " answer
[[ "$answer" =~ ^[Yy]$ ]] || { echo "Отменено"; exit 0; }

docker rm -f "$DB_CONTAINER" >/dev/null 2>&1 || true
docker volume rm "$DB_VOLUME" >/dev/null 2>&1 || true
docker rmi "${IMAGES[@]}" >/dev/null 2>&1 || true
echo "Очищено"
