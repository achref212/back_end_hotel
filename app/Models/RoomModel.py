from bson import ObjectId

from app import mongo

db = mongo.db

class RoomModel:
    def __init__(self, db):
        self.collection = db['Rooms']

    def create_room(self, data):
        return self.collection.insert_one(data).inserted_id

    def get_all_rooms(self):
        # Correctly use the `find()` method to retrieve all rooms
        print("Retrieving all rooms from the database...")
        return list(self.collection.find())  # Convert cursor to a list

    def get_room_by_id(self, room_id):
        # Retrieve a room by its ObjectId
        print(f"Retrieving room with ID: {room_id}")
        return db.Rooms.find_one({'_id': ObjectId(room_id)})

    def update_room(self, room_id, data):
        return self.collection.update_one({'_id': ObjectId(room_id)}, {'$set': data})

    def delete_room(self, room_id):
        return db.Rooms.delete_one({'_id': ObjectId(room_id)})

    def get_rooms_by_availability(self, availability):
        return list(self.collection.find({'availability': availability}))