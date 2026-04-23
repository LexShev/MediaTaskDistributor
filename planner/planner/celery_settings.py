import os


SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'emergency_secret_key')

MEDIA_SERVER_IP = os.getenv('MEDIA_SERVER_IP')
MEDIA_SERVER_PORT = os.getenv('MEDIA_SERVER_PORT')

# Application definition
INSTALLED_APPS = [
    "distribution",
    "tools",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Celery Configuration
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = os.getenv('REDIS_PORT')
CELERY_BROKER_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_RESULT_BACKEND = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Moscow'
CELERY_ENABLE_UTC = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

OPLAN_DB = 'oplan3'
OPLAN_USER = os.getenv('DB_MSSQL_USER')
OPLAN_PASSWORD = os.getenv('DB_MSSQL_PASSWORD')
OPLAN_HOST = os.getenv('DB_MSSQL_HOST')
OPLAN_PORT = os.getenv('DB_MSSQL_PORT')

PLANNER_DB = 'planner'
PLANNER_USER = os.getenv('DB_MSSQL_USER')
PLANNER_PASSWORD = os.getenv('DB_MSSQL_PASSWORD')
PLANNER_HOST = os.getenv('DB_MSSQL_HOST')
PLANNER_PORT = os.getenv('DB_MSSQL_PORT')

ODBC_DRIVER = os.getenv('ODBC_DRIVER', 'ODBC Driver 17 for SQL Server')

MONGO_DB = 'planner'
DB_MONGO_HOST = os.getenv('DB_MONGO_HOST', 'mongodb')
DB_MONGO_PORT = os.getenv('DB_MONGO_PORT')
MONGO_USER = os.getenv('DB_MONGO_USER')
MONGO_PASSWORD = os.getenv('DB_MONGO_PASSWORD')
MONGO_HOST =  f'mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{DB_MONGO_HOST}:{DB_MONGO_PORT}'

DATABASES = {
    "default": {
        "ENGINE": "mssql",
        "NAME": PLANNER_DB,
        "USER": PLANNER_USER,
        "PASSWORD": PLANNER_PASSWORD,
        "HOST": PLANNER_HOST,
        # "PORT": "1433",
        "OPTIONS": {
            "driver": ODBC_DRIVER,
            "extra_params": "Encrypt=yes;TrustServerCertificate=yes"
        },
    },
    OPLAN_DB: {
        "ENGINE": "mssql",
        "NAME": OPLAN_DB,
        "USER": OPLAN_USER,
        "PASSWORD": OPLAN_PASSWORD,
        "HOST": OPLAN_HOST,
        # "PORT": "1433",
        "OPTIONS": {
            "driver": ODBC_DRIVER,
            "extra_params": "Encrypt=yes;TrustServerCertificate=yes"
        },
    },
    PLANNER_DB: {
        "ENGINE": "mssql",
        "NAME": PLANNER_DB,
        "USER": PLANNER_USER,
        "PASSWORD": PLANNER_PASSWORD,
        "HOST": PLANNER_HOST,
        # "PORT": "1433",
        "OPTIONS": {
            "driver": ODBC_DRIVER,
            "extra_params": "Encrypt=yes;TrustServerCertificate=yes"
        },
    },

}