from contextlib import contextmanager
from pymongo import MongoClient
from django.conf import settings


@contextmanager
def mongo_connection(collection_name):
    client = None
    try:
        client = MongoClient(settings.DATABASES['ffmpeg']['HOST'])
        db = client[settings.DATABASES['ffmpeg']['NAME']]
        yield db[collection_name]
    finally:
        if client:
            client.close()

def ffmpeg_dict(file_id):
    try:
        with mongo_connection('ffmpeg') as collection:
            ffmpeg_info = collection.find_one({'_id': file_id})
            if ffmpeg_info: return ffmpeg_info
    except Exception as e:
        print(e)
        return []
