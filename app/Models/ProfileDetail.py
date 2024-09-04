# detailModel.py

from pymongo import MongoClient
from bson import ObjectId


class detailModel:
    def __init__(self, db):
        self.collection = db['details']

    def create_detail(self, data):
        # Generate a new ObjectId for the _id field
        data['_id'] = str(ObjectId())
        return self.collection.insert_one(data).inserted_id

    def get_all_details(self):
        return list(self.collection.find())

    def get_detail_by_id(self, detail_id):
        return self.collection.find_one({'_id': detail_id})

    def update_detail(self, detail_id, data):
        # Exclude the '_id' field from the update
        return self.collection.update_one({'_id': detail_id}, {'$set': {k: v for k, v in data.items() if k != '_id'}})

    def delete_detail(self, detail_id):
        return self.collection.delete_one({'_id': detail_id})
