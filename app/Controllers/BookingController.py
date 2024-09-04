from flask import request, jsonify
from bson import ObjectId

from app import mongo
from app.Models.BookingModel import BookingModel
from app.Models.RoomModel import RoomModel
from app.Repository import UserRepo

db = mongo.db

class BookingController:
    def __init__(self, db):
        self.model = BookingModel(db)
        self.room_model = RoomModel(db)

    def create_booking(self):
        data = request.get_json()

        # Verify user_id
        user_id = ObjectId(data.get('userId'))
        user = UserRepo.UserRepository.get_by_id(mongo, user_id)  # Assuming a method to fetch user
        print(user)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Verify room_id
        room_id = ObjectId(data.get('roomId'))
        room = self.room_model.get_room_by_id(room_id)  # Assuming a method to fetch room
        print(room)
        if not room:
            return jsonify({'error': 'Room not found'}), 404

        # Create booking if both user and room are valid
        try:
            # booking_id = db.Bookings.insert_one(data).inserted_id
            booking_id = self.model.create_booking(data)
            return jsonify({'booking_id': str(booking_id)}), 201

        except Exception as e:
            # Ensure the exception is converted to a string if it's not a message already
            error_message = str(e) if not isinstance(e, str) else e
            return jsonify({'error': error_message}), 500

    def get_all_bookings(self):
        bookings = self.model.get_all_bookings()
        return [{'_id': str(booking['_id']), **booking} for booking in bookings]

    def get_booking_by_id(self, booking_id):
        booking = self.model.get_booking_by_id(ObjectId(booking_id))
        if booking:
            booking['_id'] = str(booking['_id'])
            return booking
        return {'error': 'Booking not found'}

    def update_booking(self, booking_id):
        data = request.get_json()
        result = self.model.update_booking(ObjectId(booking_id), data)
        if result.modified_count:
            return {'message': 'Booking updated successfully'}
        return {'message': 'No booking was updated'}

    def delete_booking(self, booking_id):
        result = self.model.delete_booking(ObjectId(booking_id))
        if result.deleted_count:
            return {'message': 'Booking deleted successfully'}
        return {'message': 'No booking was deleted'}

    def get_bookings_by_user(self, user_id):
        bookings = self.model.get_bookings_by_user(user_id)
        return [{'_id': str(booking['_id']), **booking} for booking in bookings]