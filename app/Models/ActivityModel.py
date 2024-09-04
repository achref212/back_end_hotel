from bson import ObjectId
from datetime import datetime

class ActivityModel:
    def __init__(self, db):
        self.collection = db['Activities']

    def create_activity(self, data):
        return self.collection.insert_one(data).inserted_id

    def get_all_activities(self):
        return list(self.collection.find())

    def get_activity_by_id(self, activity_id):
        activity = self.collection.find_one({'_id': ObjectId(activity_id)})
        if activity:
            activity['_id'] = str(activity['_id'])
        return activity

    def update_activity(self, activity_id, data):
        return self.collection.update_one({'_id': ObjectId(activity_id)}, {'$set': data})

    def delete_activity(self, activity_id):
        return self.collection.delete_one({'_id': ObjectId(activity_id)})

    def get_activities_by_time(self, start_time, end_time):
        return list(self.collection.find({'startTime': {'$gte': start_time}, 'endTime': {'$lte': end_time}}))
