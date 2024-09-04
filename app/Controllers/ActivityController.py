from flask import request
from bson import ObjectId
from app.Models.ActivityModel import ActivityModel
from datetime import datetime

class ActivityController:
    def __init__(self, db):
        self.model = ActivityModel(db)

    def create_activity(self):
        data = request.get_json()
        activity_id = self.model.create_activity(data)
        return {'activity_id': str(activity_id)}

    def get_all_activities(self):
        activities = self.model.get_all_activities()
        return [{'_id': str(activity['_id']), **activity} for activity in activities]

    def get_activity_by_id(self, activity_id):
        activity = self.model.get_activity_by_id(ObjectId(activity_id))
        if activity:
            activity['_id'] = str(activity['_id'])
            return activity
        return {'error': 'Activity not found'}

    def update_activity(self, activity_id):
        data = request.get_json()
        result = self.model.update_activity(ObjectId(activity_id), data)
        if result.modified_count:
            return {'message': 'Activity updated successfully'}
        return {'message': 'No activity was updated'}

    def delete_activity(self, activity_id):
        result = self.model.delete_activity(ObjectId(activity_id))
        if result.deleted_count:
            return {'message': 'Activity deleted successfully'}
        return {'message': 'No activity was deleted'}

    def get_activities_by_time(self, start_time, end_time):
        start_time = datetime.fromisoformat(start_time)
        end_time = datetime.fromisoformat(end_time)
        activities = self.model.get_activities_by_time(start_time, end_time)
        return [{'_id': str(activity['_id']), **activity} for activity in activities]