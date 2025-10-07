import os
from dotenv import load_dotenv

load_dotenv()


SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-fallback-key-only-for-dev')

OPLAN_DB = os.getenv('OPLAN_DB', 'planner')
OPLAN_USER = os.getenv('OPLAN_USER', 'planner')
OPLAN_PASSWORD = os.getenv('OPLAN_PASSWORD')
OPLAN_HOST = os.getenv('OPLAN_HOST', 'mssql')

PLANNER_DB = os.getenv('PLANNER_DB', 'planner')
PLANNER_USER = os.getenv('PLANNER_USER', 'planner')
PLANNER_PASSWORD = os.getenv('PLANNER_PASSWORD')
PLANNER_HOST = os.getenv('PLANNER_HOST', 'mssql')

ODBC_DRIVER = os.getenv('ODBC_DRIVER', 'ODBC Driver 17 for SQL Server')

MONGO_DB = os.getenv('MONGO_DB', 'mongo_db')
MONGO_HOST = os.getenv('MONGO_HOST', 'mongodb://localhost:27017')

# Application definition
INSTALLED_APPS = [
    "distribution",
    "messenger_static",
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
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Moscow'
CELERY_ENABLE_UTC = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

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