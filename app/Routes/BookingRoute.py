from bson import ObjectId
from flask import request, jsonify

from app.Controllers.BookingController import BookingController
from app import api, mongo, app  # This is typical if you have centralized your Flask app's configurations and instances
from flask_restx import Api, Resource, fields

from app.Repository import UserRepo

booking_controller = BookingController(mongo)
db = mongo.db  # Use your database name

collection = db['Bookings']
booking_model = api.model('Booking', {
    'userId': fields.String(required=True, description='User ID'),
    'roomId': fields.String(required=True, description='Room ID'),
    'checkInDate': fields.DateTime(required=True, description='Check-in Date'),
    'checkOutDate': fields.DateTime(required=True, description='Check-out Date'),
    'guests': fields.Integer(required=True, description='Number of Guests'),
    'status': fields.String(required=True, description='Booking Status'),
})


@app.route('/bookings/', methods=['POST'])
def create_booking():
    try:
        data = request.get_json()  # Parse the JSON data sent with the POST request

        # Basic validation to check if necessary fields are present
        if 'userId' not in data or 'roomId' not in data:
            return jsonify({'error': 'Missing userId or roomId'}), 400

        # Verify user_id
        user_id = ObjectId(data['userId'])
        user = UserRepo.UserRepository.get_by_id(mongo, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Verify room_id
        room_id = ObjectId(data['roomId'])
        room = db.Rooms.find_one({'_id': room_id})
        if not room:
            return jsonify({'error': 'Room not found'}), 404

        # Insert the booking data into the database
        booking_id = db.Bookings.insert_one(data).inserted_id
        return jsonify({'message': 'Booking created successfully', 'booking_id': str(booking_id)}), 201

    except Exception as e:
        # Catch any other exceptions and return an error response
        return jsonify({'error': str(e)}), 500

@app.route('/bookings/', methods=['GET'])
def get_all_bookings():
    try:
        bookings = db.Bookings.find()
        results = []
        for booking in bookings:
            booking['_id'] = str(booking['_id'])  # Convert ObjectId to string for JSON serialization
            results.append(booking)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/bookings/<string:booking_id>', methods=['GET'])
def get_booking_by_id(booking_id):
    try:
        booking = db.Bookings.find_one({'_id': ObjectId(booking_id)})
        if booking:
            booking['_id'] = str(booking['_id'])  # Convert ObjectId to string for JSON serialization
            return jsonify(booking), 200
        else:
            return jsonify({'message': 'Booking not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/bookings/<string:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    try:
        result = db.Bookings.delete_one({'_id': ObjectId(booking_id)})
        if result.deleted_count > 0:
            return jsonify({'message': 'Booking deleted successfully'}), 200
        else:
            return jsonify({'message': 'Booking not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/bookings/<string:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No update data provided'}), 400

        result = db.Bookings.update_one({'_id': ObjectId(booking_id)}, {'$set': data})
        if result.modified_count > 0:
            return jsonify({'message': 'Booking updated successfully'}), 200
        else:
            return jsonify({'message': 'No changes made or booking not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/bookings/user/<string:user_id>', methods=['GET'])
def get_bookings_by_user(user_id):
    try:
        bookings = db.Bookings.find({'userId': user_id})
        results = []
        for booking in bookings:
            booking['_id'] = str(booking['_id'])  # Convert ObjectId to string for JSON serialization
            results.append(booking)
        if results:
            return jsonify(results), 200
        else:
            return jsonify({'message': 'No bookings found for this user'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

