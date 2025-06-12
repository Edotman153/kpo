#!/bin/bash

# Запуск unit-тестов
docker run --rm \
  --network container:book-bot-db \
  -e DB_URL=postgresql://user:pass@localhost:5434/books \
  book-bot-units pytest units/
