#!/bin/bash

# Запуск unit-тестов
docker run --rm \
  --network container:book-bot-db \
  -e DB_URL=postgresql://user:pass@localhost:5432/books \
  -v $(pwd):/app \
  book-bot-load
