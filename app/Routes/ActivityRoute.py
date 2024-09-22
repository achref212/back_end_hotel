import os

import joblib
from bson import ObjectId
from werkzeug.utils import secure_filename
import requests
from app.Controllers.ActivityController import ActivityController
from app import api, mongo, app
from flask_restx import Resource, fields
from datetime import datetime
from flask import request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import numpy as np
from sklearn.linear_model import LinearRegression
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from app.Routes.userRoute import allowed_file
from sklearn.metrics.pairwise import cosine_similarity


scheduler = BackgroundScheduler()
activity_controller = ActivityController(mongo)
db = mongo.db
collection = db['Activities']
# # Weather API setup (use your OpenWeatherMap API key)
# WEATHER_API_KEY = "902d4f6c63d0208b6a5b8721752e817b"
# WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"

activity_model = api.model('Activity', {
    'name': fields.String(required=True, description='Activity Name'),
    'description': fields.String(required=True, description='Activity Description'),
    'startTime': fields.DateTime(required=True, description='Start Time'),
    'endTime': fields.DateTime(required=True, description='End Time'),
    'location': fields.String(required=True, description='Location'),
    'price': fields.Float(required=True, description='Price'),
    'maxParticipants': fields.Integer(required=True, description='Maximum Participants'),
    'currentParticipants': fields.Integer(required=True, description='Current Participants'),
    'images': fields.List(fields.String, description='Image URLs')
})


def vectorize_activity(activity):
    """
    Convert activity details into a vector for similarity comparison.
    Use features like location, price, and maxParticipants.
    """
    location_map = {
        'Tunis': 0,
        'Paris': 1,
        'New York': 2,
        # Add more locations as needed
    }

    location_vector = location_map.get(activity['location'], 0)
    price_vector = float(activity['price'])
    participants_vector = int(activity['maxParticipants'])

    return np.array([location_vector, price_vector, participants_vector])


def recommend_activities(user_id):
    try:
        # Fetch user's past reservations
        reservations = db.Reservations.find({'userId': user_id})
        if db.Reservations.count_documents({'userId': user_id}) == 0:
            return jsonify({'message': 'No reservations found for this user'}), 404

        # Fetch all activities from the database
        all_activities = list(db.Activities.find())

        if len(all_activities) == 0:
            return jsonify({'message': 'No activities available'}), 404

        # Vectorize the user's reserved activities
        user_activity_vectors = []
        for reservation in reservations:
            activity = db.Activities.find_one({'_id': ObjectId(reservation['activityId'])})
            if activity:
                user_activity_vectors.append(vectorize_activity(activity))

        if len(user_activity_vectors) == 0:
            return jsonify({'message': 'No matching activities found for user reservations'}), 404

        user_activity_vectors = np.array(user_activity_vectors)

        # Compute similarity between user activities and all available activities
        all_activity_vectors = np.array([vectorize_activity(act) for act in all_activities])

        # Calculate cosine similarity between user activities and available activities
        similarity_scores = cosine_similarity(user_activity_vectors, all_activity_vectors)

        # Average similarity scores across all user activities
        mean_similarity_scores = np.mean(similarity_scores, axis=0)

        # Get the top recommended activities based on similarity scores
        recommended_indices = mean_similarity_scores.argsort()[::-1][:5]  # Top 5 recommendations

        recommended_activities = [all_activities[i] for i in recommended_indices]

        # Convert ObjectId to string for JSON serialization
        for activity in recommended_activities:
            activity['_id'] = str(activity['_id'])

        return jsonify(recommended_activities), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def train_pricing_model():
    X = np.array([[20, 5, 12], [10, 10, 18], [5, 15, 9]])  # Dummy data (demand, available_slots, time_of_day, temperature)
    y = np.array([100, 80, 60, 120])  # Corresponding prices

    model = LinearRegression()
    model.fit(X, y)

    # Save the model
    joblib.dump(model, 'pricing_model.pkl')

def load_pricing_model():
    if not os.path.exists('pricing_model.pkl'):
        train_pricing_model()
    return joblib.load('pricing_model.pkl')

def predict_price(demand, available_slots, time_of_day):
    model = load_pricing_model()
    features = np.array([[demand, available_slots, time_of_day]])
    predicted_price = model.predict(features)[0]
    return int(round(predicted_price))  # Round and convert to integer

