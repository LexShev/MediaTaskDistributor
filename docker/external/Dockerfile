FROM python:3.10-slim-bookworm

# Устанавливаем системные зависимости
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    gcc \
    unixodbc-dev \
    libgssapi-krb5-2 \
    && rm -rf /var/lib/apt/lists/*

# Установка Microsoft ODBC драйвера 18
RUN set -ex \
    && DEBIAN_VERSION=$(grep VERSION_ID /etc/os-release | cut -d '"' -f 2 | cut -d '.' -f 1) \
    && curl -sSL -o packages-microsoft-prod.deb \
     "https://packages.microsoft.com/config/debian/${DEBIAN_VERSION}/packages-microsoft-prod.deb" \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
        msodbcsql18 \
        mssql-tools18 \
    && echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> /etc/bash.bashrc \
    && rm -rf /var/lib/apt/lists/*

# Создаем непользовательского пользователя
RUN groupadd -r django && useradd -r -g django django

WORKDIR /app

# Копируем requirements (пути ОТНОСИТЕЛЬНО контекста сборки)
COPY planner/requirements.txt .
RUN python -m pip install pip==25.2 && \
    python -m pip install --no-cache-dir -r requirements.txt

# Копируем весь проект (кроме .dockerignore)
COPY . .

# Меняем владельца всех файлов
RUN chown -R django:django /app

# Переключаемся на непользовательского пользователя
USER django

CMD ["python", "planner/manage.py", "runserver", "0.0.0.0:8000"]