#!/bin/bash

# Запуск unit-тестов
docker run --rm \
  --network container:book-bot-db \
  -e DB_URL=postgresql://user:pass@localhost:5434/books \
  -v $(pwd):/app \
  book-bot-units