# Task to fetch all activities and update prices dynamically
def dynamic_pricing_task():
    try:
        activities = db.Activities.find()
        current_time = datetime.now().hour  # Get current hour for time_of_day factor

        for activity in activities:
            activity_id = activity['_id']
            location = activity['location']
            # Fetch reservations to calculate demand
            demand = db.Reservations.count_documents({'activityId': str(activity_id)})
            print(demand)
            available_slots = activity['maxParticipants'] - activity['currentParticipants']


            # Predict the new price based on demand, availability, and time of day
            new_price = predict_price(demand, available_slots, current_time)

            # Update the activity price in the database
            db.Activities.update_one({'_id': ObjectId(activity_id)}, {'$set': {'price': new_price}})

            print(f"Updated price for activity {activity['name']} to {new_price}")
    except Exception as e:
        print(f"Error updating activity prices: {str(e)}")

# Schedule the dynamic pricing task to run every 10 minutes
scheduler.add_job(dynamic_pricing_task, 'interval', minutes=40)

scheduler.start()

@api.route('/activities/time')
class ActivitiesByTimeResource(Resource):
    @api.param('start', 'Start time in ISO format', _in='query', required=True)
    @api.param('end', 'End time in ISO format', _in='query', required=True)
    def get(self):
        start_time = request.args.get('start')
        end_time = request.args.get('end')
        if not start_time or not end_time:
            return {"message": "Start and end times are required"}, 400
        try:
            start_time = datetime.fromisoformat(start_time)
            end_time = datetime.fromisoformat(end_time)
        except ValueError:
            return {"message": "Invalid date format. Please use ISO format"}, 400
        return activity_controller.get_activities_by_time(start_time, end_time)


@app.route('/recommendations/activities/<string:user_id>', methods=['GET'])
def get_activity_recommendations(user_id):
    return recommend_activities(user_id)
@app.route('/activities/', methods=['POST'])
def create_activity():
    try:
        # Parse the form data and handle the image upload
        data = request.form.to_dict()
        image_file = request.files.get('image')

        # Basic validation to check if necessary fields are present
        required_fields = ['name', 'description', 'startTime', 'endTime', 'location', 'price', 'maxParticipants']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        if not image_file or not allowed_file(image_file.filename):
            return jsonify({'error': 'Invalid or missing image file'}), 400

        # Securely save the image file
        filename = secure_filename(image_file.filename)
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        file_path = os.path.join(upload_folder, filename)
        image_file.save(file_path)

        # Include the image path in the data to be saved
        standardized_file_path = file_path.replace("\\", "/")
        data['image_path'] = standardized_file_path  # Use the standardized image path
        data['currentParticipants'] = 0

        # Insert the activity data into the database
        activity_id = db.Activities.insert_one(data).inserted_id
        return jsonify({'message': 'Activity created successfully', 'activity_id': str(activity_id)}), 201

    except Exception as e:
        # Catch any other exceptions and return an error response
        return jsonify({'error': str(e)}), 500

@app.route('/activities/', methods=['GET'])
def get_all_activities():
    try:
        activities = db.Activities.find()
        results = []
        for activity in activities:
            activity['_id'] = str(activity['_id'])  # Convert ObjectId to string for JSON serialization
            results.append(activity)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/activities/<string:activity_id>', methods=['GET'])
def get_activity_by_id(activity_id):
    try:
        activity = db.Activities.find_one({'_id': ObjectId(activity_id)})
        if activity:
            activity['_id'] = str(activity['_id'])  # Convert ObjectId to string for JSON serialization
            return jsonify(activity), 200
        else:
            return jsonify({'message': 'Activity not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/activities/<string:activity_id>', methods=['DELETE'])
def delete_activity(activity_id):
    try:
        result = db.Activities.delete_one({'_id': ObjectId(activity_id)})
        if result.deleted_count > 0:
            return jsonify({'message': 'Activity deleted successfully'}), 200
        else:
            return jsonify({'message': 'Activity not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/activities/<string:activity_id>', methods=['PUT'])
def update_activity(activity_id):
    try:
        data = request.form.to_dict()  # Parse the form data
        image_file = request.files.get('image')

        if not data:
            return jsonify({'message': 'No update data provided'}), 400

        # If an image file is provided, process it
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            file_path = os.path.join(upload_folder, filename)
            image_file.save(file_path)
            data['image_path'] = file_path  # Update image path if a new image is provided

        # Perform the update operation
        result = db.Activities.update_one({'_id': ObjectId(activity_id)}, {'$set': data})
        if result.modified_count > 0:
            return jsonify({'message': 'Activity updated successfully'}), 200
        else:
            return jsonify({'message': 'No changes made or activity not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500