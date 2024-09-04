import os

from bson import ObjectId
from werkzeug.utils import secure_filename

from app.Controllers.ActivityController import ActivityController
from app import api, mongo, app
from flask_restx import Resource, fields
from datetime import datetime
from flask import request, jsonify

from app.Routes.userRoute import allowed_file

activity_controller = ActivityController(mongo)
db = mongo.db
collection = db['Activities']

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

# @api.route('/activities/<string:activity_id>')
# class ActivityResource(Resource):
#     def get(self, activity_id):
#         return activity_controller.get_activity_by_id(activity_id)
#
#     @api.expect(activity_model)
#     def put(self, activity_id):
#         return activity_controller.update_activity(activity_id)
#
#     def delete(self, activity_id):
#         return activity_controller.delete_activity(activity_id)
#

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
        data['image_path'] = file_path

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