FROM python:3.10-slim

# Устанавливаем системные зависимости для ODBC
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
    && SUPPORTED_VERSIONS="11 12" \
    && case " $SUPPORTED_VERSIONS " in \
        *" $DEBIAN_VERSION "*) \
            echo "Debian $DEBIAN_VERSION is supported" ;; \
        *) \
            echo "Debian $DEBIAN_VERSION is not currently supported."; \
            exit 1 ;; \
    esac \
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

WORKDIR /app
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY .. .
CMD ["python", "planner/manage.py", "runserver", "0.0.0.0:8000"]
