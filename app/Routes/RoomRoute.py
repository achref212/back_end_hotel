from bson import ObjectId
from flask import request, jsonify
from flask_restx import Api, Resource, fields
from werkzeug.utils import secure_filename
import os
from werkzeug.datastructures import FileStorage
import numpy as np
from app.Controllers.RoomController import RoomController
from app import api, mongo, app
from app.Routes.userRoute import allowed_file
from sklearn.metrics.pairwise import cosine_similarity
import joblib
from sklearn.linear_model import LinearRegression
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flask import send_from_directory

db = mongo.db
room_controller = RoomController(mongo)

room_model = api.model('Room', {
    'number': fields.String(required=True, description='Room Number'),
    'type': fields.String(required=True, description='Room Type'),
    'description': fields.String(required=True, description='Room Description'),
    'price': fields.Float(required=True, description='Price per Night'),
    'amenities': fields.List(fields.String, description='List of Amenities'),
    'images': fields.List(fields.String, description='Image URLs'),
    'availability': fields.Boolean(required=True, description='Availability Status')
})

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
file_upload = api.parser()
file_upload.add_argument('image', location='files', type=FileStorage, required=True, help='Room image file')


# Train the model to predict room prices
def train_room_pricing_model():
    # Example training data: [room_type, season, demand]
    # Room types: Standard = 0, Superior = 1, Deluxe = 2
    # Seasons: Winter = 0, Spring = 1, Summer = 2, Autumn = 3
    X = np.array([
        [0, 2, 30],  # Standard, Summer, High demand
        [1, 2, 50],  # Superior, Summer, High demand
        [2, 2, 70],  # Deluxe, Summer, Very high demand
        [0, 0, 10],  # Standard, Winter, Low demand
        [1, 0, 20],  # Superior, Winter, Low demand
        [2, 0, 30],  # Deluxe, Winter, Medium demand
        [0, 1, 15],  # Standard, Spring, Low demand
        [1, 3, 25],  # Superior, Autumn, Medium demand
        [2, 3, 35],  # Deluxe, Autumn, High demand
        # Add more data points as needed
    ])

    y = np.array([400, 450, 700, 400, 450, 600, 420, 470, 650])  # Prices corresponding to the data points

    # Train the model
    model = LinearRegression()
    model.fit(X, y)

    # Save the model to a file for later use
    model_filename = 'room_pricing_model.pkl'
    joblib.dump(model, model_filename)


# Load the trained pricing model
def load_room_pricing_model():
    model_filename = 'room_pricing_model.pkl'
    if not os.path.exists(model_filename):
        train_room_pricing_model()  # Train and save model if it doesn't exist
    return joblib.load(model_filename)


# Predict room price based on room type, season, and demand
def predict_room_price(room_type, season, demand):
    model = load_room_pricing_model()

    # Prepare the input data for prediction (room_type, season, demand)
    features = np.array([[room_type, season, demand]])

    # Predict the price
    predicted_price = model.predict(features)[0]

    # Ensure the price stays within the range of 400 to 700
    predicted_price = max(400, min(700, predicted_price))

    return round(predicted_price, 2)


# Dynamic pricing task for rooms
def dynamic_room_pricing_task():
    try:
        rooms = db.Rooms.find()
        current_month = datetime.now().month

        # Determine the current season based on the month
        if current_month in [12, 1, 2]:
            season = 0  # Winter
        elif current_month in [3, 4, 5]:
            season = 1  # Spring
        elif current_month in [6, 7, 8]:
            season = 2  # Summer
        else:
            season = 3  # Autumn

        for room in rooms:
            room_id = room['_id']
            room_type = room.get('type', 'Standard')  # Default to 'Standard'

            # Map room type to an integer
            room_type_map = {
                'Standard': 0,
                'Superior': 1,
                'Deluxe': 2
            }
            room_type_val = room_type_map.get(room_type, 0)  # Default to Standard if not found

            # Fetch the demand (number of bookings for this room)
            demand = db.Bookings.count_documents({'roomId': str(room_id)})

            # Predict the new price based on room type, season, and demand
            new_price = predict_room_price(room_type_val, season, demand)

            # Update the room price in the database
            db.Rooms.update_one({'_id': ObjectId(room_id)}, {'$set': {'price': new_price}})

            print(f"Updated price for room {room['number']} to {new_price}, based on demand and season")

    except Exception as e:
        print(f"Error updating room prices: {str(e)}")


# Schedule the dynamic pricing task
scheduler = BackgroundScheduler()
scheduler.add_job(dynamic_room_pricing_task, 'interval', minutes=40)  # Runs every hour
scheduler.start()

# Vectorize room data
def vectorize_room(room):
    """
    Convert room details into a vector for similarity comparison.
    We use features like type, price, and availability.
    """
    room_type_map = {
        'Standard': 0,
        'Superior': 1,
        'Deluxe': 2,
        # Add other room types as needed
    }

    type_vector = room_type_map.get(room['type'], 0)  # Default to 0 if type not found
    price_vector = float(room['price'])
    availability_vector = 1 if room['availability'] else 0

    return np.array([type_vector, price_vector, availability_vector])
