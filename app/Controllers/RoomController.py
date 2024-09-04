
import os
from bson import ObjectId
from flask import request
from app import app
from app.Models.RoomModel import RoomModel
from werkzeug.utils import secure_filename

class RoomController:
    def __init__(self, db):
        self.model = RoomModel(db)

    def get_all_rooms(self):
        try:
            print("Attempting to retrieve all rooms...")
            rooms = self.model.get_all_rooms()
            print(f"Rooms retrieved: {rooms}")
            return [{'_id': str(room['_id']), **room} for room in rooms], 200
        except Exception as e:
            app.logger.error(f"Error in get_all_rooms: {str(e)}")
            return {'message': f'Failed to retrieve rooms: {str(e)}'}, 500

    def get_room_by_id(self, room_id):
        try:
            print(f"Attempting to retrieve room by ID: {room_id}")
            room = self.model.get_room_by_id(ObjectId(room_id))
            if room:
                print(f"Room found: {room}")
                room['_id'] = str(room['_id'])
                return room, 200
            return {'message': 'Room not found'}, 404
        except Exception as e:
            app.logger.error(f"Error in get_room_by_id: {str(e)}")
            return {'message': 'Failed to retrieve room'}, 500

    def delete_room(self, room_id):
        try:
            result = self.model.delete_room(ObjectId(room_id))
            if result.deleted_count:
                return {'message': 'Room deleted successfully'}, 200
            return {'message': 'No room was deleted'}, 404
        except Exception as e:
            app.logger.error(f"Error deleting room {room_id}: {str(e)}")
            return {'message': 'Failed to delete room'}, 500

    def update_room(self, room_id):
        try:
            data = request.get_json()
            if not data:
                return {'message': 'No data provided'}, 400
            result = self.model.update_room(ObjectId(room_id), data)
            if result.modified_count:
                return {'message': 'Room updated successfully'}, 200
            return {'message': 'No room was updated'}, 404
        except Exception as e:
            app.logger.error(f"Error updating room {room_id}: {str(e)}")
            return {'message': 'Failed to update room'}, 500
