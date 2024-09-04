from bson import ObjectId
from app import mongo

db = mongo.db
class BookingModel:
    def __init__(self, db):
        self.collection = db['Bookings']

    def create_booking(self, data):
        return db.Bookings.insert_one(data).inserted_id

    def get_all_bookings(self):
        return list(db.Bookings.find())

    def get_booking_by_id(self, booking_id):
        booking = self.collection.find_one({'_id': ObjectId(booking_id)})
        if booking:
            booking['_id'] = str(booking['_id'])
        return booking

    def update_booking(self, booking_id, data):
        return self.collection.update_one({'_id': ObjectId(booking_id)}, {'$set': data})

    def delete_booking(self, booking_id):
        return self.collection.delete_one({'_id': ObjectId(booking_id)})

    def get_bookings_by_user(self, user_id):
        return list(self.collection.find({'userId': user_id}))
