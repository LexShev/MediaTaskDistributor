#!/bin/bash

# Останавливаем текущие контейнеры
docker compose down

# Удаляем старую папку (если есть)
rm -rf MediaTaskDistributor

# Клонируем/обновляем репозиторий
git clone https://github.com/LexShev/MediaTaskDistributor.git .
cp /home/a.shevchenko@tltv.local/secrets/planner/env .env

# Переходим в папку проекта
# shellcheck disable=SC2164
cd MediaTaskDistributor

# Перестраиваем и запускаем контейнеры
docker compose up --build