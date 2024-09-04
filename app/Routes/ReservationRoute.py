from bson import ObjectId
from flask import request, jsonify
from app.Repository import UserRepo
from app import api, mongo, app
from flask_restx import Resource, fields

db = mongo.db

# Define the reservation model using Flask-RESTx
reservation_model = api.model('Reservation', {
    'userId': fields.String(required=True, description='User ID'),
    'activityId': fields.String(required=True, description='Activity ID'),
    'reservationDate': fields.DateTime(required=True, description='Reservation Date'),
    'guests': fields.Integer(required=True, description='Number of Guests'),
    'status': fields.String(required=True, description='Reservation Status'),
})
@app.route('/reservations/', methods=['POST'])
def create_reservation():
    try:
        # Ensure the request has JSON data and the correct Content-Type header
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 415

        data = request.get_json()  # Parse the JSON data sent with the POST request

        # Basic validation to check if necessary fields are present
        if 'userId' not in data or 'activityId' not in data or 'guests' not in data:
            return jsonify({'error': 'Missing userId, activityId, or guests'}), 400

        # Verify user_id
        try:
            user_id = ObjectId(data['userId'])
        except Exception:
            return jsonify({'error': 'Invalid userId format'}), 400
        user = UserRepo.UserRepository.get_by_id(mongo, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Verify activity_id
        try:
            activity_id = ObjectId(data['activityId'])
        except Exception:
            return jsonify({'error': 'Invalid activityId format'}), 400
        activity = db.Activities.find_one({'_id': activity_id})
        if not activity:
            return jsonify({'error': 'Activity not found'}), 404

        # Convert currentParticipants and maxParticipants to integers if stored as strings
        try:
            current_participants = int(activity.get('currentParticipants', '0'))  # Default to '0' if missing
            max_participants = int(activity.get('maxParticipants', '0'))  # Default to '0' if missing
        except ValueError:
            return jsonify({'error': 'Invalid format for maxParticipants or currentParticipants'}), 400

        # Check if the activity has enough available slots for the number of guests
        guests = int(data['guests'])
        available_slots = max_participants - current_participants

        if available_slots < guests:
            return jsonify({'error': 'Not enough available slots for the number of guests'}), 400

        # Reserve the activity by incrementing the current participants by the number of guests
        db.Activities.update_one({'_id': activity_id}, {'$inc': {'currentParticipants': guests}})

        # Insert the reservation data into the database
        reservation_id = db.Reservations.insert_one(data).inserted_id
        return jsonify({'message': 'Reservation created successfully', 'reservation_id': str(reservation_id)}), 201

    except Exception as e:
        # Catch any other exceptions and return an error response
        return jsonify({'error': str(e)}), 500


@app.route('/reservations/', methods=['GET'])
def get_all_reservations():
    try:
        reservations = db.Reservations.find()
        results = []
        for reservation in reservations:
            reservation['_id'] = str(reservation['_id'])  # Convert ObjectId to string for JSON serialization
            results.append(reservation)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reservations/<string:reservation_id>', methods=['GET'])
def get_reservation_by_id(reservation_id):
    try:
        reservation = db.Reservations.find_one({'_id': ObjectId(reservation_id)})
        if reservation:
            reservation['_id'] = str(reservation['_id'])  # Convert ObjectId to string for JSON serialization
            return jsonify(reservation), 200
        else:
            return jsonify({'message': 'Reservation not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reservations/<string:reservation_id>', methods=['DELETE'])
def delete_reservation(reservation_id):
    try:
        result = db.Reservations.delete_one({'_id': ObjectId(reservation_id)})
        if result.deleted_count > 0:
            return jsonify({'message': 'Reservation deleted successfully'}), 200
        else:
            return jsonify({'message': 'Reservation not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/reservations/<string:reservation_id>', methods=['PUT'])
def update_reservation(reservation_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No update data provided'}), 400

        # Find the existing reservation
        reservation = db.Reservations.find_one({'_id': ObjectId(reservation_id)})
        if not reservation:
            return jsonify({'message': 'Reservation not found'}), 404

        # Check if the number of guests is being updated
        new_guests = data.get('guests')
        if new_guests is not None and isinstance(new_guests, int):
            old_guests = reservation.get('guests', 0)

            # If guests count is changing, update currentParticipants in Activities
            if new_guests != old_guests:
                activity_id = reservation['activityId']
                activity = db.Activities.find_one({'_id': ObjectId(activity_id)})

                if not activity:
                    return jsonify({'message': 'Activity not found'}), 404

                # Convert currentParticipants and maxParticipants to integers
                current_participants = int(activity.get('currentParticipants', '0'))
                max_participants = int(activity.get('maxParticipants', '0'))

                # Calculate available slots considering the change in guests
                guest_difference = new_guests - old_guests
                available_slots = max_participants - current_participants

                # If increasing guests, check if there are enough available slots
                if guest_difference > 0 and available_slots < guest_difference:
                    return jsonify({'error': 'Not enough available slots to accommodate the additional guests'}), 400

                # Update the currentParticipants in the activity
                db.Activities.update_one({'_id': ObjectId(activity_id)},
                                         {'$inc': {'currentParticipants': guest_difference}})

        # Perform the reservation update
        result = db.Reservations.update_one({'_id': ObjectId(reservation_id)}, {'$set': data})
        if result.modified_count > 0:
            return jsonify({'message': 'Reservation updated successfully'}), 200
        else:
            return jsonify({'message': 'No changes made to the reservation'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/reservations/user/<string:user_id>', methods=['GET'])
def get_reservations_by_user(user_id):
    try:
        reservations = db.Reservations.find({'userId': user_id})
        results = []
        for reservation in reservations:
            reservation['_id'] = str(reservation['_id'])  # Convert ObjectId to string for JSON serialization
            results.append(reservation)
        if results:
            return jsonify(results), 200
        else:
            return jsonify({'message': 'No reservations found for this user'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
