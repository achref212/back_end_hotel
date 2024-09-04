from bson import ObjectId
from flask import request, jsonify
from flask_restx import Api, Resource, fields
from werkzeug.utils import secure_filename
import os
from werkzeug.datastructures import FileStorage

from app.Controllers.RoomController import RoomController
from app import api, mongo, app
from app.Routes.userRoute import allowed_file

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



@api.route('/rooms')
class RoomsResource(Resource):
    # def get(self):
    #     return room_controller.get_all_rooms()
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
            data['image_path'] = file_path  # Include the image path in the data to be saved
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