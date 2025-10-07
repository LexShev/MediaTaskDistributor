from contextlib import contextmanager
from pymongo import MongoClient
from planner.celery_settings import MONGO_HOST, MONGO_DB


@contextmanager
def mongo_connection(collection_name):
    client = None
    try:
        client = MongoClient(MONGO_HOST)
        db = client[MONGO_DB]
        yield db[collection_name]
    finally:
        if client:
            client.close()