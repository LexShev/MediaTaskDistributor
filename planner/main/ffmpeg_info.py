from planner.mongo_settings import mongo_connection


def ffmpeg_dict(file_id):
    try:
        with mongo_connection('ffmpeg') as collection:
            ffmpeg_info = collection.find_one({'_id': file_id})
            if ffmpeg_info:
                return ffmpeg_info
            else:
                return {}

    except Exception as e:
        print(e)
        return {}
