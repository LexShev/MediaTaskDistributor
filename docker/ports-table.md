# Матрица портов Planner ST33

## Легенда
- 🔴 **Публичный** — открыт в UFW, доступен из интернета
- 🟠 **Корпоративный** — открыт только для локальной сети (192.168.0.0/16)
- 🟡 **Межсерверный** — доступен только с определённых IP других серверов
- 🟢 **Внутренний** — только внутри сервера (localhost или Docker сеть)

---

## Сервер 1: ST 60 MSSQL Server (81.24.120.58 / 192.168.80.60)

### Основная таблица (UFW)

| Сервис | Порт | Проброс | UFW | Доступ | Разрешённые IP |
|--------|------|---------|-----|--------|----------------|
| **MSSQL** | 1433 | `1433:1433` | ✅ 1433 | 🟡 Межсерверный | `192.168.33.3` (Server 2, 3)<br/>`62.181.43.194` (Server 4) |

### UFW

```bash
#!/bin/bash
ufw default deny incoming
ufw default allow outgoing

# MSSQL - только для серверов приложений
ufw allow from 192.168.33.3 to any port 1433 proto tcp comment 'MSSQL - Server2/3 локально'
ufw allow from 62.181.43.194 to any port 1433 proto tcp comment 'MSSQL - Server4 публично'

# SSH
ufw allow from <ADMIN_IP> to any port 2233 proto tcp comment 'SSH доступ'

ufw --force enable
```

---

## Сервер 2: ST33 Streaming (81.24.120.58 / 192.168.33.3)

### Основная таблица (UFW)

| Сервис | Внутренний порт | Проброс на хост | UFW | Доступ | Разрешённые IP                                                      |
|--------|-----------------|-----------------|-----|--------|---------------------------------------------------------------------|
| **Redis** | 6379            | `6379:6379` | ✅ 6379 | 🟡 Межсерверный | `192.168.33.3` (Server 3 локально)<br/>`62.181.43.194` (Server 4)   |
| **MongoDB** | 27017           | `27017:27017` | ✅ 27017 | 🟡 Межсерверный | `192.168.33.3` (Server 3 локально)<br/>`62.181.43.194` (Server 4)   |
| **Nginx-Stream** | 8002            | `8002:8002` | ✅ 8002 | 🟡 Межсерверный | `192.168.33.3` (Server 3 локально)<br/>`62.181.43.194` (Server 4)<br/>`192.168.0.0/16` |
| **Flower** | 5555            | `5555:5555` | ✅ 5555 | 🟡 Межсерверный | `62.181.43.194` (Админ)                                             |
| **SSH** | 22              | `2233:22` | ✅ 2233 | 🔴 Публичный | Админские IP                                                        |

### Внутренние сервисы (только Docker сеть)

| Сервис | Внутренний порт | Проброс на localhost | Потребители | Примечание |
|--------|------------------|----------------------|-------------|------------|
| **Celery Worker** | — | — | Redis, MongoDB, MSSQL | Фоновые задачи, GPU |
| **Redis** | 6379 | `127.0.0.1:6379:6379` | Worker, Flower | Брокер Celery |
| **MongoDB** | 27017 | `127.0.0.1:27017:27017` | Worker | Хранение задач |
| **Nginx-Stream** | 8002 | — | Worker | Раздача видео |

### UFW скрипт

```bash
#!/bin/bash
ufw default deny incoming
ufw default allow outgoing

# Redis
ufw allow from 192.168.33.3 to any port 6379 proto tcp comment 'Redis - Server3 локально'
ufw allow from 62.181.43.194 to any port 6379 proto tcp comment 'Redis - Server4'

# MongoDB
ufw allow from 192.168.33.3 to any port 27017 proto tcp comment 'MongoDB - Server3 локально'
ufw allow from 62.181.43.194 to any port 27017 proto tcp comment 'MongoDB - Server4'

# Nginx-Stream
ufw allow from 192.168.33.3 to any port 8002 proto tcp comment 'Streaming - Server3 локально'
ufw allow from 62.181.43.194 to any port 8002 proto tcp comment 'Streaming - Server4'

# Flower (только админ)
ufw allow from 62.181.43.194 to any port 5555 proto tcp comment 'Flower - Admin'

# SSH
ufw allow from <ADMIN_IP> to any port 22 proto tcp comment 'SSH доступ'

```

---

## Сервер 3: ST33 Internal Planner (192.168.33.3)

### Основная таблица (UFW)

| Сервис | Внутренний порт | Проброс на хост | UFW | Доступ | Разрешённые IP |
|--------|-----------------|-----------------|-----|--------|----------------|
| **Nginx HTTP** | 80              | `80:80` | ✅ 80 | 🟠 Корпоративный | `192.168.0.0/16` |
| **Nginx HTTPS** | 443             | `443:443` | ✅ 443 | 🟠 Корпоративный | `192.168.0.0/16` |
| **SSH** | 22              | `2233:22` | ✅ 2233 | 🟠 Корпоративный | `192.168.0.0/16` |

### Внутренние сервисы (только Docker сеть)

