from django.db import connections
import pymongo


conn = pymongo.MongoClient("localhost", 27017)
db = conn['planner_db']
collection = db['mediainfo']

def ffmpeg_dict(program_id):
    cursor = collection.find({'_id': program_id})
    for record in cursor:
        return record