#!/bin/bash

docker run --rm \
  --network container:book-bot-db \
  -e DB_URL=postgresql://user:pass@localhost:5432/books \
  --env-file .env \
  -v ./app:/app \
  book-bot-app
