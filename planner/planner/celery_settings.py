import os
from pathlib import Path


SERVICE_TYPE = os.getenv('SERVICE_TYPE', 'internal')
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'emergency_secret_key')

MEDIA_SERVER_IP = os.getenv('MEDIA_SERVER_IP')
MEDIA_SERVER_PORT = os.getenv('MEDIA_SERVER_PORT')
CHANNELS_REDIS_HOST = os.getenv('CHANNELS_REDIS_HOST', MEDIA_SERVER_IP)

# Application definition
INSTALLED_APPS = [
    "distribution",
    "tools",
    "file_manager",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "storages"
]

# Настройки для S3 (MinIO)
USE_S3_STORAGE = os.getenv('USE_S3_STORAGE', 'false').lower() == 'true'

AWS_ACCESS_KEY_ID = os.getenv('MINIO_DJANGO_USER')
AWS_SECRET_ACCESS_KEY = os.getenv('MINIO_DJANGO_PASSWORD')

S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
AWS_STORAGE_BUCKET_NAME = S3_BUCKET_NAME
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL', 'http://minio:9000')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_ADDRESSING_STYLE = 'path'
AWS_S3_USE_SSL = os.getenv('AWS_S3_USE_SSL', 'true').lower() == 'true'
AWS_S3_VERIFY = os.getenv('AWS_S3_VERIFY', 'false').lower() == 'true'

AWS_DEFAULT_ACL = os.getenv('AWS_DEFAULT_ACL', 'private')
AWS_QUERYSTRING_AUTH = True

if SERVICE_TYPE == 'internal':
    AWS_S3_CUSTOM_DOMAIN = 'tvfab.local/s3/django-aws'
else:
    AWS_S3_CUSTOM_DOMAIN = 'tvfab.ru/s3/django-aws'

if USE_S3_STORAGE:
    DEFAULT_FILE_STORAGE = 'planner.storage.MediaStorage'

BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
MEDIA_POSTERS = os.path.join(BASE_DIR, 'media/posters')
MEDIA_WAVEFORMS = os.path.join(BASE_DIR, 'media/waveforms')
DEFAULT_LOG_DIR = os.path.join(BASE_DIR, 'logs/')

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
            "extra_params": "Encrypt=yes;TrustServerCertificate=yes;Login Timeout=10"
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
            "extra_params": "Encrypt=yes;TrustServerCertificate=yes;Login Timeout=10"
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
            "extra_params": "Encrypt=yes;TrustServerCertificate=yes;Login Timeout=10"
        },
    },

}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [{
                "address": f"redis://:{REDIS_PASSWORD}@{CHANNELS_REDIS_HOST}:{REDIS_PORT}/1",
            }],
        },
    },
}