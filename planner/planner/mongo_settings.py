from contextlib import contextmanager
from pymongo import MongoClient
from planner.celery_settings import MONGO_HOST, MONGO_DB, MONGO_TIMEOUT_MS


@contextmanager
def mongo_connection(collection_name, db_name=MONGO_DB):
    client = None
    try:
        client = MongoClient(
            MONGO_HOST,
            serverSelectionTimeoutMS=MONGO_TIMEOUT_MS,
            connectTimeoutMS=MONGO_TIMEOUT_MS,
            socketTimeoutMS=MONGO_TIMEOUT_MS,
        )
        db = client[db_name]
        yield db[collection_name]
    finally:
        if client:
            client.close()