#!/bin/bash

# Останавливаем и удаляем контейнеры текущего проекта
docker-compose down --rmi all --volumes --remove-orphans

# Очищаем Docker кэш (осторожно, это может затронуть другие проекты)
docker system prune -af
docker builder prune -af
docker image prune -a

# Переходим в директорию проекта
# shellcheck disable=SC2164
cd /home/a.shevchenko@tltv.local/PycharmProjects/

# Удаляем старую папку (если есть)
rm -rf MediaTaskDistributor

# Клонируем репозиторий
git clone https://github.com/LexShev/MediaTaskDistributor.git

# Копируем .env файл
cp /home/a.shevchenko@tltv.local/secrets/planner/env /home/a.shevchenko@tltv.local/PycharmProjects/MediaTaskDistributor/.env

# Переходим в папку проекта
# shellcheck disable=SC2164
cd MediaTaskDistributor

# Перестраиваем и запускаем контейнеры
docker-compose up --build