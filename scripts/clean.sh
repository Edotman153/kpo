#!/bin/bash

docker stop book-bot-db
docker rm book-bot-db
docker volume rm postgres_data
docker rmi book-bot-app book-bot-units