def recommend_rooms(user_id):
    try:
        # Fetch user's past bookings
        bookings = db.Bookings.find({'userId': user_id})

        if db.Bookings.count_documents({'userId': str(user_id)}) == 0:
            return jsonify({'message': 'No bookings found for this user'}), 404

        # Fetch all rooms from the database
        all_rooms = list(db.Rooms.find())

        if len(all_rooms) == 0:
            return jsonify({'message': 'No rooms available'}), 404

        # Vectorize user's booked rooms
        user_room_vectors = []
        for booking in bookings:
            room = db.Rooms.find_one({'_id': ObjectId(booking['roomId'])})
            if room:
                user_room_vectors.append(vectorize_room(room))

        if len(user_room_vectors) == 0:
            return jsonify({'message': 'No matching rooms found for user bookings'}), 404

        user_room_vectors = np.array(user_room_vectors)

        # Compute similarity between user rooms and all available rooms
        all_room_vectors = np.array([vectorize_room(room) for room in all_rooms])

        # Calculate cosine similarity
        similarity_scores = cosine_similarity(user_room_vectors, all_room_vectors)

        # Average similarity scores across all user bookings
        mean_similarity_scores = np.mean(similarity_scores, axis=0)

        # Get top recommended rooms based on similarity scores
        recommended_indices = mean_similarity_scores.argsort()[::-1][:5]  # Top 5 recommendations

        recommended_rooms = [all_rooms[i] for i in recommended_indices]

        # Convert ObjectId to string for JSON serialization
        for room in recommended_rooms:
            room['_id'] = str(room['_id'])

        return jsonify(recommended_rooms), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    upload_folder = 'D:\\project\\esprit project\\Back_End\\Uploads'
    try:
        return send_from_directory(upload_folder, filename, as_attachment=False, mimetype='image/png')
    except FileNotFoundError:
        os.abort(404)

@api.route('/rooms')
class RoomsResource(Resource):
    @api.expect(file_upload)
    def post(self):
        data = request.form.to_dict()
        image_file = request.files.get('image')
        if not data or not image_file:
            return {'message': 'Missing data or image'}, 400

        if 'number' not in data or 'type' not in data:
            return {'message': 'Missing required room details'}, 400

        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            file_path = os.path.join(upload_folder, filename)
            image_file.save(file_path)

            # Standardize the file path to use forward slashes
            standardized_file_path = file_path.replace("\\", "/")
            data['image_path'] = standardized_file_path  # Use the standardized image path

        else:
            return {'message': 'Invalid image format'}, 400

        # Insert the data into MongoDB
        try:
            room_id = db['Rooms'].insert_one(data).inserted_id
            return {'message': 'Room created successfully', 'room_id': str(room_id)}, 201
        except Exception as e:
            app.logger.error(f"Error inserting room data into MongoDB: {str(e)}")
            return {'message': 'Failed to create room'}, 500



@api.route('/rooms/<string:room_id>')
class RoomResource(Resource):
    def get(self, room_id):
        return room_controller.get_room_by_id(room_id)

    # @api.expect(room_model)
    # def put(self, room_id):
    #     return room_controller.update_room(room_id)

    def delete(self, room_id):
        return room_controller.delete_room(room_id)

@api.route('/rooms/availability/<string:availability>')
class RoomsByAvailabilityResource(Resource):
    def get(self, availability):
        return room_controller.get_rooms_by_availability(availability)


@app.route('/rooms/', methods=['GET'])
def get_all_rooms():
    try:
        rooms = db.Rooms.find()
        results = []
        for room in rooms:
            room['_id'] = str(room['_id'])  # Convert ObjectId to string
            # Assuming you might want to add more details like room status or any linked data
            # For simplicity, let's assume all data needed is already included in the room document
            results.append(room)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/rooms/<string:room_id>', methods=['PUT'])
def update_room(room_id):
    try:
        # Initialize update_data with non-file form fields, expecting them to contain JSON-like keys and values
        update_data = request.form.to_dict()

        # Handling file uploads
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                update_data['file_path'] = file_path
            else:
                return jsonify({'message': 'Invalid file format'}), 400

        # Perform the MongoDB update operation
        if update_data:
            result = db.Rooms.update_one({'_id': ObjectId(room_id)}, {'$set': update_data})
            if result.modified_count:
                return jsonify({'message': 'Room updated successfully'}), 200
            else:
                return jsonify({'message': 'No changes made or room not found'}), 404
        else:
            return jsonify({'message': 'No data provided'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recommendations/rooms/<string:user_id>', methods=['GET'])
def get_room_recommendations(user_id):
    return recommend_rooms(user_id)