| Сервис | Внутренний порт | Проброс на localhost | Потребители | Примечание |
|--------|------------------|----------------------|-------------|------------|
| **WSGI (Gunicorn)** | 8000 | — | Nginx | Основное приложение |
| **ASGI (Daphne)** | 8001 | — | Nginx | WebSocket/асинхронные запросы |
| **Nginx** | 80, 443 | — | Пользователи | Веб-сервер + SSL |

### UFW скрипт

```bash
#!/bin/bash
ufw default deny incoming
ufw default allow outgoing

# Веб-доступ только из корпоративной сети
ufw allow from 192.168.0.0/16 to any port 80 proto tcp comment 'HTTP - Корп. сеть'
ufw allow from 192.168.0.0/16 to any port 443 proto tcp comment 'HTTPS - Корп. сеть'

# SSH только из корпоративной сети
ufw allow from 192.168.0.0/16 to any port 22 proto tcp comment 'SSH - Корп. сеть'

ufw --force enable
```

---

## Сервер 4: S11 External Planner (62.181.43.194)

### Основная таблица (UFW)

| Сервис | Внутренний порт | Проброс на хост | UFW | Доступ | Разрешённые IP |
|--------|------------------|-----------------|-----|--------|----------------|
| **Nginx HTTP** | 80 | `80:80` | ✅ 80 | 🔴 Публичный | Весь мир |
| **Nginx HTTPS** | 443 | `443:443` | ✅ 443 | 🔴 Публичный | Весь мир |
| **SSH** | 22 | `51515:22` | ✅ 51515 | 🔴 Публичный | Админские IP |

### Внутренние сервисы (только Docker сеть)

| Сервис | Внутренний порт | Проброс на localhost | Потребители | Примечание |
|--------|------------------|----------------------|-------------|------------|
| **WSGI (Gunicorn)** | 8000 | — | Nginx | Основное приложение |
| **ASGI (Daphne)** | 8001 | — | Nginx | WebSocket/асинхронные запросы |
| **Nginx** | 80, 443 | — | Пользователи | Веб-сервер + Let's Encrypt |

### UFW скрипт

```bash
#!/bin/bash
ufw default deny incoming
ufw default allow outgoing

# Веб-доступ для всех
ufw allow 80/tcp comment 'HTTP - Все'
ufw allow 443/tcp comment 'HTTPS - Все'

# SSH только для админа
ufw allow from <ADMIN_IP> to any port 22 proto tcp comment 'SSH - Admin only'

ufw --force enable
```

---

## Сводная таблица всех портов (UFW)

| Сервер | Порт | Сервис | Доступ | Разрешённые IP                                   |
|--------|------|--------|--------|--------------------------------------------------|
| **ST60 (MSSQL)** | 1433 | MSSQL | 🟡 Межсерверный | `192.168.33.3`, `62.181.43.194`, `<ALLOWED IPs>` |
| **ST33 (Streaming)** | 6379 | Redis | 🟡 Межсерверный | `192.168.33.3`, `62.181.43.194`                  |
| **ST33 (Streaming)** | 27017 | MongoDB | 🟡 Межсерверный | `192.168.33.3`, `62.181.43.194`                  |
| **ST33 (Streaming)** | 8002 | Streaming | 🟡 Межсерверный | `192.168.33.3`, `62.181.43.194`                  |
| **ST33 (Streaming)** | 5555 | Flower | 🟡 Межсерверный | `192.168.33.3`, `62.181.43.194`                  |
| **ST33 (Streaming)** | 2233 | SSH | 🔴 Публичный | `<ADMIN_IP>`                                     |
| **ST33 (Internal)** | 80 | HTTP | 🟠 Корпоративный | `192.168.0.0/16`                                 |
| **ST33 (Internal)** | 443 | HTTPS | 🟠 Корпоративный | `192.168.0.0/16`                                 |
| **ST33 (Internal)** | 2233 | SSH | 🟠 Корпоративный | `192.168.0.0/16`                                 |
| **S11 (External)** | 80 | HTTP | 🔴 Публичный | `0.0.0.0/0`                                      |
| **S11 (External)** | 443 | HTTPS | 🔴 Публичный | `0.0.0.0/0`                                      |
| **S11 (External)** | 51515 | SSH | 🔴 Публичный | `<ADMIN_IP>`                                     |

---

## DNS записи

| Тип | Имя | Значение | Сервер |
|-----|-----|----------|--------|
| A | `tvfab.ru` | `62.181.43.194` | Server 4 (External) |
| A | `tvfab.local` | `192.168.33.3` | Server 3 (Internal) |

---

## Быстрая UFW сводка (все сервера)

### Сервер 1 st60 (MSSQL)
```bash
ufw allow from 192.168.33.3 to any port 1433 proto tcp
ufw allow from <ALLOWED IPs> to any port 1433 proto tcp
```

### Сервер 2 st33 (Streaming)
```bash
ufw allow from 192.168.33.3 to any port 6379,27017,8002 proto tcp
ufw allow from <ALLOWED IPs> to any port 6379,27017,8002,5555 proto tcp
```

### Сервер 3 st33 (Internal)
```bash
ufw allow from 192.168.0.0/16 to any port 80,443,2233 proto tcp
```

### Сервер 4 s11 (External)
```bash
ufw allow 80,443/tcp
ufw allow from <ADMIN_IP> to any port 51515 proto tcp
```